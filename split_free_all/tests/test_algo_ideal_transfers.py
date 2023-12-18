from django.test import TestCase

from split_free_all.algo_ideal_transfers import calculate_new_ideal_transfers_data
from split_free_all.models import Event, IdealTransfer, User, UserEventDebt


class OurAlgoTests(TestCase):
    def assert_all_debts_paid(self, user_event_debts):
        event = user_event_debts[0].event
        debt_balance_map = dict.fromkeys(
            [user_event_debt.user for user_event_debt in user_event_debts], 0.00
        )
        for transfer in IdealTransfer.objects.filter(event=event):
            debt_balance_map[transfer.sender] += float(transfer.amount)
            debt_balance_map[transfer.receiver] -= float(transfer.amount)

        for user_event_debt in user_event_debts:
            self.assertEqual(
                user_event_debt.debt_balance, debt_balance_map[user_event_debt.user]
            )

    def test_with_three_users_in_one_event(self):
        # Create some users for creating the usersEventDebts
        user1 = User.objects.create(name="User1")
        user2 = User.objects.create(name="User2")
        user3 = User.objects.create(name="User3")

        # Create an event for for creating the usersEventDebts
        event = Event.objects.create(
            title="Test Event", description="Event for testing"
        )

        # Create three userEventDebts one for each of the user
        # The debts must sum up to 0
        user_event_debts = [
            UserEventDebt.objects.create(debt_balance=-40.00, user=user1, event=event),
            UserEventDebt.objects.create(debt_balance=20.00, user=user2, event=event),
            UserEventDebt.objects.create(debt_balance=20.00, user=user3, event=event),
        ]

        calculate_new_ideal_transfers_data(user_event_debts)

        self.assertEqual(IdealTransfer.objects.filter(event=event).count(), 2)
        self.assert_all_debts_paid(user_event_debts)
