# Generated by Django 3.0.7 on 2021-01-29 10:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0052_auto_20210129_0915'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment',
            field=models.CharField(choices=[('online', 'Картой курьеру'), ('cash', 'Наличными курьеру'), ('prepayment', 'Оплачено')], db_index=True, default='cash', max_length=10, verbose_name='Способ оплаты'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('new', 'Новый'), ('in_progress', 'Выполняется'), ('completed', 'Выполнен')], db_index=True, default='new', max_length=11, verbose_name='Статус заказа'),
        ),
    ]
