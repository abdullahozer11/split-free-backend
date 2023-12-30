# Copyright (c) 2023 SplitFree Org.

from unittest.mock import patch

from django.test import TestCase
from rest_framework import status

from split_free_all.models import Balance, Debt, Expense, Group, User
from split_free_all.serializers import (
    ExpenseSerializer,
    GroupSerializer,
    UserSerializer,
)


class UserCRUDTests(TestCase):
    def test_create_user(self):
        ### Set up
        data = {"name": "Apo"}

        ### Action
        response = self.client.post("/api/users/", data)

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().name, "Apo")

    def test_read_user(self):
        ### Setup
        user = User.objects.create(name="Michael")

        ### Action
        response = self.client.get(f"/api/users/{user.id}/")

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, UserSerializer(user).data)

    def test_update_user(self):
        ### Setup
        user = User.objects.create(name="Apo")

        ### Action
        data = {"name": "Apo Jean"}

        ### Checks
        response = self.client.put(
            f"/api/users/{user.id}/", data, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.name, "Apo Jean")

    def test_delete_user(self):
        ### Setup
        user = User.objects.create(name="Michael")

        ### Action
        response = self.client.delete(f"/api/users/{user.id}/")

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 0)


class GroupCRUDTests(TestCase):
    def setUp(self):
        # Create some users for testing
        self.user1 = User.objects.create(name="User1")
        self.user2 = User.objects.create(name="User2")

    def test_create_group(self):
        ### Setup
        data = {
            "title": "Birthday Party",
            "description": "A celebration",
            "members": [self.user1.id, self.user2.id],
        }

        ### Action
        response = self.client.post("/api/groups/", data)

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Group.objects.count(), 1)
        group = Group.objects.get()
        self.assertEqual(group.title, "Birthday Party")
        self.assertEqual(group.members.count(), 2)

    def test_read_group(self):
        ### Setup
        group = Group.objects.create(title="Anniversary", description="Special day")
        group.members.set([self.user1, self.user2])

        ### Action
        response = self.client.get(f"/api/groups/{group.id}/")

        ## Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, GroupSerializer(group).data)

    def test_update_group(self):
        ### Setup
        group = Group.objects.create(title="Conference", description="Tech group")
        group.members.set([self.user1])
        data = {
            "title": "Workshop",
            "description": "Interactive session",
            "members": [self.user2.id],
        }

        ### Action
        response = self.client.put(
            f"/api/groups/{group.id}/", data, content_type="application/json"
        )

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        group.refresh_from_db()
        self.assertEqual(group.title, "Workshop")
        self.assertEqual(group.members.count(), 1)
        self.assertEqual(group.members.first().name, "User2")

    def test_delete_group(self):
        ### Setup
        group = Group.objects.create(title="Farewell", description="Goodbye party")
        group.members.set([self.user1, self.user2])

        ### Action
        response = self.client.delete(f"/api/groups/{group.id}/")

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Group.objects.count(), 0)


class ExpenseCRUDTests(TestCase):
    def setUp(self):
        # Create some users for testing
        self.user1 = User.objects.create(name="User1")
        self.user2 = User.objects.create(name="User2")

        # Create a group for testing
        self.group = Group.objects.create(
            title="Test Group",
            description="Group for testing",
        )

        self.group.members.set([self.user1, self.user2])

        # Create associated balances. This usually comes with the creation of
        # the group using the post method, but as we are unit testing we use the
        # ORM instead
        Balance.objects.create(user=self.user1, group=self.group, amount=0.00)
        Balance.objects.create(user=self.user2, group=self.group, amount=0.00)

    def test_create_expense(self):
        ### Actions
        data = {
            "amount": 50.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": self.user1.id,
            "group": self.group.id,
            "participants": [self.user1.id, self.user2.id],
        }
        response = self.client.post("/api/expenses/", data)

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 1)
        expense = Expense.objects.get()
        self.assertEqual(expense.title, "Dinner")
        self.assertEqual(expense.payer, self.user1)
        self.assertEqual(list(expense.participants.all()), [self.user1, self.user2])

    def test_read_expense(self):
        ### Setup
        expense = Expense.objects.create(
            amount=30.00,
            title="Lunch",
            description="Expense for lunch",
            payer=self.user1,
            group=self.group,
        )
        expense.participants.set([self.user1, self.user2])

        ### Action
        response = self.client.get(f"/api/expenses/{expense.id}/")

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, ExpenseSerializer(expense).data)

    @patch("split_free_all.signals.calculate_new_debts", side_effect=lambda group: None)
    def test_update_expense(self, _):
        ### Setup
        expense = Expense.objects.create(
            amount=20.00,
            title="Coffee",
            description="Expense for coffee",
            payer=self.user1,
            group=self.group,
        )
        expense.participants.set([self.user1])

        ### Action
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

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expense.refresh_from_db()
        self.assertEqual(expense.amount, 25.00)
        self.assertEqual(expense.title, "Tea")
        self.assertEqual(expense.payer, self.user2)
        self.assertEqual(list(expense.participants.all()), [self.user2])

    def test_delete_expense(self):
        ### Setup
        expense = Expense.objects.create(
            amount=40.00,
            title="Snacks",
            description="Expense for snacks",
            payer=self.user1,
            group=self.group,
        )
        expense.participants.set([self.user1, self.user2])

        ### Action
        response = self.client.delete(f"/api/expenses/{expense.id}/")

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Expense.objects.count(), 0)


class DebtTests(TestCase):
    def setUp(self):
        self.users = [
            User.objects.create(name="Apo"),
            User.objects.create(name="Michael"),
            User.objects.create(name="George"),
        ]

        self.groups = [
            Group.objects.create(
                title="Friend group", description="This group is friendly"
            ),
            Group.objects.create(
                title="Normal group", description="This group is normal"
            ),
        ]
        self.groups[0].members.set(self.users)
        self.groups[1].members.set(self.users[:-1])

    def test_get_all_debts(self):
        ### Setup
        # Let's create some meaningful debts and get them all
        Debt.objects.create(
            group=self.groups[0],
            borrower=self.users[0],
            lender=self.users[1],
            amount=100.00,
        )
        Debt.objects.create(
            group=self.groups[0],
            borrower=self.users[2],
            lender=self.users[1],
            amount=50.00,
        )

        Debt.objects.create(
            group=self.groups[1],
            borrower=self.users[1],
            lender=self.users[0],
            amount=10.00,
        )

        ### Action
        response = self.client.get(f"/api/debts/")

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_filter_debts_by_group(self):
        ### Setup
        Debt.objects.create(
            group=self.groups[0],
            borrower=self.users[0],
            lender=self.users[1],
            amount=100.00,
        )
        Debt.objects.create(
            group=self.groups[0],
            borrower=self.users[2],
            lender=self.users[1],
            amount=50.00,
        )
        Debt.objects.create(
            group=self.groups[1],
            borrower=self.users[1],
            lender=self.users[0],
            amount=10.00,
        )

        ### Action
        # Filter debts for a specific group (groups[0])
        response = self.client.get(f"/api/debts/", {"group_id": self.groups[0].id})

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Ensure that all debts in the response belong to groups[0]
        for debt in response.data:
            self.assertEqual(debt["group"], self.groups[0].id)
