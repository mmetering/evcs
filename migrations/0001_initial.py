# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-07-01 14:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('mmetering', '0023_meter_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChargingStation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('hardware_address', models.CharField(max_length=200, verbose_name='Hardware Adresse')),
            ],
            options={
                'verbose_name_plural': 'Tankstellen',
                'verbose_name': 'Tankstelle',
            },
        ),
        migrations.CreateModel(
            name='ChargingValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('start_value', models.FloatField()),
                ('end_value', models.FloatField()),
                ('charging_station', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='evcs.ChargingStation')),
            ],
        ),
        migrations.CreateModel(
            name='RFID',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('serial', models.CharField(max_length=128)),
                ('flat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mmetering.Flat')),
            ],
            options={
                'verbose_name_plural': 'RFIDs',
                'verbose_name': 'RFID',
            },
        ),
        migrations.AddField(
            model_name='chargingvalue',
            name='rfid',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='evcs.RFID', verbose_name='RFID'),
        ),
    ]
