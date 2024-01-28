# Copyright (c) 2023 SplitFree Org.

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from split_free_all.models import Balance, Debt, Expense, Group, Member
from split_free_all.serializers import (
    ExpenseSerializer,
    GroupSerializer,
    MemberSerializer,
)


class BaseAPITestCase(TestCase):
    def setUp(self):
        super().setUp()
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

        # Obtain a valid access token for the test user
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def get_auth_headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}


class MemberCRUDTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()

        # Create a group for testing
        self.group = Group.objects.create(
            title="Test Group",
            description="Group for testing",
        )

    def test_create_member(self):
        ### Set up
        data = {"name": "Apo", "group": self.group.id}

        ### Action
        response = self.client.post(
            "/api/members/", data, format="json", headers=self.get_auth_headers()
        )

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Member.objects.count(), 1)
        self.assertEqual(Member.objects.get().name, "Apo")

    def test_read_member(self):
        ### Setup
        member = Member.objects.create(name="Michael", group=self.group)

        ### Action
        response = self.client.get(
            f"/api/members/{member.id}/", format="json", headers=self.get_auth_headers()
        )

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, MemberSerializer(member).data)

    def test_update_member(self):
        ### Setup
        member = Member.objects.create(name="Apo", group=self.group)

        ### Action
        data = {"name": "Apo Jean", "group": self.group.id}

        ### Checks
        response = self.client.put(
            f"/api/members/{member.id}/",
            data,
            content_type="application/json",
            format="json",
            headers=self.get_auth_headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        member.refresh_from_db()
        self.assertEqual(member.name, "Apo Jean")

    def test_delete_member(self):
        ### Setup
        member = Member.objects.create(name="Michael", group=self.group)

        ### Action
        response = self.client.delete(
            f"/api/members/{member.id}/", format="json", headers=self.get_auth_headers()
        )

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Member.objects.count(), 0)


class GroupCRUDTests(BaseAPITestCase):
    def create_group_with_orm(self):
        self.group = Group.objects.create(
            title="Anniversary", description="Special day"
        )
        # Create two members for this group
        self.members = [
            Member.objects.create(name="Member1", group=self.group),
            Member.objects.create(name="Member2", group=self.group),
        ]

    def test_create_group(self):
        ### Setup
        data = {
            "title": "Birthday Party",
            "description": "A celebration",
            "member_names": ["Michael", "Apollon"],  # Guess who autocompleted that
        }

        ### Action
        response = self.client.post(
            "/api/groups/",
            data,
            content_type="application/json",
            format="json",
            headers=self.get_auth_headers(),
        )

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Group.objects.count(), 1)
        created_group = Group.objects.get()
        self.assertEqual(created_group.title, "Birthday Party")
        self.assertEqual(created_group.members.count(), 2)

    def test_read_group(self):
        ### Setup
        self.create_group_with_orm()

        ### Action
        response = self.client.get(
            f"/api/groups/{self.group.id}/",
            format="json",
            headers=self.get_auth_headers(),
        )

        ## Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, GroupSerializer(self.group).data)

    def test_update_group(self):
        ### Setup
        self.create_group_with_orm()
        data = {
            "title": "Workshop",
            "description": "Interactive session",
            "member_names": ["Member2"],
        }

        ### Action
        response = self.client.put(
            f"/api/groups/{self.group.id}/",
            data,
            content_type="application/json",
            format="json",
            headers=self.get_auth_headers(),
        )

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.group.refresh_from_db()
        self.assertEqual(self.group.title, "Workshop")
        self.assertEqual(self.group.members.count(), 1)
        self.assertEqual(self.group.members.first().name, "Member2")

    def test_delete_group(self):
        ### Setup
        self.create_group_with_orm()

        ### Action
        response = self.client.delete(
            f"/api/groups/{self.group.id}/",
            format="json",
            headers=self.get_auth_headers(),
        )

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Group.objects.count(), 0)


class ExpenseCRUDTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        # Create a group for testing
        self.group = Group.objects.create(
            title="Test Group",
            description="Group for testing",
        )

        # Create some members for testing
        self.member1 = Member.objects.create(name="Member1", group=self.group)
        self.member2 = Member.objects.create(name="Member2", group=self.group)

        # Create associated balances. This usually comes with the creation of
        # the group using the post method, but as we are unit testing we use the
        # ORM instead
        Balance.objects.create(owner=self.member1, group=self.group, amount=0.00)
        Balance.objects.create(owner=self.member2, group=self.group, amount=0.00)

    def test_create_expense(self):
        ### Actions
        data = {
            "amount": 50.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": self.member1.id,
            "group": self.group.id,
            "participants": [self.member1.id, self.member2.id],
        }
        response = self.client.post(
            "/api/expenses/", data, format="json", headers=self.get_auth_headers()
        )

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 1)
        expense = Expense.objects.get()
        self.assertEqual(expense.title, "Dinner")
        self.assertEqual(expense.payer, self.member1)
        self.assertEqual(expense.currency, "EUR")
        self.assertEqual(list(expense.participants.all()), [self.member1, self.member2])

    def test_read_expense(self):
        ### Setup
        expense = Expense.objects.create(
            amount=30.00,
            title="Lunch",
            description="Expense for lunch",
            payer=self.member1,
            group=self.group,
        )
        expense.participants.set([self.member1, self.member2])

        ### Action
        response = self.client.get(
            f"/api/expenses/{expense.id}/",
            format="json",
            headers=self.get_auth_headers(),
        )

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
            payer=self.member1,
            group=self.group,
        )
        expense.participants.set([self.member1])

        ### Action
        data = {
            "amount": 25.00,
            "title": "Tea",
            "description": "Expense for tea",
            "payer": self.member2.id,
            "group": self.group.id,
            "participants": [self.member2.id],
        }
        response = self.client.put(
            f"/api/expenses/{expense.id}/",
            data,
            content_type="application/json",
            format="json",
            headers=self.get_auth_headers(),
        )

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expense.refresh_from_db()
        self.assertEqual(expense.amount, 25.00)
        self.assertEqual(expense.title, "Tea")
        self.assertEqual(expense.payer, self.member2)
        self.assertEqual(list(expense.participants.all()), [self.member2])

    def test_delete_expense(self):
        ### Setup
        expense = Expense.objects.create(
            amount=40.00,
            title="Snacks",
            description="Expense for snacks",
            payer=self.member1,
            group=self.group,
        )
        expense.participants.set([self.member1, self.member2])

        ### Action
        response = self.client.delete(
            f"/api/expenses/{expense.id}/",
            format="json",
            headers=self.get_auth_headers(),
        )

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Expense.objects.count(), 0)


class DebtTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()

        self.groups = [
            Group.objects.create(
                title="Friend group", description="This group is friendly"
            ),
            Group.objects.create(
                title="Normal group", description="This group is normal"
            ),
        ]

        self.members = [
            # Members of groups[0]
            Member.objects.create(name="Apo", group=self.groups[0]),
            Member.objects.create(name="Michael", group=self.groups[0]),
            Member.objects.create(name="George", group=self.groups[0]),
            # Members of groups[1]
            Member.objects.create(name="Apo", group=self.groups[1]),
            Member.objects.create(name="Michael", group=self.groups[1]),
        ]

    def test_get_all_debts(self):
        ### Setup
        # Let's create some meaningful debts and get them all
        Debt.objects.create(
            group=self.groups[0],
            borrower=self.members[0],
            lender=self.members[1],
            amount=100.00,
        )
        Debt.objects.create(
            group=self.groups[0],
            borrower=self.members[2],
            lender=self.members[1],
            amount=50.00,
        )

        Debt.objects.create(
            group=self.groups[1],
            borrower=self.members[1],
            lender=self.members[0],
            amount=10.00,
        )

        ### Action
        response = self.client.get(
            f"/api/debts/", format="json", headers=self.get_auth_headers()
        )

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_filter_debts_by_group(self):
        ### Setup
        Debt.objects.create(
            group=self.groups[0],
            borrower=self.members[0],
            lender=self.members[1],
            amount=100.00,
        )
        Debt.objects.create(
            group=self.groups[0],
            borrower=self.members[2],
            lender=self.members[1],
            amount=50.00,
        )
        Debt.objects.create(
            group=self.groups[1],
            borrower=self.members[1],
            lender=self.members[0],
            amount=10.00,
        )

        ### Action
        # Filter debts for a specific group (groups[0])
        response = self.client.get(
            f"/api/debts/",
            {"group_id": self.groups[0].id},
            format="json",
            headers=self.get_auth_headers(),
        )

        ### Checks
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Ensure that all debts in the response belong to groups[0]
        for debt in response.data:
            self.assertEqual(debt["group"], self.groups[0].id)
