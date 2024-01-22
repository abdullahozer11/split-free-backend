# python manage.py shell < mock_data.py

from split_free_all.models import Expense, Group, Member

group1 = Group.objects.create(
    title="Apartment 101", description="Home related purchases"
)
member1 = Member.objects.create(name="Alice", group=group1)
member2 = Member.objects.create(name="Bob", group=group1)
member3 = Member.objects.create(name="Charlie", group=group1)
group1.members.set([member1, member2, member3])
expense1 = Expense.objects.create(
    group=group1,
    title="Groceries",
    description="Shopping for the week",
    amount=102.00,
    currency="EUR",
    date="2023-01-01 12:30:00",
    payer=member1,
)
expense1.participants.set([member1, member2, member3])

group2 = Group.objects.create(
    title="Road Trip Crew", description="Vacation related expenses"
)
member4 = Member.objects.create(name="Samantha", group=group2)
member5 = Member.objects.create(name="Omar", group=group2)
group2.members.set([member4, member5])
expense2 = Expense.objects.create(
    group=group2,
    title="Movie Night",
    description="Tickets and snacks",
    amount=40.00,
    currency="EUR",
    date="2023-03-10 12:30:00",
    payer=member4,
)
expense2.participants.set([member4, member5])

group3 = Group.objects.create(title="OWW", description="We had a lunch once")
member6 = Member.objects.create(name="Louis", group=group3)
member7 = Member.objects.create(name="Apo", group=group3)
member8 = Member.objects.create(name="Michael", group=group3)
group3.members.set([member6, member7, member8])
expense3 = Expense.objects.create(
    group=group3,
    title="Dinner Out",
    description="Celebration dinner",
    amount=75.00,
    currency="EUR",
    date="2023-02-15 12:30:00",
    payer=member6,
)
expense3.participants.set([member6, member7, member8])
