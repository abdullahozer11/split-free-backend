# Copyright (c) 2023 SplitFree Org.

from decimal import Decimal

from django.db.models.signals import Signal
from django.dispatch import receiver
from django.forms.models import model_to_dict

from split_free_all.algo_debts import calculate_new_debts
from split_free_all.models import Balance, Expense

################################################################################
# Group

group_created = Signal()


@receiver(group_created)
def handle_group_created(sender, instance, **kwargs):
    # Create a MemberGroupDebt with a value of 0 for each member
    for member in instance.members.all():
        Balance.objects.create(owner=member, group=instance, amount=0.00)


group_updated = Signal()


@receiver(group_updated)
def handle_group_updated(sender, instance, old_group_info, new_group_info, **kwargs):
    # Handle the case: members are added to the group
    added_members = set(new_group_info["members"]) - set(old_group_info["members"])
    if added_members:
        # Create a balance with an amount of 0 for each new added member
        for member in added_members:
            Balance.objects.create(owner=member, group=instance, amount=0.00)

    # Handle the case: members are removed from the group
    removed_members = set(old_group_info["members"]) - set(new_group_info["members"])
    if removed_members:
        # Update impacted expenses of the group
        expenses_to_update = Expense.objects.filter(
            group=instance, participants__in=removed_members
        ).distinct()
        for expense_to_update in expenses_to_update:
            old_expense_info = model_to_dict(expense_to_update)
            # If the payer is withing the removed members, it means he withdrew
            # Therefore, the other expense participants won't have to pay him
            # back. We set the expense payer to None, and this logic will be
            # handled in apply_impact_expense
            if expense_to_update.payer in removed_members:
                expense_to_update.payer = None
            expense_to_update.participants.remove(
                *(set(expense_to_update.participants.all()) & removed_members)
            )
            new_expense_info = model_to_dict(expense_to_update)
            undo_impact_expense(expense_info=old_expense_info)
            apply_impact_expense(expense_info=new_expense_info)

        # Remove the balances of the removed members
        Balance.objects.filter(owner__in=removed_members).delete()

        calculate_new_debts(group=instance)


################################################################################
# Expense


def apply_impact_expense(expense_info):
    # In case the payer paid and left, it's free for the other members of the
    # expense
    if not expense_info["payer"]:
        return

    payer_balance = Balance.objects.get(
        group=expense_info["group"], owner=expense_info["payer"]
    )
    payer_balance.amount -= expense_info["amount"]
    payer_balance.save()

    # This is the amount that each participant needs to pay for the expense
    split_amount = Decimal(
        float(expense_info["amount"]) / len(expense_info["participants"])
    )

    for member in expense_info["participants"]:
        member_balance = Balance.objects.get(group=expense_info["group"], owner=member)
        member_balance.amount += split_amount
        member_balance.save()


def undo_impact_expense(expense_info):
    payer_balance = Balance.objects.get(
        group=expense_info["group"], owner=expense_info["payer"]
    )
    payer_balance.amount += expense_info["amount"]
    payer_balance.save()

    # This is the amount that each participant paid for the expense
    split_amount = Decimal(
        float(expense_info["amount"]) / len(expense_info["participants"])
    )

    for member in expense_info["participants"]:
        member_balance = Balance.objects.get(group=expense_info["group"], owner=member)
        member_balance.amount -= split_amount
        member_balance.save()


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
