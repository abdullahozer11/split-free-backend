import json

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from split_free_all.models import Event, Expense, User
from split_free_all.serializers import (
    EventSerializer,
    ExpenseSerializer,
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


class EventCRUDTests(TestCase):
    def setUp(self):
        # Create some users for testing
        self.user1 = User.objects.create(name="User1")
        self.user2 = User.objects.create(name="User2")

    def test_create_event(self):
        data = {
            "title": "Birthday Party",
            "description": "A celebration",
            "users": [self.user1.id, self.user2.id],
        }
        response = self.client.post("/api/events/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.count(), 1)
        event = Event.objects.get()
        self.assertEqual(event.title, "Birthday Party")
        self.assertEqual(event.users.count(), 2)

    def test_read_event(self):
        event = Event.objects.create(title="Anniversary", description="Special day")
        event.users.set([self.user1, self.user2])
        response = self.client.get(f"/api/events/{event.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, EventSerializer(event).data)

    def test_update_event(self):
        event = Event.objects.create(title="Conference", description="Tech event")
        event.users.set([self.user1])
        data = {
            "title": "Workshop",
            "description": "Interactive session",
            "users": [self.user2.id],
        }
        response = self.client.put(
            f"/api/events/{event.id}/", data, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event.refresh_from_db()
        self.assertEqual(event.title, "Workshop")
        self.assertEqual(event.users.count(), 1)
        self.assertEqual(event.users.first().name, "User2")

    def test_delete_event(self):
        event = Event.objects.create(title="Farewell", description="Goodbye party")
        event.users.set([self.user1, self.user2])
        response = self.client.delete(f"/api/events/{event.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Event.objects.count(), 0)


class ExpenseCRUDTests(TestCase):
    def setUp(self):
        # Create some users for testing
        self.user1 = User.objects.create(name="User1")
        self.user2 = User.objects.create(name="User2")

        # Create an event for testing
        self.event = Event.objects.create(
            title="Test Event", description="Event for testing"
        )

    def test_create_expense(self):
        data = {
            "amount": 50.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": self.user1.id,
            "event": self.event.id,
            "users": [self.user1.id, self.user2.id],
        }
        response = self.client.post("/api/expenses/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expense.objects.count(), 1)
        expense = Expense.objects.get()
        self.assertEqual(expense.title, "Dinner")
        self.assertEqual(expense.payer, self.user1)
        self.assertEqual(list(expense.users.all()), [self.user1, self.user2])

    def test_read_expense(self):
        expense = Expense.objects.create(
            amount=30.00,
            title="Lunch",
            description="Expense for lunch",
            payer=self.user1,
            event=self.event,
        )
        expense.users.set([self.user1, self.user2])
        response = self.client.get(f"/api/expenses/{expense.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, ExpenseSerializer(expense).data)

    def test_update_expense(self):
        expense = Expense.objects.create(
            amount=20.00,
            title="Coffee",
            description="Expense for coffee",
            payer=self.user1,
            event=self.event,
        )
        expense.users.set([self.user1])
        data = {
            "amount": 25.00,
            "title": "Tea",
            "description": "Expense for tea",
            "payer": self.user2.id,
            "event": self.event.id,
            "users": [self.user2.id],
        }
        response = self.client.put(
            f"/api/expenses/{expense.id}/", data, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expense.refresh_from_db()
        self.assertEqual(expense.amount, 25.00)
        self.assertEqual(expense.title, "Tea")
        self.assertEqual(expense.payer, self.user2)
        self.assertEqual(list(expense.users.all()), [self.user2])

    def test_delete_expense(self):
        expense = Expense.objects.create(
            amount=40.00,
            title="Snacks",
            description="Expense for snacks",
            payer=self.user1,
            event=self.event,
        )
        expense.users.set([self.user1, self.user2])
        response = self.client.delete(f"/api/expenses/{expense.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Expense.objects.count(), 0)
