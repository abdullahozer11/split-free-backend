# Copyright (c) 2023 SplitFree Org.

from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from split_free_all.models import Balance, Debt, Expense, Group, Member, User
from split_free_all.serializers import (
    BalanceSerializer,
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


class UserView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        # Save the user
        user = serializer.save()

        # Get tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Build the response data
        response_data = {
            "refresh": str(refresh),
            "access": access_token,
        }

        # Set the response status and data
        self.response_status = status.HTTP_201_CREATED
        self.response_data = response_data

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            self.response_data, status=self.response_status, headers=headers
        )


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


################################################################################
# Member


class MemberView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MemberSerializer

    def get_queryset(self):
        group_id = self.request.query_params.get("group_id")
        if group_id:
            group = get_object_or_404(Group, pk=group_id)
            return Member.objects.filter(group=group)

        return Member.objects.all()


class MemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Member.objects.all()
    serializer_class = MemberSerializer


################################################################################
# Group


class GroupView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(users=self.request.user)

    def perform_create(self, serializer):
        serializer.save()

        member_names = self.request.data.get("member_names", [])

        # Trigger the custom signal
        group_created.send(
            sender=self.__class__,
            instance=serializer.instance,
            member_names=member_names,
        )


class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
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


class ExpenseView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    def perform_create(self, serializer):
        serializer.save()

        # Trigger the custom signal
        expense_created.send(sender=self.__class__, instance=serializer.instance)

    def get_queryset(self):
        group_id = self.request.query_params.get("group_id")
        if group_id:
            group = get_object_or_404(Group, pk=group_id)
            return Expense.objects.filter(group=group)

        return Expense.objects.all()


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
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


class DebtView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DebtSerializer

    def get_queryset(self):
        group_id = self.request.query_params.get("group_id")
        if group_id:
            group = get_object_or_404(Group, pk=group_id)
            return Debt.objects.filter(group=group)

        return Debt.objects.all()


################################################################################
# Balance


class BalanceView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Balance.objects.all()
    serializer_class = BalanceSerializer

    def get_queryset(self):
        group_id = self.request.query_params.get("group_id")
        if group_id:
            group = get_object_or_404(Group, pk=group_id)
            return Balance.objects.filter(group=group)

        return Balance.objects.all()


################################################################################
# Logout


class LogoutView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "logout.html"

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        return Response({"refresh_token": ""})
