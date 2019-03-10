# Generated by Django 2.1.7 on 2019-03-05 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BinanceCoinList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coinsymbol', models.CharField(max_length=10, verbose_name='Coin')),
                ('trackstate', models.BooleanField(verbose_name='Takip Durumu')),
            ],
            options={
                'ordering': ['coinsymbol'],
            },
        ),
    ]
