# Copyright (c) 2023 SplitFree Org.

from django.db.models.signals import post_save
from django.dispatch import Signal
from django.test import TestCase, override_settings

from split_free_all.models import Event, Expense, IdealTransfer, User, UserEventDebt
from split_free_all.signals import handle_event_created


class EventSignalTests(TestCase):
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

        # Check that 2 ideal transfers are created
        self.assertEqual(IdealTransfer.objects.filter(event=event).count(), 2)


class ExpenseSignalTests(TestCase):
    @override_settings(USE_TZ=False)  # Override settings to avoid issues with signals
    def setUp(self):
        # Disconnect the signal before the test starts
        post_save.disconnect(handle_event_created, sender=Event)

    @override_settings(USE_TZ=False)  # Override settings to avoid issues with signals
    def tearDown(self):
        # Reconnect the signal after the test is finished
        post_save.connect(handle_event_created, sender=Event)

    def test_handle_expense_updated_signal_added_users(self):
        # Create two users
        user1 = User.objects.create(name="Apo")
        user2 = User.objects.create(name="Michael")
        user3 = User.objects.create(name="Jeremy")
        user4 = User.objects.create(name="Maxim")
        users = [user1, user2, user3, user4]

        # Create an event with these users
        event = Event.objects.create(
            title="Holidays",
            description="Great holidays",
        )

        event.users.add(user1, user2, user3, user4)

        # Create the debt with a balance of 0.00 as it would be with the creation
        # of the event
        for user in users:
            UserEventDebt.objects.create(user=user, event=event, debt_balance=0.00)

        # Create an expense with these users within this event
        expense = Expense.objects.create(
            amount=60.00,
            title="Dinner",
            description="Expense for dinner",
            event=event,
            payer=user2,
        )

        expense.users.add(user1, user2)

        # Update the associated debts that are usually updated with the creation
        # of the expense
        debt_user1 = UserEventDebt.objects.get(user=user1, event=event)
        debt_user1.debt_balance = 30.00
        debt_user1.save()

        debt_user2 = UserEventDebt.objects.get(user=user2, event=event)
        debt_user2.debt_balance = -30.00
        debt_user2.save()

        # Update the expense by adding two users
        new_expense_data = {
            "amount": 60.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": user2.id,
            "event": event.id,
            "users": [user1.id, user2.id, user3.id, user4.id],
        }

        self.client.put(
            f"/api/expenses/{expense.id}/",
            new_expense_data,
            content_type="application/json",
        )
        self.assertEqual(expense.users.count(), 4)
        self.assertEqual(UserEventDebt.objects.filter(event=event).count(), 4)

        self.assertEqual(
            UserEventDebt.objects.get(user=user1, event=event).debt_balance, 15.00
        )
        self.assertEqual(
            UserEventDebt.objects.get(user=user2, event=event).debt_balance, -45.00
        )
        self.assertEqual(
            UserEventDebt.objects.get(user=user3, event=event).debt_balance, 15.00
        )
        self.assertEqual(
            UserEventDebt.objects.get(user=user4, event=event).debt_balance, 15.00
        )

        self.assertEqual(IdealTransfer.objects.filter(event=event).count(), 3)
