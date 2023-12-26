from django.test import TestCase

from split_free_all.algo_ideal_transfers import calculate_new_ideal_transfers_data
from split_free_all.models import Balance, Debt, Group, User


class OurAlgoTests(TestCase):
    def assert_all_debts_paid(self, user_group_debts):
        group = user_group_debts[0].group
        balance_map = dict.fromkeys(
            [user_group_debt.user for user_group_debt in user_group_debts], 0.00
        )
        for debt in Debt.objects.filter(group=group):
            balance_map[debt.borrower] += float(debt.amount)
            balance_map[debt.lender] -= float(debt.amount)

        for user_group_debt in user_group_debts:
            self.assertEqual(user_group_debt.amount, balance_map[user_group_debt.user])

    def test_with_three_users_in_one_group(self):
        # Create some users for creating the usersGroupDebts
        user1 = User.objects.create(name="User1")
        user2 = User.objects.create(name="User2")
        user3 = User.objects.create(name="User3")

        # Create a group for for creating the usersGroupDebts
        group = Group.objects.create(
            title="Test Group", description="Group for testing"
        )

        # Create three userGroupDebts one for each of the user
        # The debts must sum up to 0
        user_group_debts = [
            Balance.objects.create(amount=-40.00, user=user1, group=group),
            Balance.objects.create(amount=20.00, user=user2, group=group),
            Balance.objects.create(amount=20.00, user=user3, group=group),
        ]

        calculate_new_ideal_transfers_data(group=group)

        self.assertEqual(Debt.objects.filter(group=group).count(), 2)
        self.assert_all_debts_paid(user_group_debts)
