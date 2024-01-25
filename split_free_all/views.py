# Copyright (c) 2023 SplitFree Org.

from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from rest_framework import generics

from split_free_all.models import Debt, Expense, Group, Member, User
from split_free_all.serializers import (
    DebtSerializer,
    ExpenseSerializer,
    GroupSerializer,
    MemberSerializer,
    UserSerializer,
)
from split_free_all.signals import (
    expense_created,
    expense_destroyed,
    expense_updated,
    group_created,
    group_updated,
)

################################################################################
# User


class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


################################################################################
# Member


class MemberList(generics.ListCreateAPIView):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer


class MemberDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer


################################################################################
# Group


class GroupList(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def perform_create(self, serializer):
        serializer.save()

        member_names = self.request.data.get("member_names", [])

        # Trigger the custom signal
        group_created.send(
            sender=self.__class__,
            instance=serializer.instance,
            member_names=member_names,
        )


class GroupDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def perform_update(self, serializer):
        serializer.save()

        old_member_names = [member.name for member in serializer.instance.members.all()]
        new_member_names = self.request.data.get("member_names", [])

        # Trigger the custom signal
        group_updated.send(
            sender=self.__class__,
            instance=serializer.instance,
            old_member_names=old_member_names,
            new_member_names=new_member_names,
        )


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
            old_expense_info["participants"] != new_expense_info["participants"]
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

    def perform_destroy(self, instance):
        instance = self.get_object()
        # Trigger the custom signal
        expense_destroyed.send(sender=self.__class__, instance=instance)

        instance.delete()


################################################################################
# Debt


class DebtListView(generics.ListAPIView):
    serializer_class = DebtSerializer

    def get_queryset(self):
        group_id = self.request.query_params.get("group_id")
        if group_id:
            group = get_object_or_404(Group, pk=group_id)
            return Debt.objects.filter(group=group)

        return Debt.objects.all()
