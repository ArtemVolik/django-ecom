# Generated by Django 3.0.7 on 2021-01-13 11:40

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0042_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='called_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Принят'),
        ),
        migrations.AddField(
            model_name='order',
            name='delivered_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Доставлен'),
        ),
        migrations.AddField(
            model_name='order',
            name='payment',
            field=models.CharField(choices=[('O', 'Картой курьеру'), ('I', 'Наличными курьеру'), ('P', 'Оплачено')], default='I', max_length=2),
        ),
        migrations.AddField(
            model_name='order',
            name='registrated_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Оформлен'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('N', 'Новый'), ('P', 'Выполняется'), ('C', 'Выполнен')], default='N', max_length=2),
        ),
    ]
