# Copyright (c) 2023 SplitFree Org.

from django.db import models


class User(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f'User("{self.name}")'


class Event(models.Model):
    title = models.CharField(max_length=255, default=None)
    description = models.TextField()
    users = models.ManyToManyField(User)

    def __str__(self):
        return f'Event("{self.title}")'


class UserEventDebt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    debt_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f'User("{self.user.name}"): {self.debt_balance}'


class Expense(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    title = models.CharField(max_length=255, default=None)
    description = models.TextField()
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payer")
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    users = models.ManyToManyField(User, related_name="users")

    def __str__(self):
        return f'Expense("{self.title}") - Amount: {self.amount}'


class IdealTransfer(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="receiver"
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):
        return f"Transfer({self.sender.name} to {self.receiver.name}): {self.amount}"
