# Copyright (c) 2023 SplitFree Org.

from decimal import Decimal

from django.db.models.signals import Signal
from django.dispatch import receiver
from django.forms.models import model_to_dict

from split_free_all.algo_ideal_transfers import calculate_new_ideal_transfers_data
from split_free_all.models import UserEventDebt


def apply_impact_expense(expense_info):
    # In case the payer paid and left, it's free for the other users of the
    if not expense_info["payer"]:
        return

    number_users_in_expense = len(expense_info["users"])
    # Update the debt balance of each user for this event
    for user in expense_info["users"]:
        user_event_debt = UserEventDebt.objects.get(
            event=expense_info["event"], user=user
        )
        if user.id == expense_info["payer"]:
            user_event_debt.debt_balance -= Decimal(
                float(expense_info["amount"]) * (1 - 1 / number_users_in_expense)
            )
        else:
            user_event_debt.debt_balance += Decimal(
                float(expense_info["amount"]) / number_users_in_expense
            )
        user_event_debt.save()


def undo_impact_expense(expense_info):
    number_users_in_expense = len(expense_info["users"])

    # Update the debt balance of each user for this event
    for user in expense_info["users"]:
        user_event_debt = UserEventDebt.objects.get(
            event=expense_info["event"], user=user
        )
        if user.id == expense_info["payer"]:
            user_event_debt.debt_balance += Decimal(
                float(expense_info["amount"]) * (1 - 1 / number_users_in_expense)
            )
        else:
            user_event_debt.debt_balance -= Decimal(
                float(expense_info["amount"]) / number_users_in_expense
            )
        user_event_debt.save()


event_created = Signal()


@receiver(event_created)
def handle_event_created(sender, instance, **kwargs):
    # Create a UserEventDebt with a value of 0 for each user
    for user in instance.users.all():
        UserEventDebt.objects.create(user=user, event=instance, debt_balance=0.0)


expense_created = Signal()


@receiver(expense_created)
def handle_expense_created(sender, instance, **kwargs):
    apply_impact_expense(expense_info=model_to_dict(instance))
    # Generate the ideal transfers
    calculate_new_ideal_transfers_data(event=instance.event)


expense_updated = Signal()


@receiver(expense_updated)
def renew_debts_and_transfers(
    sender, instance, old_expense_info, new_expense_info, **kwargs
):
    undo_impact_expense(expense_info=old_expense_info)
    apply_impact_expense(expense_info=new_expense_info)
    # Generate the ideal transfers
    calculate_new_ideal_transfers_data(event=instance.event)
