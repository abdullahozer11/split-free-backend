# Copyright (c) 2023 SplitFree Org.
# serializers.py

from rest_framework import serializers

from split_free_all.models import Balance, Debt, Expense, Group, Member, User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, required=True
    )

    class Meta:
        model = User
        fields = ["email", "password"]

    def validate(self, data):
        if "password" not in data:
            raise serializers.ValidationError({"password": "This field is required."})
        if "email" not in data:
            raise serializers.ValidationError({"email": "This field is required."})
        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                {"email": "A user with that email already exists."}
            )
        if len(data["password"]) < 8:
            raise serializers.ValidationError(
                {
                    "password": "This password is too short. It must contain at least 8 characters."
                }
            )
        return data

    def create(self, validated_data):
        user = User(email=validated_data["email"])
        user.set_password(validated_data["password"])
        user.save()
        return user


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = "__all__"


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"

    def create(self, validated_data):
        user = self.context["request"].user

        group = Group(
            title=validated_data["title"],
            description=validated_data["description"],
            creator=user,
        )
        group.save()
        group.users.add(user)
        return group


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = "__all__"


class DebtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debt
        fields = "__all__"


class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Balance
        fields = "__all__"
