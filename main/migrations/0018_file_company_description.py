# Generated by Django 2.0.4 on 2019-02-26 10:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_auto_20190218_0620'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='company_description',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),

    ]
