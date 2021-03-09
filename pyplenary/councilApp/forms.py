from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .helperFunctions import *
from .models import *

class LoginForm(forms.Form):
	username = forms.CharField(label='Email', help_text='Please enter the email you signed up with.')
	password = forms.CharField(widget=forms.PasswordInput, label='Password', help_text='This is case-sensitive.')

class PasswordChangeEmail(forms.Form):
	email = forms.EmailField(max_length=254, label="", widget=forms.TextInput(attrs={'placeholder': 'Email'}))

class StartPollForm(forms.Form):
	title = forms.CharField(max_length=1000, label="Poll title", widget=forms.TextInput(attrs={'placeholder': 'Poll topic'}))
	anonymous = forms.BooleanField(required = False, label="Anonymous voting", widget=forms.CheckboxInput(attrs={'class': 'centred-checkbox'}))
	repsOnly = forms.BooleanField(required = False, label="Reps only", widget=forms.CheckboxInput(attrs={'class': 'centred-checkbox'}))