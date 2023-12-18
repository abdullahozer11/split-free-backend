# Copyright (c) 2023 SplitFree Org.
# urls.py

from django.urls import path

from split_free_all.views import (
    EventDetail,
    EventList,
    ExpenseDetail,
    ExpenseList,
    UserDetail,
    UserList,
)

urlpatterns = [
    path("users/", UserList.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetail.as_view(), name="user-detail"),
    path("events/", EventList.as_view(), name="event-list"),
    path("events/<int:pk>/", EventDetail.as_view(), name="event-detail"),
    path("expenses/", ExpenseList.as_view(), name="expense-list"),
    path("expenses/<int:pk>/", ExpenseDetail.as_view(), name="expense-detail"),
]
