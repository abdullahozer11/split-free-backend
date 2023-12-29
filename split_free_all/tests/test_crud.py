# Copyright (c) 2023 SplitFree Org.

from unittest.mock import patch

from django.test import TestCase
from rest_framework import status

from split_free_all.models import Balance, Expense, Group, User
from split_free_all.serializers import (
    ExpenseSerializer,
    GroupSerializer,
    UserSerializer,
)


class UserCRUDTests(TestCase):
    def test_create_user(self):
        data = {"name": "Apo"}
        response = self.client.post("/api/users/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().name, "Apo")

    def test_read_user(self):
        user = User.objects.create(name="Michael")
        response = self.client.get(f"/api/users/{user.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, UserSerializer(user).data)

    def test_update_user(self):
        user = User.objects.create(name="Apo")
        data = {"name": "Apo Jean"}
        response = self.client.put(
            f"/api/users/{user.id}/", data, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.name, "Apo Jean")

    def test_delete_user(self):
        user = User.objects.create(name="Michael")
        response = self.client.delete(f"/api/users/{user.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 0)


class GroupCRUDTests(TestCase):
    def setUp(self):
        # Create some users for testing
        self.user1 = User.objects.create(name="User1")
        self.user2 = User.objects.create(name="User2")

    def test_create_group(self):
        data = {
            "title": "Birthday Party",
            "description": "A celebration",
            "members": [self.user1.id, self.user2.id],
        }
        response = self.client.post("/api/groups/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Group.objects.count(), 1)
        group = Group.objects.get()
        self.assertEqual(group.title, "Birthday Party")
        self.assertEqual(group.members.count(), 2)

    def test_read_group(self):
        group = Group.objects.create(title="Anniversary", description="Special day")
        group.members.set([self.user1, self.user2])
        response = self.client.get(f"/api/groups/{group.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, GroupSerializer(group).data)

    def test_update_group(self):
        group = Group.objects.create(title="Conference", description="Tech event")
        group.members.set([self.user1])
        data = {
            "title": "Workshop",
            "description": "Interactive session",
            "members": [self.user2.id],
        }
        response = self.client.put(
            f"/api/groups/{group.id}/", data, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        group.refresh_from_db()
        self.assertEqual(group.title, "Workshop")
        self.assertEqual(group.members.count(), 1)
        self.assertEqual(group.members.first().name, "User2")

    def test_delete_group(self):
        group = Group.objects.create(title="Farewell", description="Goodbye party")
        group.members.set([self.user1, self.user2])
        response = self.client.delete(f"/api/groups/{group.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Group.objects.count(), 0)


class ExpenseCRUDTests(TestCase):
    def setUp(self):
        # Create some users for testing
        self.user1 = User.objects.create(name="User1")
        self.user2 = User.objects.create(name="User2")

        # Create an event for testing
        self.group = Group.objects.create(
            title="Test Event",
            description="Event for testing",
        )

        self.group.members.add(self.user1, self.user2)

        # Create associated balances. This usually comes with the creation of
        # the event using the post method, but as we are unit testing we use the
        # ORM instead
        Balance.objects.create(user=self.user1, group=self.group, amount=0.00)
        Balance.objects.create(user=self.user2, group=self.group, amount=0.00)

    def test_create_expense(self):
        data = {
            "amount": 50.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": self.user1.id,
            "group": self.group.id,
            "participants": [self.user1.id, self.user2.id],
        }
        response = self.client.post("/api/expenses/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 1)
        expense = Expense.objects.get()
        self.assertEqual(expense.title, "Dinner")
        self.assertEqual(expense.payer, self.user1)
        self.assertEqual(list(expense.participants.all()), [self.user1, self.user2])

    def test_read_expense(self):
        expense = Expense.objects.create(
            amount=30.00,
            title="Lunch",
            description="Expense for lunch",
            payer=self.user1,
            group=self.group,
        )
        expense.participants.set([self.user1, self.user2])
        response = self.client.get(f"/api/expenses/{expense.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, ExpenseSerializer(expense).data)

    @patch("split_free_all.signals.calculate_new_debts", side_effect=lambda group: None)
    def test_update_expense(self, _):
        expense = Expense.objects.create(
            amount=20.00,
            title="Coffee",
            description="Expense for coffee",
            payer=self.user1,
            group=self.group,
        )
        expense.participants.set([self.user1])
        data = {
            "amount": 25.00,
            "title": "Tea",
            "description": "Expense for tea",
            "payer": self.user2.id,
            "group": self.group.id,
            "participants": [self.user2.id],
        }
        response = self.client.put(
            f"/api/expenses/{expense.id}/", data, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expense.refresh_from_db()
        self.assertEqual(expense.amount, 25.00)
        self.assertEqual(expense.title, "Tea")
        self.assertEqual(expense.payer, self.user2)
        self.assertEqual(list(expense.participants.all()), [self.user2])

    def test_delete_expense(self):
        expense = Expense.objects.create(
            amount=40.00,
            title="Snacks",
            description="Expense for snacks",
            payer=self.user1,
            group=self.group,
        )
        expense.participants.set([self.user1, self.user2])
        response = self.client.delete(f"/api/expenses/{expense.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Expense.objects.count(), 0)
