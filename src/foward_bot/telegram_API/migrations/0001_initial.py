# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-12-20 22:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_index=True, max_length=100, verbose_name='Token')),
                ('register', models.CharField(blank=True, max_length=1000, verbose_name='Register')),
                ('ssl_certificate', models.FileField(blank=True, null=True, upload_to='telegrambot/ssl/', verbose_name='SSL certificate')),
                ('enabled', models.BooleanField(default=True, verbose_name='Enable')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Date Modified')),
            ],
            options={
                'verbose_name': 'Bot',
                'verbose_name_plural': 'Bots',
            },
        ),
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('type', models.CharField(choices=[('private', 'Private'), ('group', 'Group'), ('supergroup', 'Supergroup'), ('channel', 'Channel')], max_length=255)),
                ('title', models.CharField(blank=True, max_length=255, null=True)),
                ('username', models.CharField(blank=True, max_length=255, null=True)),
                ('first_name', models.CharField(blank=True, max_length=255, null=True)),
                ('last_name', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'Chat',
                'verbose_name_plural': 'Chats',
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date updated')),
                ('message_id', models.BigIntegerField(db_index=True, verbose_name='Id')),
                ('date', models.DateTimeField(verbose_name='Date')),
                ('text', models.TextField(blank=True, null=True, verbose_name='Text')),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='telegram_API.Chat', verbose_name='Chat')),
            ],
            options={
                'ordering': ['-date'],
                'verbose_name': 'Message',
                'verbose_name_plural': 'Messages',
            },
        ),
        migrations.CreateModel(
            name='Update',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date updated')),
                ('update_id', models.BigIntegerField(db_index=True, verbose_name='Update Id')),
                ('bot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='updates', to='telegram_API.Bot', verbose_name='Bot')),
                ('message', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='updates', to='telegram_API.Message', verbose_name='Message')),
            ],
            options={
                'verbose_name': 'Update',
                'verbose_name_plural': 'Updates',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=255, verbose_name='First name')),
                ('last_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Last name')),
                ('username', models.CharField(blank=True, max_length=255, null=True, verbose_name='User name')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
        ),
        migrations.AddField(
            model_name='message',
            name='forward_from',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='forwarded_from', to='telegram_API.User', verbose_name='Forward from'),
        ),
        migrations.AddField(
            model_name='message',
            name='from_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='telegram_API.User', verbose_name='User'),
        ),
        migrations.AlterUniqueTogether(
            name='update',
            unique_together=set([('update_id', 'bot')]),
        ),
    ]
