# Generated by Django 3.0.5 on 2020-09-28 17:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('judgment', '0003_auto_20200702_1232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='judgment',
            name='relevance',
            field=models.IntegerField(blank=True, choices=[(2, 'Highly Relevant'), (1, 'Relevant'), (0, 'Non-Relevant')], null=True, verbose_name='Relevance'),
        ),
    ]
