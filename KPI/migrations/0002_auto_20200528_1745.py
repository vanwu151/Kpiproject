# Generated by Django 3.0.1 on 2020-05-28 17:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('KPI', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='score',
            old_name='score_requiredepartment',
            new_name='score_require_department',
        ),
        migrations.RenameField(
            model_name='score',
            old_name='score_requireusername',
            new_name='score_require_username',
        ),
    ]
