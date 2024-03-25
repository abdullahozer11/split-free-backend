# Copyright (c) 2023 SplitFree Org.

from decimal import Decimal

from django.db.models.signals import Signal
from django.dispatch import receiver
from django.forms.models import model_to_dict

from split_free_backend.core.algo_debts import calculate_new_debts
from split_free_backend.core.models import Balance, Debt, Expense, Member

################################################################################
# Group

group_created = Signal()


@receiver(group_created)
def handle_group_created(sender, instance, member_names, **kwargs):
    # Create members from the member_names passed in the request
    members = []
    if member_names:
        for member_name in member_names:
            members.append(Member.objects.create(name=member_name, group=instance))
        instance.members.set(members)
    # Otherwise, use the members are already created objects
    else:
        members = instance.members.all()

    # Create a MemberGroupDebt with a value of 0 for each member
    for member in members:
        Balance.objects.create(owner=member, group=instance, amount=0.00)


group_updated = Signal()


@receiver(group_updated)
def handle_group_updated(sender, instance, old_member_names, new_member_names, **kwargs):
    # Handle the case: members are added to the group
    added_member_names = set(new_member_names) - set(old_member_names)
    if added_member_names:
        # Create these new members and associate them a balance of 0
        for member_name in added_member_names:
            member = Member.objects.create(name=member_name, group=instance)
            Balance.objects.create(owner=member, group=instance, amount=0.00)

    # Handle the case: members are removed from the group
    removed_member_names = set(old_member_names) - set(new_member_names)
    if removed_member_names:
        removed_members = Member.objects.filter(name__in=removed_member_names, group=instance)
        # Update impacted expenses of the group
        expenses_to_update = Expense.objects.filter(group=instance, participants__in=removed_members).distinct()
        for expense_to_update in expenses_to_update:
            old_expense_info = model_to_dict(expense_to_update)
            # If the payer is withing the removed members, it means he withdrew
            # Therefore, the other expense participants won't have to pay him
            # back. We set the expense payer to None, and this logic will be
            # handled in apply_impact_expense
            if expense_to_update.payer in removed_members:
                expense_to_update.payer = None
            # Remove the removed members from the expense participants
            for removed_member in removed_members:
                if removed_member in expense_to_update.participants.all():
                    expense_to_update.participants.remove(removed_member)
            new_expense_info = model_to_dict(expense_to_update)
            undo_impact_expense(expense_info=old_expense_info)
            apply_impact_expense(expense_info=new_expense_info)
        # Remove the members, the balances will be removed by the on_delete
        removed_members.delete()

        calculate_new_debts(group=instance)


################################################################################
# Expense


def apply_impact_expense(expense_info):
    # In case the payer paid and left, it's free for the other members of the
    # expense
    if not expense_info["payer"]:
        return

    payer_balance = Balance.objects.get(group=expense_info["group"], owner=expense_info["payer"])
    payer_balance.amount -= expense_info["amount"]
    payer_balance.save()

    # This is the amount that each participant needs to pay for the expense
    split_amount = Decimal(float(expense_info["amount"]) / len(expense_info["participants"]))

    for member in expense_info["participants"]:
        member_balance = Balance.objects.get(group=expense_info["group"], owner=member)
        member_balance.amount += split_amount
        member_balance.save()


def undo_impact_expense(expense_info):
    if expense_info["payer"] and expense_info["participants"]:
        payer_balance = Balance.objects.get(group=expense_info["group"], owner=expense_info["payer"])
        payer_balance.amount += expense_info["amount"]
        payer_balance.save()

        # This is the amount that each participant paid for the expense
        split_amount = Decimal(float(expense_info["amount"]) / len(expense_info["participants"]))

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
def renew_debts_and_transfers(sender, instance, old_expense_info, new_expense_info, **kwargs):
    undo_impact_expense(expense_info=old_expense_info)
    apply_impact_expense(expense_info=new_expense_info)
    calculate_new_debts(group=instance.group)


################################################################################
# Member


def undo_impact_member(member):
    Balance.objects.get(owner=member).delete()

    for debt in Debt.objects.filter(borrower=member):
        debt.lender.balance.amount += debt.amount
        debt.lender.balance.save()

    for debt in Debt.objects.filter(lender=member):
        debt.borrower.balance.amount -= debt.amount
        debt.borrower.balance.save()


expense_destroyed = Signal()
member_deleted = Signal()


def remove_debts_and_transfers(sender, instance, **kwargs):
    if isinstance(instance, Expense):
        undo_impact_expense(expense_info=model_to_dict(instance))
    elif isinstance(instance, Member):
        undo_impact_member(member=instance)
    calculate_new_debts(group=instance.group)


expense_destroyed.connect(remove_debts_and_transfers)
member_deleted.connect(remove_debts_and_transfers)
