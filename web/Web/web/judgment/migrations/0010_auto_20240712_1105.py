# Generated by Django 3.0.5 on 2024-07-12 15:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_session_show_debugging_content'),
        ('judgment', '0009_debuggingjudgment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='judgment',
            name='session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='judgments', to='core.Session'),
        ),
    ]