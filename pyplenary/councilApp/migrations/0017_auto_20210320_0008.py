# Generated by Django 3.1.7 on 2021-03-19 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('councilApp', '0016_auto_20210320_0003'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pendingrego',
            name='email',
            field=models.EmailField(max_length=254, null=True),
        ),
    ]
