# Copyright (c) 2023 SplitFree Org.
from datetime import timedelta

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
    Activity,
    Balance,
    Debt,
    Expense,
    Group,
    InviteToken,
    Member,
    User,
)
from split_free_all.serializers import (
    ActivitySerializer,
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
    member_deleted,
)

################################################################################
# CustomPermission


class OnlyAdminPermissionExceptPost(BasePermission):
    def has_permission(self, request, view):
        # Allow POST request without authentication
        if request.method == "POST":
            return True
        # Require authentication for other methods
        return (
            request.user and request.user.is_authenticated and request.user.is_superuser
        )


################################################################################
# User


@permission_classes([OnlyAdminPermissionExceptPost])
class UserView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        # Save the user
        user = serializer.save()

        # Get tokens
        refresh = RefreshToken.for_user(user)

        if user.is_anonymous:
            refresh.set_exp(lifetime=timedelta(days=99999))

        # Build the response data
        response_data = {
            "id": str(user.id),
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        # Set the response status and data
        self.response_status = status.HTTP_201_CREATED
        self.response_data = response_data

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                self.response_data, status=self.response_status, headers=headers
            )
        except Exception as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserInfoView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        name = request.user.name
        return Response(
            {"name": name, "id": request.user.id}, status=status.HTTP_200_OK
        )

    def post(self, request):
        new_name = request.data.get("name")
        if not new_name:
            return Response(
                {"error": "name is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        user = request.user
        user.name = new_name
        user.save()
        return Response(status=status.HTTP_200_OK)


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

    def perform_create(self, serializer):
        serializer.save()

        Balance.objects.create(
            owner=serializer.instance, group=serializer.instance.group, amount=0.00
        )

        Activity.objects.create(
            user=self.request.user,
            text=f'{self.request.user.name} added member "{serializer.instance.name}" to group "{serializer.instance.group.title}"',
            group=serializer.instance.group,
        )


class MemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MemberSerializer

    def get_queryset(self):
        return Member.objects.filter(group__users=self.request.user)

    def perform_destroy(self, instance):
        # Trigger the custom signal
        member_deleted.send(
            sender=self.__class__,
            instance=instance,
        )

        Activity.objects.create(
            user=self.request.user,
            text=f'{self.request.user.name} removed member "{instance.name}" from group "{instance.group.title}"',
            group=instance.group,
        )

        instance.delete()


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

        Activity.objects.create(
            user=self.request.user,
            text=f'{self.request.user.name} created group "{serializer.instance.title}"',
            group=serializer.instance,
        )

        for member_name in member_names:
            Activity.objects.create(
                user=self.request.user,
                text=f'{self.request.user.name} added member "{member_name}" to group "{serializer.instance.title}"',
                group=serializer.instance,
            )


class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = GroupSerializer

    def get_queryset(self):
        return Group.objects.filter(users=self.request.user)

    def perform_update(self, serializer):
        # Get the current instance before the update
        old_instance = Group.objects.get(pk=serializer.instance.pk)

        # Perform the update
        serializer.save()

        # Compare the old and new titles
        if old_instance.title != serializer.instance.title:
            Activity.objects.create(
                user=self.request.user,
                text=f'{self.request.user.name} changed group title from "{old_instance.title}" to "{serializer.instance.title}"',
                group=serializer.instance,
            )

        # Compare the old and new descriptions
        if old_instance.description != serializer.instance.description:
            Activity.objects.create(
                user=self.request.user,
                text=f'{self.request.user.name} changed group description from "{old_instance.description}" to "{serializer.instance.description}"',
                group=serializer.instance,
            )

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

        Activity.objects.create(
            user=self.request.user,
            text=f'{self.request.user.name} added an expense "{serializer.instance.title}" of amount {serializer.instance.amount}'
            f' {serializer.instance.currency} to group "{serializer.instance.group.title}"',
            group=serializer.instance.group,
        )


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView, BaseExpenseView):
    def perform_update(self, serializer):
        instance = self.get_object()
        old_participants = instance._participants()
        old_expense_info = model_to_dict(instance)
        serializer.save()
        new_expense_info = model_to_dict(serializer.instance)

        keys = [
            "amount",
            "title",
            "description",
            "currency",
            "date",
            "payer",
            "participants",
        ]

        for key in keys:
            if old_expense_info[key] != new_expense_info[key]:
                log = f"{self.request.user.name} changed "
                if key == "amount":
                    log += f'expense "{instance.title}" amount from {instance.amount} to {serializer.instance.amount}'
                elif key == "payer":
                    log += f'expense "{instance.title}" payer from "{instance.payer.name}" to "{serializer.instance.payer.name}"'
                elif key == "participants":
                    log += f'expense "{instance.title}" participants from "{old_participants}" to "{serializer.instance._participants()}"'
                else:
                    log += f'expense "{instance.title}" {key} from "{old_expense_info[key]}" to "{new_expense_info[key]}"'
                Activity.objects.create(
                    user=self.request.user,
                    text=log,
                    group=serializer.instance.group,
                )

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

        Activity.objects.create(
            user=self.request.user,
            text=f'{self.request.user.name} deleted expense "{instance.title}"',
            group=instance.group,
        )

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
        Activity.objects.create(
            user=self.request.user,
            text=f'New user has joined to group "{group.title}"',
            group=group,
        )
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


################################################################################
# Invite User to Group


class ActivityView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
