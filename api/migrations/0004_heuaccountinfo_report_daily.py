# Generated by Django 3.2 on 2021-04-27 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_heuaccountinfo_account_verify_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='heuaccountinfo',
            name='report_daily',
            field=models.BooleanField(default=False),
        ),
    ]
