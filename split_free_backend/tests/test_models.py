# Copyright (c) 2023 SplitFree Org.

from django.db import IntegrityError
from django.test import TestCase

from split_free_backend.core.models import Group, Member


class MemberModelTest(TestCase):
    def setUp(self):
        # Create a group
        self.group = Group.objects.create(title="Test Group", description="Test description")

    def test_unique_member_name_within_group(self):
        # Create two members with the same name within the same group
        Member.objects.create(name="Alice", group=self.group)

        with self.assertRaises(IntegrityError):
            Member.objects.create(name="Alice", group=self.group)

    def test_unique_member_name_across_groups(self):
        # Create members with the same name but in different groups
        Member.objects.create(name="Bob", group=self.group)

        # Create another group
        another_group = Group.objects.create(title="Another Group", description="Another description")

        # Creating a member with the same name in a different group should be allowed
        member2 = Member.objects.create(name="Bob", group=another_group)

        # No exception should be raised
        member2.full_clean()
