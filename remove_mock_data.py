# python manage.py shell < remove_mock_data.py

from split_free_all.models import Balance, Debt, Expense, Group, Member

Expense.objects.all().delete()
Group.objects.all().delete()
Member.objects.all().delete()
Balance.objects.all().delete()
Debt.objects.all().delete()
