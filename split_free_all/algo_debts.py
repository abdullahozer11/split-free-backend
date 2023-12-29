from copy import deepcopy

from split_free_all.models import Balance, Debt


def get_selection_with_sum(target_sum, selection_length, balances):
    # This is the case where we try to get all balance of balances to sum up to 0
    if selection_length == len(balances) and target_sum == 0:
        return balances
    # For a selection of 1 balance, let's return the first balance that is equal
    # to the target sum
    if selection_length == 1:
        for balance in balances:
            if balance.amount == target_sum:
                return [balance]
        # If no selection of one balance is found return an empty list
        return []

    # For a selection of 2 balances, let's have two indices one at the beginning
    # and one at the end of balances and move them until they sum up to the
    # target or overlap.
    # Remember that this is possible because the balances list is sorted at any
    # point of the algorithm.
    if selection_length == 2:
        low_index = 0
        high_index = len(balances) - 1
        while low_index < high_index:
            sum_balances = balances[low_index].amount + balances[high_index].amount
            if sum_balances < 0:
                low_index += 1
            elif sum_balances > 0:
                high_index -= 1
            else:
                return [balances[low_index], balances[high_index]]
        # If no selection of 2 balances is found return an empty list
        return []

    # For a selection of more than 2 balances, let's operate recursively to
    # lower values of selection_length: loop through the array this an index
    # first_index, and try to target the sum
    # (target_sum - balances[first_index].balance) with
    # selection_length-1 balances in the array starting from after this
    # first_index
    for first_index in range(len(balances) - (selection_length - 1)):
        potential_matching_selection = get_selection_with_sum(
            target_sum=target_sum - balances[first_index].amount,
            balances=balances[first_index + 1 :],
            selection_length=selection_length - 1,
        )
        if potential_matching_selection:
            return [balances[first_index]] + potential_matching_selection

    # If no matching selection is found return an empty list
    return []


def remove_selection_from_balances(balances, selection):
    selected_balance_ids = set(balance.id for balance in selection)
    new_balances = []
    for balance in balances:
        if balance.id not in selected_balance_ids:
            new_balances.append(balance)
    return new_balances


def get_debts_from(selection):
    if len(selection) < 2:
        return []
    # As the balances in the selection are sorted according to their amount,
    # let's consider the first and the last one, one will be positive and the
    # other one negative. Let's make them match into a debt so that the one with
    # the smallest absolute value is removed and the one with the greatest
    # absolute value is kept with what's left. In case they cancel out, they
    # both disappear
    debts = []
    while selection:
        debt = Debt(
            group=selection[0].group,
            borrower=selection[-1].user,
            lender=selection[0].user,
        )
        # The first element is negative and the last positive, we sum them to
        # "get the difference" and judge which one has more "weight"
        difference = selection[0].amount + selection[-1].amount
        if difference < 0:
            # Example selection[0] -> -100 and selection[-1] -> +10
            debt.amount = selection[-1].amount
            selection[0].amount = difference
            selection.pop()
        elif difference > 0:
            # Example selection[0] -> -10 and selection[-1] -> +100
            debt.amount = -selection[0].amount
            selection[-1].amount = difference
            selection.pop(0)
        else:
            # Example selection[0] -> -100 and selection[-1] -> +100
            debt.amount = selection[-1].amount
            selection.pop(0)
            selection.pop()
        debts.append(debt)
    return debts


def calculate_new_debts(group):
    unsorted_balances = Balance.objects.filter(group=group)
    # Let's sort the balances according to their amount
    balances = deepcopy(sorted(unsorted_balances, key=lambda balance: balance.amount))

    # This is where the debts are stored
    debts = []
    # Let's select balances of 1, 2, ... len(balances)//2 balances into a
    # `selection`. The length of a selection is called selection_length
    selection_length = 1
    while balances:
        # If no selections of null sum could be found with less than
        # 'len(balances) // 2' , there won't be selections of more than that
        if selection_length > len(balances) // 2:
            selection_length = len(balances)
        # Try to find a selection of length: selection_length
        selection = get_selection_with_sum(
            target_sum=0.00,
            selection_length=selection_length,
            balances=balances,
        )
        # If none is found, let's increment the counter of selection_length
        if not selection:
            selection_length += 1
        # If one is found, next iteration, we'll try to extract another
        # selection of length: selection_length
        else:
            # Remove the balances of the found selection from the balances, so
            # that we need to deal with only the leftover balances
            balances = remove_selection_from_balances(
                balances=balances, selection=selection
            )
            # Extract the debts from this selection. As non of its
            # sub-selections can sum to 0, we get (selection-length - 1)
            # debts out of this selection
            debts.extend(get_debts_from(selection=selection))

    # Save the debts in database
    for debt in debts:
        debt.save()
