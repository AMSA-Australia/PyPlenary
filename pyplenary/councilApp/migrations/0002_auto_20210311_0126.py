# Generated by Django 3.1.7 on 2021-03-10 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('councilApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='supermajority',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='poll',
            name='weighted',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='poll',
            name='repsOnly',
            field=models.BooleanField(default=False),
        ),
    ]
