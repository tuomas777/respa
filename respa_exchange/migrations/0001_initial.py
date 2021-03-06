# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-04-15 07:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('resources', '0034_add_reserver_email'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExchangeConfiguration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='a descriptive name for this Exchange configuration', max_length=70, unique=True, verbose_name='name')),
                ('url', models.URLField(help_text='the URL to the Exchange Web Service (e.g. https://contoso.com/EWS/Exchange.asmx)', verbose_name='EWS URL')),
                ('username', models.CharField(help_text='the service user to authenticate as, in domain\\username format', max_length=64, verbose_name='username')),
                ('password', models.CharField(help_text="the user's password (stored as plain-text)", max_length=256, verbose_name='password')),
                ('enabled', models.BooleanField(db_index=True, default=True, help_text='whether synchronization is enabled at all against this Exchange instance', verbose_name='enabled')),
            ],
            options={
                'verbose_name': 'Exchange configuration',
                'verbose_name_plural': 'Exchange configurations',
            },
        ),
        migrations.CreateModel(
            name='ExchangeReservation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_id_hash', models.CharField(db_index=True, editable=False, max_length=32)),
                ('principal_email', models.EmailField(editable=False, max_length=254)),
                ('_item_id', models.CharField(blank=True, db_column='item_id', editable=False, max_length=200)),
                ('_change_key', models.CharField(blank=True, db_column='change_key', editable=False, max_length=100)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='time of creation')),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='time of modification')),
                ('exchange', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, to='respa_exchange.ExchangeConfiguration')),
                ('reservation', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.DO_NOTHING, to='resources.Reservation')),
            ],
            options={
                'verbose_name': 'Exchange reservation',
                'verbose_name_plural': 'Exchange reservations',
            },
        ),
        migrations.CreateModel(
            name='ExchangeResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sync_to_respa', models.BooleanField(db_index=True, default=True, help_text='if disabled, events will not be synced from the Exchange calendar to Respa', verbose_name='sync Exchange to Respa')),
                ('sync_from_respa', models.BooleanField(db_index=True, default=True, help_text='if disabled, new events will not be synced from Respa to the Exchange calendar; pre-existing events continue to be updated', verbose_name='sync Respa to Exchange')),
                ('principal_email', models.EmailField(help_text='the email address for this resource in Exchange', max_length=254, unique=True, verbose_name='principal email')),
                ('exchange', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='respa_exchange.ExchangeConfiguration', verbose_name='Exchange configuration')),
                ('resource', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='resources.Resource', verbose_name='resource')),
            ],
            options={
                'verbose_name': 'Exchange resource',
                'verbose_name_plural': 'Exchange resources',
            },
        ),
    ]
