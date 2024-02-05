# Copyright (c) 2023 SplitFree Org.

from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import permission_classes
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from split_free_all.models import (
    Balance,
    Debt,
    Expense,
    Group,
    InviteToken,
    Member,
    User,
)
from split_free_all.serializers import (
    BalanceSerializer,
    DebtSerializer,
    ExpenseSerializer,
    GroupSerializer,
    InviteTokenSerializer,
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
# CustomPermission


class CustomPermission(BasePermission):
    def has_permission(self, request, view):
        # Allow GET request without authentication
        if request.method == "POST":
            return True
        # Require authentication for other methods
        return (
            request.user and request.user.is_authenticated and request.user.is_superuser
        )


################################################################################
# User


@permission_classes([CustomPermission])
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
        query1 = Member.objects.filter(group__users=self.request.user)
        group_id = self.request.query_params.get("group_id", None)
        if group_id is not None:
            query2 = query1.filter(group__id=group_id)
            return query2

        return query1


class MemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MemberSerializer

    def get_queryset(self):
        return Member.objects.filter(group__users=self.request.user)


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
    serializer_class = GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(users=self.request.user)

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


class BaseExpenseView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        user_expenses = Expense.objects.filter(group__users=self.request.user)
        group_id = self.request.query_params.get("group_id")

        if group_id:
            group_expenses = user_expenses.filter(group=group_id)
            return group_expenses

        return user_expenses


class ExpenseView(generics.ListCreateAPIView, BaseExpenseView):
    def perform_create(self, serializer):
        serializer.save()

        # Trigger the custom signal
        expense_created.send(sender=self.__class__, instance=serializer.instance)


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView, BaseExpenseView):
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
        query1 = Debt.objects.filter(group__users=self.request.user)
        group_id = self.request.query_params.get("group_id", None)

        if group_id is not None:
            query2 = query1.filter(group__id=group_id)
            return query2

        return query1


################################################################################
# Balance


class BalanceView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BalanceSerializer

    def get_queryset(self):
        query1 = Balance.objects.filter(group__users=self.request.user)
        group_id = self.request.query_params.get("group_id", None)

        if group_id is not None:
            query2 = query1.filter(group__id=group_id)
            return query2

        return query1


################################################################################
# Logout


class LogoutView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "logout.html"

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "Token is blacklisted"}, status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"detail": "Token is invalid or expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get(self, request):
        return Response({"refresh_token": ""})


################################################################################
# Delete User


class DeleteUserView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        user.delete()
        return Response(status=status.HTTP_200_OK)


################################################################################
# Invite User to Group


class AcceptInviteView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        hash = request.data.get("invite_token")
        token = get_object_or_404(InviteToken, hash=hash)
        if token.is_expired():
            return Response(
                {"detail": "Invite token is expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        group = token.group
        group.users.add(request.user)
        token.delete()
        return Response(status=status.HTTP_200_OK)


class InviteGenerateView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = InviteTokenSerializer

    def post(self, request):
        group_id = request.data.get("group_id")
        if not group_id:
            return Response(
                {"detail": "Group id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        group = Group.objects.get(id=group_id)
        if not group:
            return Response(
                {"detail": "Group not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token = InviteToken.objects.create(group=group)
        if not token:
            return Response(
                {"detail": "Error with token creation"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token.save()
        return Response({"invite_token": token.hash}, status=status.HTTP_201_CREATED)
