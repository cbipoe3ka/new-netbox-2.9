# Generated by Django 3.0.5 on 2020-04-23 10:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='payment_type',
            field=models.CharField(default='Rent', max_length=50),
        ),
    ]
