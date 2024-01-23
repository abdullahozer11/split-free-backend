# Copyright (c) 2023 SplitFree Org.

from django.db.models.signals import post_save
from django.test import TestCase, override_settings

from split_free_all.models import Balance, Debt, Expense, Group, Member
from split_free_all.signals import handle_group_created


class GroupSignalTests(TestCase):
    @override_settings(USE_TZ=False)  # Override settings to avoid issues with signals
    def setUp(self):
        # Disconnect the signal before the test starts
        post_save.disconnect(handle_group_created, sender=Group)

    @override_settings(USE_TZ=False)  # Override settings to avoid issues with signals
    def tearDown(self):
        # Reconnect the signal after the test is finished
        post_save.connect(handle_group_created, sender=Group)

    def test_handle_group_created_signal(self):
        ### Setup
        # Create three members
        member1 = Member.objects.create(name="Apo")
        member2 = Member.objects.create(name="Michael")
        member3 = Member.objects.create(name="Jeremy")

        ### Action
        # Create a group with these members
        data = {
            "title": "Birthday Party",
            "description": "A celebration",
            "members": [member1.id, member2.id, member3.id],
        }
        response = self.client.post("/api/groups/", data)

        ### Checks
        # Check that Balance objects were created (thanks to the signal)
        group_id = response.data["id"]
        group = Group.objects.get(id=group_id)
        balances = Balance.objects.filter(group=group)
        self.assertEqual(balances.count(), 3)

        # Check that the balance is set to 0.0 for each member
        for member in [member1, member2, member3]:
            balance = Balance.objects.get(owner=member)
            self.assertEqual(balance.amount, 0.0)

    def create_basic_group(self):
        # Create members
        self.members = [
            Member.objects.create(name="Apo"),
            Member.objects.create(name="Michael"),
            Member.objects.create(name="Jake"),
            Member.objects.create(name="John"),
        ]
        # Create an group with these members
        self.group = Group.objects.create(
            title="Day of eating",
            description="Breakfast, lunch and dinner",
        )
        # Add the created members to the group
        self.group.members.set(self.members)
        # Create the debt with a balance of 0.00 as it would be with the
        # creation of the group
        for member in self.members:
            Balance.objects.create(owner=member, group=self.group, amount=0.00)

        # Create expenses with these members within this group
        self.expenses = [
            Expense.objects.create(
                amount=10.00,
                title="Breakfast",
                description="Expense for breakfast",
                group=self.group,
                payer=self.members[0],
            ),
            Expense.objects.create(
                amount=20.00,
                title="Lunch",
                description="Expense for lunch",
                group=self.group,
                payer=self.members[1],
            ),
            Expense.objects.create(
                amount=40.00,
                title="Dinner",
                description="Expense for dinner",
                group=self.group,
                payer=self.members[2],
            ),
        ]
        # Involve all members in all expenses
        for expense in self.expenses:
            expense.participants.set(self.members)

        # Update the associated debts that are usually updated with the creation
        # of the expense
        # Member 1: -7.50 + 5 + 10 = 7.50
        debt_member1 = Balance.objects.get(owner=self.members[0], group=self.group)
        debt_member1.amount = 7.50
        debt_member1.save()

        # Member 2: 2.50 - 15 + 10 = -2.50
        debt_member2 = Balance.objects.get(owner=self.members[1], group=self.group)
        debt_member2.amount = -2.50
        debt_member2.save()

        # Member 3: 2.50 + 5 - 30 = -22.50
        debt_member3 = Balance.objects.get(owner=self.members[2], group=self.group)
        debt_member3.amount = -22.50
        debt_member3.save()

        # Member 4: 2.50 + 5 + 10 = 17.50
        debt_member4 = Balance.objects.get(owner=self.members[3], group=self.group)
        debt_member4.amount = 17.50
        debt_member4.save()

    def test_handle_group_destroyed_signal(self):
        ### Setup
        self.create_basic_group()

        ### Action
        self.client.delete(f"/api/groups/{self.group.id}/")

        ### Checks
        # This is the result of cascade deletion cause there is no signals but
        # it's left here, we never know if we add some signals one day
        self.assertEqual(Expense.objects.filter(group=self.group).count(), 0)
        self.assertEqual(Balance.objects.filter(group=self.group).count(), 0)
        self.assertEqual(Debt.objects.filter(group=self.group).count(), 0)

    def test_handle_group_updated_signal_added_members(self):
        ### Setup
        self.create_basic_group()

        # Create new members
        new_members = [
            Member.objects.create(name="Sarah"),
            Member.objects.create(name="Sophie"),
        ]
        self.members.extend(new_members)

        ### Action
        # Update the group by adding them as new members
        new_group_data = {
            "title": "Day of eating",
            "description": "Breakfast, lunch and dinner",
            "members": [member.id for member in self.members],
        }
        self.client.put(
            f"/api/groups/{self.group.id}/",
            new_group_data,
            content_type="application/json",
        )

        ### Checks
        self.assertEqual(Group.objects.get(pk=self.group.id).members.count(), 6)
        self.assertEqual(Balance.objects.filter(group=self.group).count(), 6)
        for member in new_members:
            self.assertEqual(
                Balance.objects.get(group=self.group, owner=member).amount, 0.00
            )

    def test_handle_group_updated_signal_removed_members(self):
        self.create_basic_group()

        # Remove the last two members of the group
        new_group_data = {
            "title": "Day of eating",
            "description": "Breakfast, lunch and dinner",
            "members": [member.id for member in self.members[:-2]],
        }
        self.client.put(
            f"/api/groups/{self.group.id}/",
            new_group_data,
            content_type="application/json",
        )

        # Check the group
        self.assertEqual(Group.objects.get(pk=self.group.id).members.count(), 2)

        # Check the expenses
        for expense in self.expenses:
            self.assertEqual(expense.participants.count(), 2)

        # Check the balances
        self.assertEqual(Balance.objects.filter(group=self.group).count(), 2)
        # The last balance was paid for by the last member who withdrew so there
        # is nothing to pay back for this one
        # Member 1: -5 + 10 = 5
        self.assertEqual(
            Balance.objects.get(owner=self.members[0], group=self.group).amount,
            5.00,
        )
        # Member 1: 5 - 10 = -5
        self.assertEqual(
            Balance.objects.get(owner=self.members[1], group=self.group).amount,
            -5.00,
        )


class ExpenseSignalTests(TestCase):
    @override_settings(USE_TZ=False)  # Override settings to avoid issues with signals
    def setUp(self):
        # Disconnect the signal before the test starts
        post_save.disconnect(handle_group_created, sender=Group)

    @override_settings(USE_TZ=False)  # Override settings to avoid issues with signals
    def tearDown(self):
        # Reconnect the signal after the test is finished
        post_save.connect(handle_group_created, sender=Group)

    def test_handle_expense_created_signal_payer_is_participant(self):
        ### Setup
        # Create three members
        members = [
            Member.objects.create(name="Apo"),
            Member.objects.create(name="Michael"),
            Member.objects.create(name="Jeremy"),
        ]

        # Create a group and add the members to it
        group = Group.objects.create(title="Holidays", description="Great holidays")
        group.members.set(members)

        # Create balances with an amount of 0
        for member in members:
            Balance.objects.create(owner=member, group=group, amount=0.00)

        ### Action
        # Create an expense with these members
        expense_data = {
            "amount": 60.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": members[1].id,
            "group": group.id,
            "participants": [member.id for member in members],
        }
        self.client.post("/api/expenses/", expense_data)

        ###Checks
        # Check the balance of each member
        self.assertEqual(
            Balance.objects.get(group=group, owner=members[0]).amount,
            20.00,
        )
        self.assertEqual(
            Balance.objects.get(group=group, owner=members[1]).amount,
            -40.00,
        )
        self.assertEqual(
            Balance.objects.get(group=group, owner=members[2]).amount,
            20.00,
        )

        # Check that 2 debts are created
        self.assertEqual(Debt.objects.filter(group=group).count(), 2)

    def test_handle_expense_created_signal_payer_is_not_participant(self):
        ### Setup
        # Create three members
        members = [
            Member.objects.create(name="Apo"),
            Member.objects.create(name="Michael"),
            Member.objects.create(name="Jeremy"),
        ]

        # Create a group and add the members to it
        group = Group.objects.create(title="Holidays", description="Great holidays")
        group.members.set(members)

        # Create balances with an amount of 0
        for member in members:
            Balance.objects.create(owner=member, group=group, amount=0.00)

        ### Action
        # Create an expense with whose participants are only the first and
        # second members but whose payer is the third member
        expense_data = {
            "amount": 60.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "date": "2024-01-24 16:38",
            "payer": members[2].id,
            "group": group.id,
            "participants": [members[0].id, members[1].id],
        }
        self.client.post("/api/expenses/", expense_data)

        ### Checks
        # Check the balance of each member
        self.assertEqual(
            Balance.objects.get(group=group, owner=members[0]).amount,
            30.00,
        )
        self.assertEqual(
            Balance.objects.get(group=group, owner=members[1]).amount,
            30.00,
        )
        self.assertEqual(
            Balance.objects.get(group=group, owner=members[2]).amount,
            -60.00,
        )

        # Check that 2 debts are created
        self.assertEqual(Debt.objects.filter(group=group).count(), 2)

    def create_basic_expense(self):
        # Create members
        self.members = [
            Member.objects.create(name="Apo"),
            Member.objects.create(name="Michael"),
            Member.objects.create(name="Jake"),
        ]
        # Create an group with these members
        self.group = Group.objects.create(
            title="Holidays",
            description="Great holidays",
        )
        # Add the created members to the group
        self.group.members.set(self.members)
        # Create the balances with an amount of 0.00 as it would be with the
        # creation of the group
        for member in self.members:
            Balance.objects.create(owner=member, group=self.group, amount=0.00)

        # Create an expense with these members within this group
        self.expense = Expense.objects.create(
            amount=60.00,
            title="Dinner",
            description="Expense for dinner",
            group=self.group,
            payer=self.members[0],
        )
        # Add the created members to the expense
        self.expense.participants.set(self.members)
        # Update the associated balances that are usually updated with the
        # creation of the expense
        debt_member1 = Balance.objects.get(owner=self.members[0], group=self.group)
        debt_member1.amount = -40.00
        debt_member1.save()

        debt_member2 = Balance.objects.get(owner=self.members[1], group=self.group)
        debt_member2.amount = 20.00
        debt_member2.save()

        debt_member3 = Balance.objects.get(owner=self.members[2], group=self.group)
        debt_member3.amount = 20.00
        debt_member3.save()

    def test_handle_expense_updated_signal_added_members(self):
        ### Setup
        self.create_basic_expense()

        # Create two new members their debts
        new_members = [
            Member.objects.create(name="Maxim"),
            Member.objects.create(name="Clement"),
        ]
        self.members.extend(new_members)
        for member in new_members:
            Balance.objects.create(owner=member, group=self.group, amount=0.00)
        # Add the members to the group
        self.group.members.add(*new_members)

        ### Action
        # Update the expense by adding two members
        new_expense_data = {
            "amount": 60.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": self.members[0].id,
            "group": self.group.id,
            # Only this changes as there are now 4 members
            "participants": [member.id for member in self.members],
        }
        self.client.put(
            f"/api/expenses/{self.expense.id}/",
            new_expense_data,
            content_type="application/json",
        )

        ### Checks
        self.assertEqual(self.expense.participants.count(), 5)
        self.assertEqual(Balance.objects.filter(group=self.group).count(), 5)

        for member_index, member in enumerate(self.members):
            balance = -48.00 if member_index == 0 else 12.00
            self.assertEqual(
                Balance.objects.get(owner=member, group=self.group).amount,
                balance,
            )

        self.assertEqual(Debt.objects.filter(group=self.group).count(), 4)

    def test_handle_expense_updated_signal_removed_members(self):
        ### Setup
        self.create_basic_expense()

        ### Action
        new_expense_data = {
            "amount": 60.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": self.members[0].id,
            "group": self.group.id,
            # We remove the last member, they are only two now
            "participants": [member.id for member in self.members[:-1]],
        }
        self.client.put(
            f"/api/expenses/{self.expense.id}/",
            new_expense_data,
            content_type="application/json",
        )

        ### Checks
        self.assertEqual(self.expense.participants.count(), 2)

        expected_debts = [-30.00, 30.00, 0.00]
        for member_index, member in enumerate(self.members):
            self.assertEqual(
                Balance.objects.get(owner=member, group=self.group).amount,
                expected_debts[member_index],
            )

        self.assertEqual(Debt.objects.filter(group=self.group).count(), 1)

    def test_handle_expense_updated_signal_new_amount(self):
        ### Setup
        self.create_basic_expense()

        ### Action
        new_expense_data = {
            # The amount has changed from 60.00 to 90.00
            "amount": 90.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            "payer": self.members[0].id,
            "group": self.group.id,
            "participants": [member.id for member in self.members],
        }
        self.client.put(
            f"/api/expenses/{self.expense.id}/",
            new_expense_data,
            content_type="application/json",
        )

        ### Checks
        expected_debts = [-60.00, 30.00, 30.00]
        for member_index, member in enumerate(self.members):
            self.assertEqual(
                Balance.objects.get(owner=member, group=self.group).amount,
                expected_debts[member_index],
            )

        self.assertEqual(Debt.objects.filter(group=self.group).count(), 2)

    def test_handle_expense_updated_signal_changed_payer(self):
        ### Setup
        self.create_basic_expense()

        ### Action
        new_expense_data = {
            "amount": 60.00,
            "title": "Dinner",
            "description": "Expense for dinner",
            # The payer is not the first but the last member now
            "payer": self.members[-1].id,
            "group": self.group.id,
            "participants": [member.id for member in self.members],
        }
        self.client.put(
            f"/api/expenses/{self.expense.id}/",
            new_expense_data,
            content_type="application/json",
        )

        ### Checks
        expected_debts = [20.00, 20.00, -40.00]
        for member_index, member in enumerate(self.members):
            self.assertEqual(
                Balance.objects.get(owner=member, group=self.group).amount,
                expected_debts[member_index],
            )

        self.assertEqual(Debt.objects.filter(group=self.group).count(), 2)

    def test_handle_expense_destroyed(self):
        ### Setup
        self.create_basic_expense()

        ### Action
        self.client.delete(f"/api/expenses/{self.expense.id}/")

        ### Checks
        for member in self.members:
            self.assertEqual(
                Balance.objects.get(owner=member, group=self.group).amount,
                0.00,
            )
        self.assertEqual(Debt.objects.filter(group=self.group).count(), 0)
