# Generated by Django 2.0.4 on 2019-02-07 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_auto_20190204_0905'),
    ]

    operations = [
        migrations.AddField(
            model_name='storedsearch',
            name='searchset_id',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='result',
            name='sector',
            field=models.CharField(blank=True, max_length=255),
        )
    ]