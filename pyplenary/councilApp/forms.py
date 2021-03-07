from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .helperFunctions import *
# from .models import Delegates

# class LoginForm(forms.Form):
# 	username = forms.CharField(label='Email', help_text='Please enter the email you signed up with.')
# 	password = forms.CharField(widget=forms.PasswordInput, label='Password', help_text='This is case-sensitive.')

# class PasswordChangeEmail(forms.Form):
# 	email = forms.EmailField(max_length=254, label="", widget=forms.TextInput(attrs={'placeholder': 'Email'}))