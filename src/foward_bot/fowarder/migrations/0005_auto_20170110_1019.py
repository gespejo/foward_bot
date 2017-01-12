# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-01-10 10:19
from __future__ import unicode_literals

from django.db import migrations, models
import foward_bot.fowarder.models


class Migration(migrations.Migration):

    dependencies = [
        ('fowarder', '0004_autoforward_message_header'),
    ]

    operations = [
        migrations.AddField(
            model_name='autoforward',
            name='message_count',
            field=models.BigIntegerField(default=0, verbose_name='Messages Forwarded'),
        ),
        migrations.AlterField(
            model_name='autoforward',
            name='lang',
            field=models.CharField(choices=[(b'ar', b'ARABIC'), (b'zh', b'CHINESE'), (b'en', b'ENGLISH'), (b'fr', b'FRENCH'), (b'de', b'GERMAN'), (b'hi', b'HINDI'), (b'None', b'NONE'), (b'ru', b'RUSSIAN'), (b'es', b'SPANISH')], default=foward_bot.fowarder.models.Languages('None'), max_length=10, verbose_name='Language'),
        ),
    ]
