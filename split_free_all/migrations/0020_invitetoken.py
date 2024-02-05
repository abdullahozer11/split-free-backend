# Generated by Django 4.2 on 2024-02-05 18:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("split_free_all", "0019_alter_group_users"),
    ]

    operations = [
        migrations.CreateModel(
            name="InviteToken",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("hash", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                (
                    "group",
                    models.ForeignKey(
                        default=None,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="split_free_all.group",
                    ),
                ),
            ],
            options={
                "unique_together": {("hash", "group")},
            },
        ),
    ]
