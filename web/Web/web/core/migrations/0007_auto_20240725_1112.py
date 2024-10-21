# Generated by Django 3.0.5 on 2024-07-25 15:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_sessiontimer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sessiontimer',
            name='session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timers', to='core.Session'),
        ),
    ]