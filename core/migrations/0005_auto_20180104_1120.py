# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-04 11:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20170822_1223'),
    ]

    operations = [
        migrations.AddField(
            model_name='flight',
            name='warnings',
            field=models.IntegerField(default=0, editable=False),
        ),
        migrations.AlterField(
            model_name='flight',
            name='status',
            field=models.CharField(choices=[('I', 'Init'), ('W', 'Waiting'), ('C', 'Canceled'), ('A', 'Arrived'), ('H', 'Help'), ('O', 'OK'), ('R', 'Removed')], default='I', max_length=1, verbose_name='Status'),
        ),
    ]
