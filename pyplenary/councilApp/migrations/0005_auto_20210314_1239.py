# Generated by Django 3.1.7 on 2021-03-14 01:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('councilApp', '0004_poll_outcome'),
    ]

    operations = [
        migrations.AlterField(
            model_name='poll',
            name='outcome',
            field=models.IntegerField(default=0),
        ),
    ]
