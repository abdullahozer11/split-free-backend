# Copyright (c) 2023 SplitFree Org.
import uuid

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from split_free_backend.core.helpers import generate_hash

CURRENCY_CHOICES = [
    ("EUR", "Euro"),
    ("USD", "US Dollar"),
    ("GBP", "British Pound"),
    ("TRY", "Turkish lira"),
]


class UserManager(BaseUserManager):
    def create_user(self, email=None, password=None, **extra_fields):
        # in case entry is for anon user lets not make email or password required
        if email is None and password is None:
            user = self.model(**extra_fields)
            user.set_unusable_password()
            user.is_anonymous = True
            user.is_active = True
        else:
            if not email:
                raise ValueError("The Email field must be set")
            if not password:
                raise ValueError("The Password field must be set")
            user = self.model(email=email, **extra_fields)
            user.set_password(password)
            user.is_anonymous = False

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=128, null=True)
    email = models.EmailField(unique=True, max_length=128)
    password = models.CharField(max_length=128, null=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=False)
    activation_token = models.CharField(max_length=128, null=True, blank=True)

    USERNAME_FIELD = "email"
    objects = UserManager()

    def __str__(self):
        if self.is_anonymous:
            return f'AnonUser("{self.id}")'
        else:
            return f'User("{self.email}")'

    def save(self, *args, **kwargs):
        if self.is_anonymous:
            if self.email == "" or not self.email:
                # Set a unique email for anonymous users with null email
                self.email = f"anon_{uuid.uuid4()}@example.com"
                self.is_active = True

        if settings.NEW_USERS_ACTIVE:
            self.is_active = True

        if not self.activation_token and not self.is_anonymous:
            self.activation_token = str(uuid.uuid4())

        super().save(*args, **kwargs)


class Member(models.Model):
    name = models.CharField(max_length=255)
    group = models.ForeignKey("Group", on_delete=models.CASCADE, null=True, related_name="members")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'Member("{self.name}")'

    class Meta:
        # Ensure that the combination of 'name' and 'group' is unique
        unique_together = ["name", "group"]


class Group(models.Model):
    title = models.CharField(max_length=255, default=None)
    description = models.TextField(null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    users = models.ManyToManyField(User, null=True, related_name="expense_groups")

    def __str__(self):
        return f'Group("{self.title}")'


class Balance(models.Model):
    owner = models.OneToOneField(Member, blank=True, null=True, on_delete=models.CASCADE)
    currency = models.CharField(max_length=4, choices=CURRENCY_CHOICES, default="EUR")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f'Owner("{self.owner.name}"): {self.amount}'


class Expense(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    title = models.CharField(max_length=255, default=None)
    description = models.TextField(null=True, blank=True)
    currency = models.CharField(max_length=4, choices=CURRENCY_CHOICES, default="EUR")
    payer = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payed_expenses",
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    date = models.CharField(max_length=240, default="")
    participants = models.ManyToManyField(Member, related_name="participated_expenses")

    def __str__(self):
        return f'Expense("{self.title}") - Amount: {self.amount}'

    def _participants(self):
        participants_names = [par.name for par in self.participants.all()]
        if not participants_names:
            return ""
        if len(participants_names) == 1:
            return participants_names[0]
        participants_str = ", ".join(participants_names[:-1])
        participants_str += f" and {participants_names[-1]}"
        return participants_str


class Debt(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=4, choices=CURRENCY_CHOICES, default="EUR")
    borrower = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="debts_borrowed")
    lender = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="debts_lent")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)

    def __str__(self):
        return f"Debt({self.borrower.name} to {self.lender.name}): {self.amount}"


class InviteToken(models.Model):
    token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)

    def __str__(self):
        return f"Token for {self.group.title}"

    class Meta:
        unique_together = ["token", "group"]

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = generate_hash()
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=1)
        return super().save(*args, **kwargs)

    def is_expired(self):
        return self.expires_at is not None and self.expires_at < timezone.now()


class Activity(models.Model):
    text = models.CharField(max_length=256)
    date = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Activity: {self.text}"
