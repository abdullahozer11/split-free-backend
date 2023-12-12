# urls.py
from django.urls import path
from .views import (
    UserList,
    UserDetail,
    EventList,
    EventDetail,
    ExpenseList,
    ExpenseDetail,
    UserEventDebtList,
    UserEventDebtDetail,
)

urlpatterns = [
    path("users/", UserList.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetail.as_view(), name="user-detail"),
    path("events/", EventList.as_view(), name="event-list"),
    path("events/<int:pk>/", EventDetail.as_view(), name="event-detail"),
    path("expenses/", ExpenseList.as_view(), name="expense-list"),
    path("expenses/<int:pk>/", ExpenseDetail.as_view(), name="expense-detail"),
]
