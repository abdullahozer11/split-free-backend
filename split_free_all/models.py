# Copyright (c) 2023 SplitFree Org.

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

CURRENCY_CHOICES = [
    ("EUR", "Euro"),
    ("USD", "US Dollar"),
    ("GBP", "British Pound"),
    ("TRY", "Turkish lira"),
]


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=32, null=True)
    email = models.EmailField(
        unique=True, max_length=128, default="example@hotmail.com"
    )
    password = models.CharField(max_length=32, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    objects = UserManager()

    def __str__(self):
        return f'User("{self.email}")'


class Member(models.Model):
    name = models.CharField(max_length=255)
    group = models.ForeignKey("Group", on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'Member("{self.name}")'

    class Meta:
        # Ensure that the combination of 'name' and 'group' is unique
        unique_together = ["name", "group"]


class Group(models.Model):
    title = models.CharField(max_length=255, default=None)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'Group("{self.title}")'


class Balance(models.Model):
    owner = models.OneToOneField(
        Member, blank=True, null=True, on_delete=models.CASCADE
    )
    currency = models.CharField(max_length=4, choices=CURRENCY_CHOICES, default="EUR")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f'Owner("{self.owner.name}"): {self.amount}'


class Expense(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    title = models.CharField(max_length=255, default=None)
    description = models.TextField()
    currency = models.CharField(max_length=4, choices=CURRENCY_CHOICES, default="EUR")
    payer = models.ForeignKey(
        Member, on_delete=models.SET_NULL, null=True, blank=True, related_name="payer"
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    date = models.CharField(max_length=30, default="")
    participants = models.ManyToManyField(Member, related_name="participants")

    def __str__(self):
        return f'Expense("{self.title}") - Amount: {self.amount}'


class Debt(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=4, choices=CURRENCY_CHOICES, default="EUR")
    borrower = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="borrower"
    )
    lender = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="lender")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)

    def __str__(self):
        return f"Debt({self.borrower.name} to {self.lender.name}): {self.amount}"
