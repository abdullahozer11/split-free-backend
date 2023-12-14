from rest_framework import generics, viewsets

from .models import Event, Event, Expense, User, UserEventDebt
from .serializers import (
    UserSerializer,
    EventSerializer,
    ExpenseSerializer,
)
from .signals import event_created, expense_created


################################################################################
# User


class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


################################################################################
# Event


class EventList(generics.ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def perform_create(self, serializer):
        serializer.save()

        # Trigger the custom signal
        event_created.send(sender=self.__class__, instance=serializer.instance)


class EventDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer


################################################################################
# Expense


class ExpenseList(generics.ListCreateAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    def perform_create(self, serializer):
        serializer.save()

        # Trigger the custom signal
        expense_created.send(sender=self.__class__, instance=serializer.instance)


class ExpenseDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
