# Generated by Django 3.0.7 on 2021-01-13 10:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0041_auto_20210112_1626'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('N', 'Новый'), ('P', 'Выполняется'), ('C', 'Выполнен')], default='N', max_length=3),
        ),
    ]
