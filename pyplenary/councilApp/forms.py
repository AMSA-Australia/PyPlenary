from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class LoginForm(forms.Form):
	username = forms.CharField(label='Email', help_text='Please enter the email you signed up with.')
	password = forms.CharField(widget=forms.PasswordInput, label='Password', help_text='This is case-sensitive.')

class PasswordChangeEmail(forms.Form):
	email = forms.EmailField(max_length=254, label="", widget=forms.TextInput(attrs={'placeholder': 'Email'}))

class StartPollForm(forms.Form):
	title = forms.CharField(max_length=1000, label="Poll title", widget=forms.TextInput(attrs={'placeholder': 'Motion to be put to a vote'}))
	anonymous = forms.BooleanField(required = False, label="Anonymous voting", 
		widget=forms.CheckboxInput(attrs={'class': 'centred-checkbox'}))
	repsOnly = forms.BooleanField(required = False, label="Reps only", 
		widget=forms.CheckboxInput(attrs={'class': 'centred-checkbox', 'id':'check_reps'}))
	weighted = forms.BooleanField(required = False, label="Institution-weighted vote", 
		widget=forms.CheckboxInput(attrs={'class': 'centred-checkbox', 'id':'check_weighted', 'disabled':True}))
	majority = forms.ChoiceField(required = True, label="Majority", choices=[('simple','Simple majority (1/2 of votes)'),('super','Supermajority (2/3 of votes)')],
		widget=forms.RadioSelect(), initial='simple')
	