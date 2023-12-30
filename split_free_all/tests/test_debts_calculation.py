import random

from django.test import TestCase

from split_free_all.algo_debts import calculate_new_debts
from split_free_all.models import Balance, Debt, Group, User


class OurAlgoTests(TestCase):
    def assert_all_debts_paid(self, balances):
        group = balances[0].group
        # Dictionary whose key is a user an whose value is the balance in a group
        debt_checker = dict.fromkeys([balance.user for balance in balances], 0.00)
        for debt in Debt.objects.filter(group=group):
            debt_checker[debt.borrower] += float(debt.amount)
            debt_checker[debt.lender] -= float(debt.amount)

        for balance in balances:
            self.assertEqual(balance.amount, debt_checker[balance.user])

    def setUp(self):
        # Create a group
        self.group = Group.objects.create(
            title="Test Group", description="Group for testing"
        )

    def test_with_three_users_in_one_group(self):
        ### Setup
        # Create some users
        users = [
            User.objects.create(name="User1"),
            User.objects.create(name="User2"),
            User.objects.create(name="User3"),
        ]

        self.group.members.add(*users)

        # Create three userGroupDebts one for each of the user
        # The debts must sum up to 0
        balances = [
            Balance.objects.create(amount=-40.00, user=users[0], group=self.group),
            Balance.objects.create(amount=20.00, user=users[1], group=self.group),
            Balance.objects.create(amount=20.00, user=users[2], group=self.group),
        ]

        ### Action
        calculate_new_debts(group=self.group)

        ### Checks
        self.assertEqual(Debt.objects.filter(group=self.group).count(), 2)
        self.assert_all_debts_paid(balances)

    def test_member_with_null_balance(self):
        ### Setup
        users = [
            User.objects.create(name="A"),
            User.objects.create(name="B"),
            User.objects.create(name="C"),
            User.objects.create(name="D"),
        ]
        self.group.members.add(*users)

        balances = [
            Balance.objects.create(amount=0.00, user=users[0], group=self.group),
            Balance.objects.create(amount=-30.00, user=users[1], group=self.group),
            Balance.objects.create(amount=25.00, user=users[2], group=self.group),
            Balance.objects.create(amount=5.00, user=users[3], group=self.group),
        ]

        ### Action
        calculate_new_debts(group=self.group)

        ### Checks
        self.assertEqual(Debt.objects.filter(group=self.group).count(), 2)
        self.assert_all_debts_paid(balances)

    def test_members_cancelling_in_pairs(self):
        ### Setup
        number_of_members = 20
        users = [
            User.objects.create(name=f"User {i}") for i in range(number_of_members)
        ]
        self.group.members.add(*users)

        balances = []
        for i in range(0, number_of_members, 2):
            balances.append(
                Balance.objects.create(amount=100 + i, user=users[i], group=self.group)
            )
            balances.append(
                Balance.objects.create(
                    amount=-(100 + i), user=users[i + 1], group=self.group
                )
            )

        ### Action
        calculate_new_debts(group=self.group)

        ### Checks
        self.assertEqual(
            Debt.objects.filter(group=self.group).count(), int(number_of_members / 2)
        )
        self.assert_all_debts_paid(balances)

    def test_members_cancelling_in_pairs_and_triplets(self):
        ### Setup
        # The first 30 will cancel in triplets and the last 20 in pairs
        number_of_members = 10
        users = [
            User.objects.create(name=f"User {i}") for i in range(number_of_members)
        ]

        # Create a group
        group = Group.objects.create(
            title="Test Group", description="Group for testing"
        )

        group.members.add(*users)
        balances = []
        for i in range(0, int((3 / 5) * number_of_members), 3):
            balances.append(
                Balance.objects.create(amount=10 + i, user=users[i], group=self.group)
            )
            balances.append(
                Balance.objects.create(
                    amount=10 + i, user=users[i + 1], group=self.group
                )
            )
            balances.append(
                Balance.objects.create(
                    amount=-2 * (10 + i), user=users[i + 2], group=self.group
                )
            )
        for i in range(int((3 / 5) * number_of_members), number_of_members, 2):
            balances.append(
                Balance.objects.create(amount=100 + i, user=users[i], group=self.group)
            )
            balances.append(
                Balance.objects.create(
                    amount=-(100 + i), user=users[i + 1], group=self.group
                )
            )

        ### Action
        calculate_new_debts(group=self.group)

        ### Checks
        self.assertEqual(
            Debt.objects.filter(group=self.group).count(),
            int((3 / 5) * number_of_members),
        )
        self.assert_all_debts_paid(balances)
