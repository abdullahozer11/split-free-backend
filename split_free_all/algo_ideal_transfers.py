from copy import deepcopy

from split_free_all.models import Balance, Debt


def get_group_with_sum(target_sum, group_length, debts):
    # This the case where we try to get all elements of debts to sum up to 0
    if group_length == len(debts) and target_sum == 0:
        return debts
    # For a group of 1 element, let's return the first element that is equal to
    # the target sum
    if group_length == 1:
        for debt in debts:
            if debt.amount == target_sum:
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
            sum_debts = debts[low_index].amount + debts[high_index].amount
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
    # to target the sum (target_sum - debts[first_index].balance) with
    # group_length in the array starting from after this first_index
    for first_index in range(len(debts) - (group_length - 1)):
        potential_matching_group = get_group_with_sum(
            target_sum=target_sum - debts[first_index].amount,
            debts=debts[first_index + 1 :],
            group_length=group_length - 1,
        )
        if potential_matching_group:
            return [debts[first_index]] + potential_matching_group

    # If no matching group is found return an empty list
    return []


def remove_group_from_debts(debts, selection):
    selection_debt_ids = set(person.id for person in selection)
    new_debts = []
    for debt in debts:
        if debt.id not in selection_debt_ids:
            new_debts.append(debt)
    return new_debts


def get_ideal_transfers_from(selection):
    if len(selection) < 2:
        return []
    # As the debts in the selection are sorted according to their balance, let's
    # Consider the first and the last one, one will be positive and the other
    # one negative. Let's make them match into a transaction so that the one
    # the smallest absolute value is removed and the one with the greatest
    # absolute value is kept with what's left. In case they cancel out, they
    # both disappear
    transfers = []
    while selection:
        debt = Debt(
            group=selection[0].group,
            borrower=selection[-1].user,
            lender=selection[0].user,
        )
        # The first element is negative and the last positive, we sum them to
        # "get the difference" and judge which one has more weight
        difference = selection[0].amount + selection[-1].amount
        if difference < 0:
            # Example 0 -> -100 and 1 -> +10
            debt.amount = selection[-1].amount
            selection[0].amount = difference
            selection.pop()
        elif difference > 0:
            # Example 0 -> -10 and 1 -> +100
            debt.amount = -selection[0].amount
            selection[-1].amount = difference
            selection.pop(0)
        else:
            # Example 0 -> -100 and 1 -> +100
            debt.amount = selection[-1].amount
            selection.pop(0)
            selection.pop()
        transfers.append(debt)
    return transfers


def calculate_new_ideal_transfers_data(group):
    user_group_debts = Balance.objects.filter(group=group)
    # Let's sort the user_event debts according to their balance
    debts = deepcopy(
        sorted(user_group_debts, key=lambda user_group_debt: user_group_debt.amount)
    )  # debt is a simpler name for after

    # This is where the ideal transfers are stored
    ideal_transfers = []
    # Let's select debts of 1, 2, ... len(debts)//2 debts
    # This variable is called selection_length
    selection_length = 1
    while debts:
        # If no groups of null sum could be found with less than 'len(debts) // 2'
        # There won't be group of more than that
        if selection_length > len(debts) // 2:
            selection_length = len(debts)
        # Try to find a group of length: group_length
        selection = get_group_with_sum(
            target_sum=0.00, group_length=selection_length, debts=debts
        )
        # If none is found, let's increment the counter of group_length
        # If one is found, next iteration, we'll try to extract another group of
        # length group_length
        if not selection:
            selection_length += 1
        else:
            # Remove the debts of the found group from the debts, so that we
            # need to deal with only the leftover debts
            debts = remove_group_from_debts(debts=debts, selection=selection)
            # Extract the ideal transfers from this group. As non of its
            # subgroups can sum to 0, we get (group-length - 1)transfers
            # out of this group
            transfers = get_ideal_transfers_from(selection=selection)
            ideal_transfers.extend(transfers)

    # Save the ideal_transfers in database
    for ideal_transfer in ideal_transfers:
        ideal_transfer.save()
