# Copyright (c) 2023 SplitFree Org.

from django.contrib import admin

# Register your models here.
from split_free_all.models import Balance, Expense, Group, Member, User

admin.site.register(User)
admin.site.register(Member)
admin.site.register(Group)
admin.site.register(Balance)
admin.site.register(Expense)
