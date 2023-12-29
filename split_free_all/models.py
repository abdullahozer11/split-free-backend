# Copyright (c) 2023 SplitFree Org.

from django.db import models


class User(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f'User("{self.name}")'


class Group(models.Model):
    title = models.CharField(max_length=255, default=None)
    description = models.TextField()
    members = models.ManyToManyField(User)

    def __str__(self):
        return f'Group("{self.title}")'


class Balance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f'User("{self.user.name}"): {self.amount} in {self.group.title}'


class Expense(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    title = models.CharField(max_length=255, default=None)
    description = models.TextField()
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payer")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)
    participants = models.ManyToManyField(User, related_name="participants")

    def __str__(self):
        return f'Expense("{self.title}") - Amount: {self.amount}'


class Debt(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    borrower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="borrower"
    )
    lender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lender")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, default=None)

    def __str__(self):
        return f"Debt({self.borrower.name} to {self.lender.name}): {self.amount}"
