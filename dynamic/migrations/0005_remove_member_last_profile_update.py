# Generated by Django 3.2.9 on 2021-12-03 03:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dynamic', '0004_auto_20211203_1150'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='member',
            name='last_profile_update',
        ),
    ]