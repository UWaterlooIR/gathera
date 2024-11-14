# Generated by Django 3.0.5 on 2024-11-13 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_logevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='disable_search',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='session',
            name='integrated_cal',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='session',
            name='nudge_to_cal',
            field=models.BooleanField(default=False),
        ),
    ]
