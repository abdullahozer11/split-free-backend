# Copyright (c) 2023 SplitFree Org.
# serializers.py

from rest_framework import serializers

from split_free_all.models import Debt, Expense, Group, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"

    def create(self, validated_data):
        member_ids = validated_data.pop("members", None)
        group = Group.objects.create(**validated_data)
        group.members = []
        for id in member_ids:
            member = User.objects.get(pk=id)
            group.members.append(member)
        group.save()
        return group


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = "__all__"

    def create(self, validated_data):
        group_id = validated_data.pop("group_id", None)
        expense = Expense.objects.create(**validated_data)

        if group_id:
            group = Group.objects.get(pk=group_id)
            expense.group = group
            expense.save()

        return expense


class DebtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debt
        fields = "__all__"
