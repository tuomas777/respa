# Generated by Django 2.1.7 on 2019-05-27 20:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0077_resource_slot_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='state',
            field=models.CharField(choices=[('created', 'created'), ('cancelled', 'cancelled'), ('confirmed', 'confirmed'), ('denied', 'denied'), ('requested', 'requested'), ('waiting_for_payment', 'waiting for payment')], default='created', max_length=32, verbose_name='State'),
        ),
    ]
