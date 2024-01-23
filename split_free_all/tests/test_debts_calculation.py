import random

from django.test import TestCase

from split_free_all.algo_debts import calculate_new_debts
from split_free_all.models import Balance, Debt, Group, Member


class OurAlgoTests(TestCase):
    def assert_all_debts_paid(self, balances):
        group = balances[0].group
        # Dictionary whose key is a member an whose value is the balance in a group
        debt_checker = dict.fromkeys([balance.owner for balance in balances], 0.00)
        for debt in Debt.objects.filter(group=group):
            debt_checker[debt.borrower] += float(debt.amount)
            debt_checker[debt.lender] -= float(debt.amount)

        for balance in balances:
            self.assertEqual(balance.amount, debt_checker[balance.owner])

    def setUp(self):
        # Create a group
        self.group = Group.objects.create(
            title="Test Group", description="Group for testing"
        )

    def test_with_three_members_in_one_group(self):
        ### Setup
        # Create some members
        members = [
            Member.objects.create(name="Member1"),
            Member.objects.create(name="Member2"),
            Member.objects.create(name="Member3"),
        ]

        self.group.members.set(members)

        # Create three memberGroupDebts one for each of the member
        # The debts must sum up to 0
        balances = [
            Balance.objects.create(amount=-40.00, owner=members[0], group=self.group),
            Balance.objects.create(amount=20.00, owner=members[1], group=self.group),
            Balance.objects.create(amount=20.00, owner=members[2], group=self.group),
        ]

        ### Action
        calculate_new_debts(group=self.group)

        ### Checks
        self.assertEqual(Debt.objects.filter(group=self.group).count(), 2)
        self.assert_all_debts_paid(balances)

    def test_member_with_null_balance(self):
        ### Setup
        members = [
            Member.objects.create(name="A"),
            Member.objects.create(name="B"),
            Member.objects.create(name="C"),
            Member.objects.create(name="D"),
        ]
        self.group.members.set(members)

        balances = [
            Balance.objects.create(amount=0.00, owner=members[0], group=self.group),
            Balance.objects.create(amount=-30.00, owner=members[1], group=self.group),
            Balance.objects.create(amount=25.00, owner=members[2], group=self.group),
            Balance.objects.create(amount=5.00, owner=members[3], group=self.group),
        ]

        ### Action
        calculate_new_debts(group=self.group)

        ### Checks
        self.assertEqual(Debt.objects.filter(group=self.group).count(), 2)
        self.assert_all_debts_paid(balances)

    def test_members_cancelling_in_pairs(self):
        ### Setup
        number_of_members = 20
        members = [
            Member.objects.create(name=f"Member {i}") for i in range(number_of_members)
        ]
        self.group.members.set(members)

        balances = []
        for i in range(0, number_of_members, 2):
            balances.append(
                Balance.objects.create(
                    amount=100 + i, owner=members[i], group=self.group
                )
            )
            balances.append(
                Balance.objects.create(
                    amount=-(100 + i), owner=members[i + 1], group=self.group
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
        # The first 9 will cancel in triplets and the last 6 in pairs
        number_of_members = 15
        members = [
            Member.objects.create(name=f"Member {i}") for i in range(number_of_members)
        ]

        # Create a group
        group = Group.objects.create(
            title="Test Group", description="Group for testing"
        )

        group.members.set(members)
        balances = []
        for i in range(0, int((3 / 5) * number_of_members), 3):
            balances.append(
                Balance.objects.create(
                    amount=10 + i, owner=members[i], group=self.group
                )
            )
            balances.append(
                Balance.objects.create(
                    amount=10 + i, owner=members[i + 1], group=self.group
                )
            )
            balances.append(
                Balance.objects.create(
                    amount=-2 * (10 + i), owner=members[i + 2], group=self.group
                )
            )
        for i in range(int((3 / 5) * number_of_members), number_of_members, 2):
            balances.append(
                Balance.objects.create(
                    amount=100 + i, owner=members[i], group=self.group
                )
            )
            balances.append(
                Balance.objects.create(
                    amount=-(100 + i), owner=members[i + 1], group=self.group
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
