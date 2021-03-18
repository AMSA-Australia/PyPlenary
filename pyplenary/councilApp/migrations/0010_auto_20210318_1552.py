# Generated by Django 3.1.7 on 2021-03-18 04:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('councilApp', '0009_delegate_pronouns'),
    ]

    operations = [
        migrations.AddField(
            model_name='delegate',
            name='first_time',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='Speaker',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('index', models.IntegerField()),
                ('point_of_order', models.BooleanField()),
                ('delegate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='councilApp.delegate')),
            ],
            options={
                'db_table': 'Speaker',
                'ordering': ['index'],
            },
        ),
    ]
