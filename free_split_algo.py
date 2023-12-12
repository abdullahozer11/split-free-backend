# Input: a list of tuples with a name an a credit
# ex:
# [
#     {
#         "name": "Apo",
#         value: 1,
#     },
#     {
#         "name": "Maxim",
#         value: 2,
#     },
#     {
#         "name": "Michael",
#         value: -3,
#     },
# ]
# Output: a list of transactions to reestablish the balance
# With the above example:
# [('Michael', 'Apo', 1), ('Michael', 'Maxim', 2)]

# Step 1:
# Sort the list of tuples relatively to their credit value
# Step 2:
# Search an isolate groups of tuples whose credits sum equals to 0
# First search groups of 1 tuple, then 2, then 3... until dealing with all tuples
# Step 3:
# For each group of tuple, sort them relatively to their credit value
# Step 4:
# Pair the tuple with the smallest absolute credit value that is negative with
# the tuple with the tuple with the highest absolute value that is positive to
# make a transaction between them so that one of them has a credit of 0 after
# the operation. Iterate until all transactions are made

def get_tuples_with_sum(credits, number_of_tuples, target=0):
    if number_of_tuples == 1:
        for credit in credits:
            if credit["value"] == target:
                return [credit]
        return []

    if number_of_tuples == 2:
        low_index = 0
        high_index = len(credits) - 1
        while low_index < high_index:
            sum_credits = credits[low_index]["value"] + credits[high_index]["value"]
            if sum_credits < target:
                low_index += 1
            elif sum_credits > target:
                high_index -= 1
            else:
                return [credits[low_index], credits[high_index]]
        return []

    for i in range(len(credits)-(number_of_tuples-1)):
        potential_targets = get_tuples_with_sum(
            credits[i+1:],
            number_of_tuples=number_of_tuples-1,
            target=target-credits[i]["value"],
        )
        if potential_targets:
            return [credits[i]] + potential_targets
        return []

    return []

def get_transactions_with(tuples):
    transactions = []
    while tuples:
        diff = tuples[-1]["value"] - abs(tuples[0]["value"])
        if diff > 0:
            transactions.append(
                (
                    tuples[0]["name"],
                    tuples[-1]["name"],
                    tuples[0]["value"]
                )
            )
            tuples[-1]["value"] -= tuples[0]["value"]
            tuples.pop(0)

        elif diff < 0:
            transactions.append(
                (
                    tuples[0]["name"],
                    tuples[-1]["name"],
                    tuples[-1]["value"]
                )
            )
            tuples[0]["value"] += tuples[-1]["value"]
            tuples.pop()
        else:
            transactions.append(
                (
                    tuples[0]["name"],
                    tuples[-1]["name"],
                    tuples[-1]["value"]
                )
            )
            tuples.pop(-1)
            tuples.pop(0)
    return transactions

def remove_tuples_from_credits(credits, tuples):
    names = [t['name'] for t in tuples]
    new_credits = []
    for credit in credits:
        if not credit['name'] in names:
            new_credits.append(credit)
    return new_credits

def balance_transactions(credits):
    credits = sorted(credits, key=lambda x: x["value"])
    number_of_tuples = 1
    all_transactions = []
    while credits:
        if number_of_tuples > len(credits) // 2:
            number_of_tuples = len(credits)
        tuples = get_tuples_with_sum(credits, number_of_tuples)
        if not tuples:
            number_of_tuples += 1
        else:
            credits = remove_tuples_from_credits(credits, tuples)
            transactions = get_transactions_with(tuples)
            all_transactions.append(transactions)
    return all_transactions

    all_transactions

credits = [
    {
        "name": "Apo",
        "value": 1,
    },
    {
        "name": "Maxim",
        "value": 2,
    },
    {
        "name": "Michael",
        "value": -3,
    },
]
transactions = balance_transactions(credits)
print(transactions)

