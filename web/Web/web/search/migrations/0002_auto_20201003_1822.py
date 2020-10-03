# Generated by Django 3.0.5 on 2020-10-03 22:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='searchresult',
            name='query',
        ),
        migrations.RemoveField(
            model_name='searchresult',
            name='session',
        ),
        migrations.RemoveField(
            model_name='searchresult',
            name='username',
        ),
        migrations.RemoveField(
            model_name='serpclick',
            name='session',
        ),
        migrations.RemoveField(
            model_name='serpclick',
            name='username',
        ),
        migrations.DeleteModel(
            name='Query',
        ),
        migrations.DeleteModel(
            name='SearchResult',
        ),
        migrations.DeleteModel(
            name='SERPClick',
        ),
    ]