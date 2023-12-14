from django.db.models.signals import post_save
from django.dispatch import Signal
from django.test import TestCase, override_settings

from split_free_all.models import Event, User, UserEventDebt
from split_free_all.signals import handle_event_created


class SignalTests(TestCase):
    @override_settings(USE_TZ=False)  # Override settings to avoid issues with signals
    def setUp(self):
        # Disconnect the signal before the test starts
        post_save.disconnect(handle_event_created, sender=Event)

    @override_settings(USE_TZ=False)  # Override settings to avoid issues with signals
    def tearDown(self):
        # Reconnect the signal after the test is finished
        post_save.connect(handle_event_created, sender=Event)

    def test_handle_event_created_signal(self):
        # Create three users
        user1 = User.objects.create(name="Apo")
        user2 = User.objects.create(name="Michael")
        user3 = User.objects.create(name="Jeremy")

        # Create an event with these users
        data = {
            "title": "Birthday Party",
            "description": "A celebration",
            "users": [user1.id, user2.id, user3.id],
        }
        response = self.client.post("/api/events/", data)

        # Check that UserEventDebt objects were created (thanks to the signal)
        event_id = response.data["id"]
        event = Event.objects.get(id=event_id)
        users_event_debts = UserEventDebt.objects.filter(event=event)
        self.assertEqual(users_event_debts.count(), 3)

        # Check that the debt_balance is set to 0.0 for each user
        for user in [user1, user2, user3]:
            user_event_debt = users_event_debts.get(user=user)
            self.assertEqual(user_event_debt.debt_balance, 0.0)

    def test_handle_expense_created_signal(self):
        # Create three users
        user1 = User.objects.create(name="Apo")
        user2 = User.objects.create(name="Michael")
        user3 = User.objects.create(name="Jeremy")

        # Create an event with these users
        event_data = {
            "title": "Holidays",
            "description": "Great holidays",
            "users": [user1.id, user2.id, user3.id],
        }
        response = self.client.post("/api/events/", event_data)
        event_id = response.data["id"]
        event = Event.objects.get(id=event_id)

        # Create an expense with these users
        expense_data = {
            "amount": 60.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": user2.id,
            "event": event.id,
            "users": [user1.id, user2.id, user3.id],
        }
        self.client.post("/api/expenses/", expense_data)

        # Check the balance of each user
        self.assertEqual(
            UserEventDebt.objects.filter(event=event, user=user1).first().debt_balance,
            20.00,
        )
        self.assertEqual(
            UserEventDebt.objects.filter(event=event, user=user2).first().debt_balance,
            -40.00,
        )
        self.assertEqual(
            UserEventDebt.objects.filter(event=event, user=user3).first().debt_balance,
            20.00,
        )
