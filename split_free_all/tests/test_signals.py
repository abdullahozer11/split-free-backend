# Copyright (c) 2023 SplitFree Org.

from django.db.models.signals import post_save
from django.test import TestCase, override_settings

from split_free_all.models import Balance, Debt, Expense, Group, User
from split_free_all.signals import handle_group_created


class GroupSignalTests(TestCase):
    @override_settings(USE_TZ=False)  # Override settings to avoid issues with signals
    def setUp(self):
        # Disconnect the signal before the test starts
        post_save.disconnect(handle_group_created, sender=Group)

    @override_settings(USE_TZ=False)  # Override settings to avoid issues with signals
    def tearDown(self):
        # Reconnect the signal after the test is finished
        post_save.connect(handle_group_created, sender=Group)

    def test_handle_event_created_signal(self):
        # Create three users
        user1 = User.objects.create(name="Apo")
        user2 = User.objects.create(name="Michael")
        user3 = User.objects.create(name="Jeremy")

        # Create an event with these users
        data = {
            "title": "Birthday Party",
            "description": "A celebration",
            "members": [user1.id, user2.id, user3.id],
        }
        response = self.client.post("/api/events/", data)

        # Check that UserEventDebt objects were created (thanks to the signal)
        group_id = response.data["id"]
        group = Group.objects.get(id=group_id)
        users_group_debts = Balance.objects.filter(group=group)
        self.assertEqual(users_group_debts.count(), 3)

        # Check that the debt_balance is set to 0.0 for each user
        for user in [user1, user2, user3]:
            user_group_debt = users_group_debts.get(user=user)
            self.assertEqual(user_group_debt.amount, 0.0)

    def create_basic_group(self):
        # Create users
        self.members = [
            User.objects.create(name="Apo"),
            User.objects.create(name="Michael"),
            User.objects.create(name="Jake"),
            User.objects.create(name="John"),
        ]
        # Create an group with these members
        self.group = Group.objects.create(
            title="Day of eating",
            description="Breakfast, lunch and dinner",
        )
        # Add the created users to the group
        self.group.members.add(*self.members)
        # Create the debt with a balance of 0.00 as it would be with the creation
        # of the group
        for user in self.members:
            Balance.objects.create(user=user, group=self.group, amount=0.00)

        # Create expenses with these users within this group
        self.expenses = [
            Expense.objects.create(
                amount=10.00,
                title="Breakfast",
                description="Expense for breakfast",
                group=self.group,
                payer=self.members[0],
            ),
            Expense.objects.create(
                amount=20.00,
                title="Lunch",
                description="Expense for lunch",
                group=self.group,
                payer=self.members[1],
            ),
            Expense.objects.create(
                amount=40.00,
                title="Dinner",
                description="Expense for dinner",
                group=self.group,
                payer=self.members[2],
            ),
        ]
        # Involve all users in all expenses
        for expense in self.expenses:
            expense.participants.add(*self.members)

        # Update the associated debts that are usually updated with the creation
        # of the expense
        # User 1: -7.50 + 5 + 10 = 7.50
        debt_user1 = Balance.objects.get(user=self.members[0], group=self.group)
        debt_user1.amount = 7.50
        debt_user1.save()

        # User 2: 2.50 - 15 + 10 = -2.50
        debt_user2 = Balance.objects.get(user=self.members[1], group=self.group)
        debt_user2.amount = -2.50
        debt_user2.save()

        # User 3: 2.50 + 5 - 30 = -22.50
        debt_user3 = Balance.objects.get(user=self.members[2], group=self.group)
        debt_user3.amount = -22.50
        debt_user3.save()

        # User 4: 2.50 + 5 + 10 = 17.50
        debt_user4 = Balance.objects.get(user=self.members[3], group=self.group)
        debt_user4.amount = 17.50
        debt_user4.save()

    def test_handle_group_destroyed_signal(self):
        self.create_basic_group()

        self.client.delete(f"/api/events/{self.group.id}/")

        # This is the result of cascade deletion cause there is no signal but
        # it's left here, we never know if we add some signals one day
        self.assertEqual(Expense.objects.filter(group=self.group).count(), 0)
        self.assertEqual(Balance.objects.filter(group=self.group).count(), 0)
        self.assertEqual(Debt.objects.filter(group=self.group).count(), 0)


class ExpenseSignalTests(TestCase):
    @override_settings(USE_TZ=False)  # Override settings to avoid issues with signals
    def setUp(self):
        # Disconnect the signal before the test starts
        post_save.disconnect(handle_group_created, sender=Group)

    @override_settings(USE_TZ=False)  # Override settings to avoid issues with signals
    def tearDown(self):
        # Reconnect the signal after the test is finished
        post_save.connect(handle_group_created, sender=Group)

    def test_handle_expense_created_signal(self):
        # Create three users
        user1 = User.objects.create(name="Apo")
        user2 = User.objects.create(name="Michael")
        user3 = User.objects.create(name="Jeremy")

        # Create an group with these users
        group_data = {
            "title": "Holidays",
            "description": "Great holidays",
            "members": [user1.id, user2.id, user3.id],
        }
        response = self.client.post("/api/events/", group_data)
        group_id = response.data["id"]
        group = Group.objects.get(id=group_id)

        # Create an expense with these users
        expense_data = {
            "amount": 60.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": user2.id,
            "group": group.id,
            "participants": [user1.id, user2.id, user3.id],
        }
        self.client.post("/api/expenses/", expense_data)

        # Check the balance of each user
        self.assertEqual(
            Balance.objects.filter(group=group, user=user1).first().amount,
            20.00,
        )
        self.assertEqual(
            Balance.objects.filter(group=group, user=user2).first().amount,
            -40.00,
        )
        self.assertEqual(
            Balance.objects.filter(group=group, user=user3).first().amount,
            20.00,
        )

        # Check that 2 ideal transfers are created
        self.assertEqual(Debt.objects.filter(group=group).count(), 2)

    def create_basic_expense(self):
        # Create users
        self.members = [
            User.objects.create(name="Apo"),
            User.objects.create(name="Michael"),
            User.objects.create(name="Jake"),
        ]
        # Create an group with these users
        self.group = Group.objects.create(
            title="Holidays",
            description="Great holidays",
        )
        # Add the created users to the group
        self.group.members.add(*self.members)
        # Create the debt with a balance of 0.00 as it would be with the creation
        # of the group
        for user in self.members:
            Balance.objects.create(user=user, group=self.group, amount=0.00)

        # Create an expense with these users within this group
        self.expense = Expense.objects.create(
            amount=60.00,
            title="Dinner",
            description="Expense for dinner",
            group=self.group,
            payer=self.members[0],
        )
        # Add the created users to the expense
        self.expense.participants.add(*self.members)
        # Update the associated debts that are usually updated with the creation
        # of the expense
        debt_user1 = Balance.objects.get(user=self.members[0], group=self.group)
        debt_user1.amount = -40.00
        debt_user1.save()

        debt_user2 = Balance.objects.get(user=self.members[1], group=self.group)
        debt_user2.amount = 20.00
        debt_user2.save()

        debt_user3 = Balance.objects.get(user=self.members[2], group=self.group)
        debt_user3.amount = 20.00
        debt_user3.save()

    def test_handle_expense_updated_signal_added_users(self):
        self.create_basic_expense()

        # Create two new users their debts
        new_users = [
            User.objects.create(name="Maxim"),
            User.objects.create(name="Clement"),
        ]
        self.members.extend(new_users)
        for user in new_users:
            Balance.objects.create(user=user, group=self.group, amount=0.00)
        # Add the users to the group
        self.group.members.add(*new_users)

        # Update the expense by adding two users
        new_expense_data = {
            "amount": 60.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": self.members[0].id,
            "group": self.group.id,
            # Only this changes as there are now 4 users
            "participants": [user.id for user in self.members],
        }

        self.client.put(
            f"/api/expenses/{self.expense.id}/",
            new_expense_data,
            content_type="application/json",
        )
        self.assertEqual(self.expense.participants.count(), 5)
        self.assertEqual(Balance.objects.filter(group=self.group).count(), 5)

        for user_index, user in enumerate(self.members):
            balance = -48.00 if user_index == 0 else 12.00
            self.assertEqual(
                Balance.objects.get(user=user, group=self.group).amount,
                balance,
            )

        self.assertEqual(Debt.objects.filter(group=self.group).count(), 4)

    def test_handle_expense_updated_signal_removed_users(self):
        self.create_basic_expense()
        new_expense_data = {
            "amount": 60.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": self.members[0].id,
            "group": self.group.id,
            # We remove the last user, they are only two now
            "participants": [user.id for user in self.members[:-1]],
        }

        self.client.put(
            f"/api/expenses/{self.expense.id}/",
            new_expense_data,
            content_type="application/json",
        )
        self.assertEqual(self.expense.participants.count(), 2)

        expected_debts = [-30.00, 30.00, 0.00]
        for user_index, user in enumerate(self.members):
            self.assertEqual(
                Balance.objects.get(user=user, group=self.group).amount,
                expected_debts[user_index],
            )

        self.assertEqual(Debt.objects.filter(group=self.group).count(), 1)

    def test_handle_expense_updated_signal_new_amount(self):
        self.create_basic_expense()
        new_expense_data = {
            # The amount has changed from 60.00 to 90.00
            "amount": 90.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": self.members[0].id,
            "group": self.group.id,
            "participants": [user.id for user in self.members],
        }

        self.client.put(
            f"/api/expenses/{self.expense.id}/",
            new_expense_data,
            content_type="application/json",
        )

        expected_debts = [-60.00, 30.00, 30.00]
        for user_index, user in enumerate(self.members):
            self.assertEqual(
                Balance.objects.get(user=user, group=self.group).amount,
                expected_debts[user_index],
            )

        self.assertEqual(Debt.objects.filter(group=self.group).count(), 2)

    def test_handle_expense_updated_signal_changed_payer(self):
        self.create_basic_expense()
        new_expense_data = {
            "amount": 60.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            # The payer is not the first but the last user now
            "payer": self.members[-1].id,
            "group": self.group.id,
            "participants": [user.id for user in self.members],
        }

        self.client.put(
            f"/api/expenses/{self.expense.id}/",
            new_expense_data,
            content_type="application/json",
        )

        expected_debts = [20.00, 20.00, -40.00]
        for user_index, user in enumerate(self.members):
            self.assertEqual(
                Balance.objects.get(user=user, group=self.group).amount,
                expected_debts[user_index],
            )

        self.assertEqual(Debt.objects.filter(group=self.group).count(), 2)

    def test_handle_expense_destroyed(self):
        self.create_basic_expense()

        self.client.delete(f"/api/expenses/{self.expense.id}/")

        for user in self.members:
            self.assertEqual(
                Balance.objects.get(user=user, group=self.group).amount,
                0.00,
            )
        self.assertEqual(Debt.objects.filter(group=self.group).count(), 0)
