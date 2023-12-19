from copy import deepcopy
from decimal import Decimal

from split_free_all.models import IdealTransfer, UserEventDebt


def get_group_with_sum(target_sum, group_length, debts):
    # This the case where we try to get all elements of debts to sum up to 0
    if group_length == len(debts) and target_sum == 0:
        return debts
    # For a group of 1 element, let's return the first element that is equal to
    # the target sum
    if group_length == 1:
        for debt in debts:
            if debt.debt_balance == target_sum:
                return [debt]
        # If 1-debt group is found return an empty list
        return []

    # For a group of 2 elements, let's have two indices one at the beginning and
    # one at the end and move them until they sum up to the target or overlap.
    # Remember that this is possible because the debts list is sorted at any
    # point of the algorithm
    if group_length == 2:
        low_index = 0
        high_index = len(debts) - 1
        while low_index < high_index:
            sum_debts = debts[low_index].debt_balance + debts[high_index].debt_balance
            if sum_debts < 0:
                low_index += 1
            elif sum_debts > 0:
                high_index -= 1
            else:
                return [debts[low_index], debts[high_index]]
        # If no group of 2 elements is found return an empty list
        return []

    # In the case of group_length > 2, let's operate recursively to lower values
    # of group_length: loop through the array this an index first_index, and try
    # to target the sum (target_sum - debts[first_index].debt_balance) with
    # group_length in the array starting from after this first_index
    for first_index in range(len(debts) - (group_length - 1)):
        potential_matching_group = get_group_with_sum(
            target_sum=target_sum - debts[first_index].debt_balance,
            debts=debts[first_index + 1 :],
            group_length=group_length - 1,
        )
        if potential_matching_group:
            return [debts[first_index]] + potential_matching_group

    # If no matching group is found return an empty list
    return []


def remove_group_from_debts(debts, group):
    group_debt_ids = set(debt.id for debt in group)
    new_debts = []
    for debt in debts:
        if debt.id not in group_debt_ids:
            new_debts.append(debt)
    return new_debts


def get_ideal_transfers_from(group):
    # As the debts in the group are sorted according to their balance, let's
    # Consider the first and the last one, one will be positive and the other
    # one negative. Let's make them match into a transaction so that the one
    # the smallest absolute value is removed and the one with the greatest
    # absolute value is kept with what's left. In case they cancel out, they
    # both disappear
    transfers = []
    while group:
        transfer = IdealTransfer(
            event=group[0].event, sender=group[-1].user, receiver=group[0].user
        )
        # The first element is negative and the last positive, we sum them to
        # "get the difference" and judge which one has more weight
        difference = group[0].debt_balance + group[-1].debt_balance
        if difference < 0:
            # Example 0 -> -100 and 1 -> +10
            transfer.amount = group[-1].debt_balance
            group[0].debt_balance = difference
            group.pop()
        elif difference > 0:
            # Example 0 -> -10 and 1 -> +100
            transfer.amount = -group[0].debt_balance
            group[-1].debt_balance = difference
            group.pop(0)
        else:
            # Example 0 -> -100 and 1 -> +100
            transfer.amount = group[-1].debt_balance
            group.pop(0)
            group.pop()
        transfers.append(transfer)
    return transfers


def calculate_new_ideal_transfers_data(event):
    user_event_debts = UserEventDebt.objects.filter(event=event)
    # Let's sort the user_event debts according to their balance
    debts = deepcopy(
        sorted(
            user_event_debts, key=lambda user_event_debt: user_event_debt.debt_balance
        )
    )  # debt is a simpler name for after

    number_debts = len(debts)

    # This is where the ideal transfers are stored
    ideal_transfers = []
    # Let's group debts of 1, 2, ... number_debts//2 debts
    # This variable is called group_length
    group_length = 1
    while debts:
        # If no groups of null sum could be found with less than 'number_debts // 2'
        # There won't be group of more than that
        if group_length > number_debts // 2:
            group_length = number_debts
        # Try to find a group of length: group_length
        group = get_group_with_sum(
            target_sum=0.00, group_length=group_length, debts=debts
        )
        # If none is found, let's increment the counter of group_length
        # If one is found, next iteration, we'll try to extract another group of
        # length group_length
        if not group:
            group_length += 1
        else:
            # Remove the debts of the found group from the debts, so that we
            # need to deal with only the leftover debts
            debts = remove_group_from_debts(debts=debts, group=group)
            # Extract the ideal transfers from this group. As non of its
            # sub-groups can sum to 0, we get (group-length - 1)transfers
            # out of this group
            transfers = get_ideal_transfers_from(group)
            ideal_transfers.extend(transfers)

    # Save the ideal_transfers in database
    for ideal_transfer in ideal_transfers:
        ideal_transfer.save()
