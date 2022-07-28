# Generated by Django 4.0.1 on 2022-05-22 18:00

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facilities', '0013_alter_edited_facility_info_date_edited_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='edited_facility_info',
            name='date_edited',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2022, 5, 22, 21, 0, 50, 550977), null=True),
        ),
        migrations.AlterField(
            model_name='emr_info',
            name='date_of_emr_impl',
            field=models.DateField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='facility_info',
            name='date_added',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2022, 5, 22, 21, 0, 50, 550977), null=True),
        ),
    ]