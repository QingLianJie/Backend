# Generated by Django 3.2 on 2021-04-16 02:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20210407_2012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='heuaccountinfo',
            name='account_verify_status',
            field=models.BooleanField(default=False),
        ),
    ]