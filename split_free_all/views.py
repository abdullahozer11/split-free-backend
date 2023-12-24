# Copyright (c) 2023 SplitFree Org.

from django.forms.models import model_to_dict
from rest_framework import generics, viewsets

from split_free_all.models import Event, Expense, User, UserEventDebt
from split_free_all.serializers import (
    EventSerializer,
    ExpenseSerializer,
    UserSerializer,
)
from split_free_all.signals import event_created, expense_created, expense_updated

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

    def perform_update(self, serializer):
        instance = self.get_object()
        old_expense_info = model_to_dict(instance)
        serializer.save()
        new_expense_info = model_to_dict(serializer.instance)

        if (
            old_expense_info["users"] != new_expense_info["users"]
            or old_expense_info["amount"] != new_expense_info["amount"]
            or old_expense_info["payer"] != new_expense_info["payer"]
        ):
            # Trigger the custom signal
            expense_updated.send(
                sender=self.__class__,
                instance=serializer.instance,
                old_expense_info=old_expense_info,
                new_expense_info=new_expense_info,
            )
