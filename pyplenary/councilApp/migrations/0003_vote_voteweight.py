# Generated by Django 3.1.7 on 2021-03-10 16:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('councilApp', '0002_auto_20210311_0126'),
    ]

    operations = [
        migrations.AddField(
            model_name='vote',
            name='voteWeight',
            field=models.IntegerField(default=1),
        ),
    ]
