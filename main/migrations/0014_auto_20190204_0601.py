# Generated by Django 2.0.4 on 2019-02-04 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_auto_20190123_0925'),
    ]

    operations = [
        migrations.AddField(
            model_name='result',
            name='del_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='storedsearch',
            name='del_id',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='storedsearch',
            name='description',
            field=models.CharField(max_length=140, unique=True),
        ),
    ]
