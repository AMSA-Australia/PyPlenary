from django import forms
from django.db import models
from django.contrib.auth.models import User

class Institution(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, null=True)
    shortName = models.CharField(max_length=100, null=True)
    state = models.CharField(max_length=100, null=True)
    votesWeight = models.IntegerField(default=1)
    is_node = models.BooleanField()

    class Meta:
        db_table = 'Institution'

    def __str__(self):
        output = f'{self.shortName} - {self.name}'
        return output

class Delegate(models.Model):
    id = models.AutoField(primary_key=True)
    authClone = models.OneToOneField(User, models.PROTECT, db_column='authClone', null=True)
    name = models.CharField(max_length=100, null=True)
    email = models.EmailField(max_length=254, null=True, blank=True, unique=True)
    rep = models.BooleanField(default=False)
    superadmin = models.BooleanField(default=False)
    institution = models.ForeignKey(Institution, models.CASCADE, null=True)
    role = models.CharField(max_length=200, null=True)
    speakerNum = models.IntegerField(default=0)
    pronouns = models.CharField(max_length=100, null=True)
    first_time = models.BooleanField(default=False)

    class Meta:
        db_table = 'Delegate'

    def __str__(self):
        output = f'{self.name} ({self.institution.shortName})'
        return output

class Poll(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=500, null=True)
    yesVotes = models.IntegerField(default=0)
    noVotes = models.IntegerField(default=0)
    abstainVotes = models.IntegerField(default=0)
    startTime = models.DateTimeField(auto_now_add=True, null=True)
    endTime = models.DateTimeField(null=True)
    active = models.BooleanField(default=False)
    anonymous = models.BooleanField(default=False)
    repsOnly = models.BooleanField(default=False)
    weighted = models.BooleanField(default=False)
    supermajority = models.BooleanField(default=False) #False for simple, True for super
    roll_call = models.BooleanField(default=False)
    outcome = models.IntegerField(default=0) # 0 for no result, 1 for pass, 2 for fail, 3 for chair's call

    # TODO: Separately store number of ballots and number of votes

    class Meta:
        db_table = 'Poll'

    def __str__(self):
        output = f'{self.id} - {self.title}'
        return output
    
    def describe(self):
        result = []
        result.append('AMSA Reps only' if self.repsOnly else 'Voting open to all')
        if self.roll_call:
            result.append('Roll call')
        result.append('Anonymous voting' if self.anonymous else 'Non-anonymous')
        result.append('Requires ⅔ supermajority' if self.supermajority else 'Requires ½ simple majority')
        result.append('Institutional-weighted votes' if self.weighted else 'Votes not weighted')
        return result

class Proxy(models.Model):
    id = models.AutoField(primary_key=True)
    voter = models.ForeignKey(Delegate, models.CASCADE, related_name='Proxy_voter')
    holder = models.ForeignKey(Delegate, models.CASCADE, related_name='Proxy_holder')
    active = models.BooleanField(default=True)
    activeTime = models.DateTimeField(auto_now_add=True, null=True)
    expiryTime = models.DateTimeField(null=True)

    class Meta:
        db_table = 'Proxy'

    def __str__(self):
        output = f'{self.holder.name}: proxy for {self.voter.name}'
        return output

class Vote(models.Model):
    id = models.AutoField(primary_key=True)
    poll = models.ForeignKey(Poll, models.CASCADE)
    voter = models.ForeignKey(Delegate, models.CASCADE, related_name='Vote_voter')
    proxy = models.ForeignKey(Proxy, models.CASCADE, null=True)
    vote = models.IntegerField(default=0) # 0 for abstain, 1 for Yes, 2 for No 
    voteWeight = models.IntegerField(default=1)
    voteTime = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = 'Vote'

    def __str__(self):
        output = f'{self.poll.title} - {self.rep.institution} - {self.vote}'
        return output

class ResetToken(models.Model):
    id = models.AutoField(primary_key=True)
    token = models.CharField(max_length=100, null=True)
    active = models.BooleanField(default = True)
    user = models.ForeignKey(User, models.DO_NOTHING, db_column = 'user', null=True)
    
    class Meta:
        db_table = 'ResetToken'

class PendingRego(models.Model):
    id = models.AutoField(primary_key=True)
    token = models.CharField(max_length=100, null=True)
    active = models.BooleanField(default = True)
    name = models.CharField(max_length=100, null=True)
    email = models.EmailField(max_length=254, null=True)
    institution = models.ForeignKey(Institution, models.CASCADE, null=True)
    role = models.CharField(max_length=200, null=True)
    pronouns = models.CharField(max_length=100, null=True)
    firstTime = models.BooleanField(default=False)

    class Meta:
        db_table = 'PendingRego'


class Speaker(models.Model):
    """An entry on the Speaker List"""
    id = models.AutoField(primary_key=True)
    delegate = models.ForeignKey(Delegate, models.CASCADE)
    index = models.IntegerField()
    intention = models.IntegerField() # 0 = standard, 1 = point of order, 2 = for, 3 = against
    node = models.ForeignKey(Institution, models.CASCADE, null=True)
    
    class Meta:
        db_table = 'Speaker'
        ordering = ['index']
    
    # For speaker list websockets
    
    @staticmethod
    def speakers_for_ws():
        return [s.to_json() for s in Speaker.objects.all().select_related('delegate', 'delegate__institution', 'node')]
    
    def to_json(self):
        return {
            'delegate': {'id': self.delegate.id, 'name': self.delegate.name, 'role': self.delegate.role, 'speakerNum': self.delegate.speakerNum, 'first_time': self.delegate.first_time, 'institution': self.delegate.institution.shortName},
            'index': self.index,
            'intention': self.intention,
            'node': self.node.shortName if self.node is not None else '',
        }
