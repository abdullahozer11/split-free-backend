# Copyright (c) 2023 SplitFree Org.

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from split_free_all.helpers import get_auth_headers
from split_free_all.models import Group, Member, User


class AnonUserTests(TestCase):
    def test_anon_user_can_register(self):
        url = reverse("user-list")
        response = self.client.post(url, {"is_anonymous": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue("access" in response.data)
        self.assertTrue("refresh" in response.data)

    def test_anon_user_can_fetch_data(self):
        anon_user = User.objects.create(email=None, password=None, is_anonymous=True)
        refresh = RefreshToken.for_user(anon_user)
        access_token = str(refresh.access_token)

        group = Group.objects.create(title="Test Group")
        group.users.add(anon_user)
        group.save()

        url = reverse("group-list")
        response = self.client.get(
            url, format="json", headers=get_auth_headers(access_token)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Test Group")

    def test_anon_user_cannot_fetch_data(self):
        url = reverse("group-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Authentication credentials were not provided."
        )

    def test_delete_anon_user(self):
        anon_user = User.objects.create(email=None, password=None, is_anonymous=True)
        refresh = RefreshToken.for_user(anon_user)
        access_token = str(refresh.access_token)

        url = reverse("user-info")

        id_response = self.client.get(
            url,
            format="json",
            headers=get_auth_headers(access_token),
        )

        response = self.client.delete(
            f"/api/users/{id_response.data['id']}/",
            {id: id_response.data["id"]},
            headers=get_auth_headers(access_token),
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(User.objects.count(), 0)

    def test_anon_user_can_create_group(self):
        url = reverse("user-list")
        response = self.client.post(url, {"is_anonymous": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue("access" in response.data)
        self.assertTrue("refresh" in response.data)
        access_token = response.data["access"]

        url = reverse("group-list")
        response = self.client.post(
            url,
            {"title": "Test Group"},
            format="json",
            headers=get_auth_headers(access_token),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Group.objects.count(), 1)
        self.assertEqual(Group.objects.get().title, "Test Group")

    def test_anon_user_can_attach_to_group_member(self):
        anon_user = User.objects.create(
            email=None, password=None, is_anonymous=True, is_active=True
        )
        member1 = Member.objects.create(name="Alice")
        member2 = Member.objects.create(name="Bob")

        group = Group.objects.create(title="Test Group")
        group.members.add(member1)
        group.members.add(member2)
        group.users.add(anon_user)
        group.save()

        refresh = RefreshToken.for_user(anon_user)
        access_token = str(refresh.access_token)

        response = self.client.put(
            f"/api/members/{member1.id}/",
            {"name": "Alice", "group": group.id, "user": anon_user.id},
            content_type="application/json",
            format="json",
            headers=get_auth_headers(access_token),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Member.objects.get(id=member1.id).user, anon_user)
        self.assertEqual(Member.objects.get(id=member2.id).user, None)

    def test_anon_user_is_created_active_by_default(self):
        url = reverse("user-list")
        response = self.client.post(url, {"is_anonymous": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get().is_active, True)
