from django.db import models


class User(models.Model):
    name = models.CharField(max_length=255)


class Event(models.Model):
    title = models.CharField(max_length=255, default=None)
    description = models.TextField()
    users = models.ManyToManyField(User)


class UserEventDebt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    debt_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)


class Expense(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    title = models.CharField(max_length=255, default=None)
    description = models.TextField()
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payer")
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    users = models.ManyToManyField(User, related_name="users")
