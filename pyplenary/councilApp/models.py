from django import forms
from .forms import *
from django.db import models
from django.contrib.auth.models import User

class Delegates(models.Model):
    id = models.AutoField(primary_key=True)
    authClone = models.OneToOneField(User, models.PROTECT, db_column='authClone', null=True)
    name = models.CharField(max_length=100, null=True)
    email = models.EmailField(max_length=254, null=True, blank=True, unique=True)
    rep = models.BooleanField(default=False)
    superadmin = models.BooleanField(default=False)
    institution = models.CharField(max_length=100, null=True)
    role = models.CharField(max_length=200, null=True)
    speakerNum = models.IntegerField(default=0)

    class Meta:
        db_table = 'Delegates'

    def __str__(self):
        output = f'{self.speakerNum}. {self.name} - {self.role}'
        return output