# Copyright (c) 2023 SplitFree Org.

from django.contrib import admin

# Register your models here.
from split_free_backend.core.models import (
    Activity,
    Balance,
    Expense,
    Group,
    Member,
    User,
)

admin.site.register(User)
admin.site.register(Member)
admin.site.register(Group)
admin.site.register(Balance)
admin.site.register(Expense)
admin.site.register(Activity)
