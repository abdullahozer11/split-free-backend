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

    def test_with_three_users_in_one_group(self):
        # Create some users
        users = [
            User.objects.create(name="User1"),
            User.objects.create(name="User2"),
            User.objects.create(name="User3"),
        ]

        # Create a group
        group = Group.objects.create(
            title="Test Group", description="Group for testing"
        )

        group.members.add(*users)

        # Create three userGroupDebts one for each of the user
        # The debts must sum up to 0
        balances = [
            Balance.objects.create(amount=-40.00, user=users[0], group=group),
            Balance.objects.create(amount=20.00, user=users[1], group=group),
            Balance.objects.create(amount=20.00, user=users[2], group=group),
        ]

        calculate_new_debts(group=group)

        self.assertEqual(Debt.objects.filter(group=group).count(), 2)
        self.assert_all_debts_paid(balances)
