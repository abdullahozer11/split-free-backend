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


class ExpenseSignalTests(TestCase):
    @override_settings(USE_TZ=False)  # Override settings to avoid issues with signals
    def setUp(self):
        # Disconnect the signal before the test starts
        post_save.disconnect(handle_event_created, sender=Event)

    @override_settings(USE_TZ=False)  # Override settings to avoid issues with signals
    def tearDown(self):
        # Reconnect the signal after the test is finished
        post_save.connect(handle_event_created, sender=Event)

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

    def create_basic_expense(self):
        # Create users
        self.users = [
            User.objects.create(name="Apo"),
            User.objects.create(name="Michael"),
            User.objects.create(name="Jake"),
        ]
        # Create an event with these users
        self.event = Event.objects.create(
            title="Holidays",
            description="Great holidays",
        )
        # Add the created users to the event
        self.event.users.add(*self.users)
        # Create the debt with a balance of 0.00 as it would be with the creation
        # of the event
        for user in self.users:
            UserEventDebt.objects.create(user=user, event=self.event, debt_balance=0.00)

        # Create an expense with these users within this event
        self.expense = Expense.objects.create(
            amount=60.00,
            title="Dinner",
            description="Expense for dinner",
            event=self.event,
            payer=self.users[0],
        )
        # Add the created users to the expense
        self.expense.users.add(*self.users)
        # Update the associated debts that are usually updated with the creation
        # of the expense
        debt_user1 = UserEventDebt.objects.get(user=self.users[0], event=self.event)
        debt_user1.debt_balance = -40.00
        debt_user1.save()

        debt_user2 = UserEventDebt.objects.get(user=self.users[1], event=self.event)
        debt_user2.debt_balance = 20.00
        debt_user2.save()

        debt_user3 = UserEventDebt.objects.get(user=self.users[2], event=self.event)
        debt_user3.debt_balance = 20.00
        debt_user3.save()

    def test_handle_expense_updated_signal_added_users(self):
        self.create_basic_expense()

        # Create two new users their debts
        new_users = [
            User.objects.create(name="Maxim"),
            User.objects.create(name="Clement"),
        ]
        self.users.extend(new_users)
        for user in new_users:
            UserEventDebt.objects.create(user=user, event=self.event, debt_balance=0.00)
        # Add the users to the event
        self.event.users.add(*new_users)

        # Update the expense by adding two users
        new_expense_data = {
            "amount": 60.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": self.users[0].id,
            "event": self.event.id,
            # Only this changes as there are now 4 users
            "users": [user.id for user in self.users],
        }

        self.client.put(
            f"/api/expenses/{self.expense.id}/",
            new_expense_data,
            content_type="application/json",
        )
        self.assertEqual(self.expense.users.count(), 5)
        self.assertEqual(UserEventDebt.objects.filter(event=self.event).count(), 5)

        for user_index, user in enumerate(self.users):
            debt_balance = -48.00 if user_index == 0 else 12.00
            self.assertEqual(
                UserEventDebt.objects.get(user=user, event=self.event).debt_balance,
                debt_balance,
            )

        self.assertEqual(IdealTransfer.objects.filter(event=self.event).count(), 4)

    def test_handle_expense_updated_signal_removed_users(self):
        self.create_basic_expense()
        new_expense_data = {
            "amount": 60.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": self.users[0].id,
            "event": self.event.id,
            # We remove the last user, they are only two now
            "users": [user.id for user in self.users[:-1]],
        }

        self.client.put(
            f"/api/expenses/{self.expense.id}/",
            new_expense_data,
            content_type="application/json",
        )
        self.assertEqual(self.expense.users.count(), 2)

        expected_debts = [-30.00, 30.00, 0.00]
        for user_index, user in enumerate(self.users):
            self.assertEqual(
                UserEventDebt.objects.get(user=user, event=self.event).debt_balance,
                expected_debts[user_index],
            )

        self.assertEqual(IdealTransfer.objects.filter(event=self.event).count(), 1)

    def test_handle_expense_updated_signal_new_amount(self):
        self.create_basic_expense()
        new_expense_data = {
            # The amount has changed from 60.00 to 90.00
            "amount": 90.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": self.users[0].id,
            "event": self.event.id,
            "users": [user.id for user in self.users],
        }

        self.client.put(
            f"/api/expenses/{self.expense.id}/",
            new_expense_data,
            content_type="application/json",
        )

        expected_debts = [-60.00, 30.00, 30.00]
        for user_index, user in enumerate(self.users):
            self.assertEqual(
                UserEventDebt.objects.get(user=user, event=self.event).debt_balance,
                expected_debts[user_index],
            )

        self.assertEqual(IdealTransfer.objects.filter(event=self.event).count(), 2)

    def test_handle_expense_updated_signal_changed_payer(self):
        self.create_basic_expense()
        new_expense_data = {
            "amount": 60.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            # The payer is not the first but the last user now
            "payer": self.users[-1].id,
            "event": self.event.id,
            "users": [user.id for user in self.users],
        }

        self.client.put(
            f"/api/expenses/{self.expense.id}/",
            new_expense_data,
            content_type="application/json",
        )

        expected_debts = [20.00, 20.00, -40.00]
        for user_index, user in enumerate(self.users):
            self.assertEqual(
                UserEventDebt.objects.get(user=user, event=self.event).debt_balance,
                expected_debts[user_index],
            )

        self.assertEqual(IdealTransfer.objects.filter(event=self.event).count(), 2)
