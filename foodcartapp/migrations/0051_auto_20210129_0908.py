# Generated by Django 3.0.7 on 2021-01-29 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0050_auto_20210116_1256'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='comment',
            field=models.TextField(default='', verbose_name='Комментарий'),
        ),
    ]
