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

class Polls(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=500, null=True)
    yesVotes = models.IntegerField(default=0)
    noVotes = models.IntegerField(default=0)
    abstainVotes = models.IntegerField(default=0)
    startTime = models.DateTimeField(auto_now_add=True, null=True)
    endTime = models.DateTimeField(null=True)
    active = models.BooleanField(default=False)
    anonymous = models.BooleanField(default=False)
    repsOnly = models.BooleanField(default=True)

    class Meta:
        db_table = 'Polls'

    def __str__(self):
        output = f'{self.id} - {self.title}'
        return output

class Votes(models.Model):
    id = models.AutoField(primary_key=True)
    poll = models.ForeignKey(Polls, models.CASCADE)
    voter = models.ForeignKey(Delegates, models.CASCADE, related_name='voter')
    proxy = models.ForeignKey(Delegates, models.CASCADE, null=True, related_name='proxy')
    vote = models.IntegerField(default=0) # 2 for Yes, 1 for No, 0 for Abstain
    voteTime = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = 'Votes'

    def __str__(self):
        output = f'{self.poll.title} - {self.rep.institution} - {self.vote}'
        return output
