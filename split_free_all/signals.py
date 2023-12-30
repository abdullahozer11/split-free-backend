# Copyright (c) 2023 SplitFree Org.

from decimal import Decimal

from django.db.models.signals import Signal
from django.dispatch import receiver
from django.forms.models import model_to_dict

from split_free_all.algo_debts import calculate_new_debts
from split_free_all.models import Balance

################################################################################
# Group

group_created = Signal()


@receiver(group_created)
def handle_group_created(sender, instance, **kwargs):
    # Create a UserGroupDebt with a value of 0 for each user
    for user in instance.members.all():
        Balance.objects.create(user=user, group=instance, amount=0.00)


################################################################################
# Expense


def apply_impact_expense(expense_info):
    # In case the payer paid and left, it's free for the other users of the
    # expense
    if not expense_info["payer"]:
        return

    number_users_in_expense = len(expense_info["participants"])
    # Update the balance of each user for this group
    for user in expense_info["participants"]:
        user_balance = Balance.objects.get(group=expense_info["group"], user=user)
        if user.id == expense_info["payer"]:
            user_balance.amount -= Decimal(
                float(expense_info["amount"]) * (1 - 1 / number_users_in_expense)
            )
        else:
            user_balance.amount += Decimal(
                float(expense_info["amount"]) / number_users_in_expense
            )
        user_balance.save()


def undo_impact_expense(expense_info):
    number_users_in_expense = len(expense_info["participants"])
    # Update the balance of each user for this group
    for user in expense_info["participants"]:
        user_balance = Balance.objects.get(group=expense_info["group"], user=user)
        if user.id == expense_info["payer"]:
            user_balance.amount += Decimal(
                float(expense_info["amount"]) * (1 - 1 / number_users_in_expense)
            )
        else:
            user_balance.amount -= Decimal(
                float(expense_info["amount"]) / number_users_in_expense
            )
        user_balance.save()


expense_created = Signal()


@receiver(expense_created)
def handle_expense_created(sender, instance, **kwargs):
    apply_impact_expense(expense_info=model_to_dict(instance))
    calculate_new_debts(group=instance.group)


expense_updated = Signal()


@receiver(expense_updated)
def renew_debts_and_transfers(
    sender, instance, old_expense_info, new_expense_info, **kwargs
):
    undo_impact_expense(expense_info=old_expense_info)
    apply_impact_expense(expense_info=new_expense_info)
    calculate_new_debts(group=instance.group)


expense_destroyed = Signal()


@receiver(expense_destroyed)
def remove_debts_and_transfers(sender, instance, **kwargs):
    undo_impact_expense(expense_info=model_to_dict(instance))
    calculate_new_debts(group=instance.group)
