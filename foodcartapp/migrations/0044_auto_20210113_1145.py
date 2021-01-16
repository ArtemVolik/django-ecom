# Generated by Django 3.0.7 on 2021-01-13 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0043_auto_20210113_1140'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment',
            field=models.CharField(choices=[('online', 'Картой курьеру'), ('cash', 'Наличными курьеру'), ('prepayment', 'Оплачено')], default='cash', max_length=10),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('new', 'Новый'), ('in_progress', 'Выполняется'), ('completed', 'Выполнен')], default='new', max_length=11),
        ),
    ]