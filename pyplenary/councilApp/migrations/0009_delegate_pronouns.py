# Generated by Django 3.1.7 on 2021-03-15 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('councilApp', '0008_auto_20210315_2056'),
    ]

    operations = [
        migrations.AddField(
            model_name='delegate',
            name='pronouns',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
