# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-22 12:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20170822_1201'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='flight',
            name='recipient_id',
        ),
        migrations.RemoveField(
            model_name='flight',
            name='recipient_name',
        ),
        migrations.AddField(
            model_name='flight',
            name='send_id',
            field=models.CharField(default='', max_length=255, verbose_name='Send id'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='flight',
            name='send_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Send name'),
        ),
    ]