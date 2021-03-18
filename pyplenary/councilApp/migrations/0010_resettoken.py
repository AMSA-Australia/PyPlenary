# Generated by Django 3.1.7 on 2021-03-18 09:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('councilApp', '0009_delegate_pronouns'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResetToken',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('token', models.CharField(max_length=100, null=True)),
                ('active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(db_column='user', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'ResetTokens',
            },
        ),
    ]
