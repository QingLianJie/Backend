# Generated by Django 3.2 on 2021-06-04 12:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_auto_20210604_2035'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='heuaccountinfo',
            name='first_time_collect_scores',
        ),
    ]
