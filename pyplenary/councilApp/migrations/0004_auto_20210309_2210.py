# Generated by Django 3.1.7 on 2021-03-09 11:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('councilApp', '0003_auto_20210309_2157'),
    ]

    operations = [
        migrations.AddField(
            model_name='votes',
            name='proxy',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='proxy', to='councilApp.delegates'),
        ),
        migrations.AlterField(
            model_name='votes',
            name='voter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='voter', to='councilApp.delegates'),
        ),
    ]
