# Copyright (c) 2023 SplitFree Org.
# urls.py

from django.urls import path

from split_free_all.views import (
    DebtListView,
    ExpenseDetail,
    ExpenseList,
    GroupDetail,
    GroupList,
    UserDetail,
    UserList,
)

urlpatterns = [
    path("debts/", DebtListView.as_view(), name="debt-list"),
    path("users/", UserList.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetail.as_view(), name="user-detail"),
    path("groups/", GroupList.as_view(), name="group-list"),
    path("groups/<int:pk>/", GroupDetail.as_view(), name="group-detail"),
    path("expenses/", ExpenseList.as_view(), name="expense-list"),
    path("expenses/<int:pk>/", ExpenseDetail.as_view(), name="expense-detail"),
]
