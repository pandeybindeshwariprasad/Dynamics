# Generated by Django 2.0.6 on 2018-10-12 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_auto_20181010_1639'),
    ]

    operations = [
        migrations.AddField(
            model_name='result',
            name='new_flag',
            field=models.CharField(max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='result',
            name='uncertainty_flag',
            field=models.CharField(default='No', max_length=20),
        ),
    ]
