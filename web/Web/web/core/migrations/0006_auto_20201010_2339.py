# Generated by Django 3.0.5 on 2020-10-11 03:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20201010_1855'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ccnewsrecord',
            name='record_id',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]