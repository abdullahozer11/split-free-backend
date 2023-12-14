from decimal import Decimal

from django.db.models.signals import Signal
from django.dispatch import receiver

from .models import UserEventDebt

event_created = Signal()


@receiver(event_created)
def handle_event_created(sender, instance, **kwargs):
    # Create a UserEventDebt with a value of 0 for each user
    for user in instance.users.all():
        UserEventDebt.objects.create(user=user, event=instance, debt_balance=0.0)


expense_created = Signal()


@receiver(expense_created)
def handle_expense_created(sender, instance, **kwargs):
    nb_users_in_expense = instance.users.count()

    # Update the debt balance of each user for this event
    for user in instance.users.all():
        user_event_debt = UserEventDebt.objects.get(event=instance.event, user=user)
        if user.id == instance.payer.id:
            user_event_debt.debt_balance -= Decimal(
                float(instance.amount) * (1 - 1 / nb_users_in_expense)
            )
        else:
            user_event_debt.debt_balance += Decimal(
                float(instance.amount) / nb_users_in_expense
            )
        user_event_debt.save()
