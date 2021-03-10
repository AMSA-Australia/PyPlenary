from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.http import JsonResponse, FileResponse, Http404, HttpResponse
from django.contrib.auth.models import User
from django.forms import formset_factory, ValidationError
from django.core import mail
from django.core.mail import send_mail
from django.views.decorators.http import last_modified
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .forms import *
from .models import *
import toml
import os

# Load config
print(os.getcwd())
with open('config.toml', 'r', encoding='utf8') as f:
	config = toml.load(f)

def index(request):
    return render(request, 'councilApp/index.html', {'active_tab':'index', 'config':config})

def speakerList(request):
    return render(request, 'councilApp/speaker_list.html', {'active_tab':'speaker_list', 'config':config})

def delegates(request):
    allDelegates = Delegates.objects.all()
    allDelegates = sorted(allDelegates, key=lambda x:x.speakerNum)
    thisDelegateId = None
    if request.user.is_authenticated:
        thisDelegateId = Delegates.objects.get(authClone=request.user).id
    return render(request, 'councilApp/delegates.html', {'allDelegates':allDelegates, 'thisDelegateId':thisDelegateId, 
        'active_tab':'delegates', 'config':config})

def profile(request):
    return render(request, 'councilApp/profile.html', {'active_tab':'profile', 'config':config})

def vote(request):
    return render(request, 'councilApp/vote.html', {'active_tab':'vote', 'config':config})

def loginCustom(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        loginForm = LoginForm(request.POST)
        if loginForm.is_valid():
            username = loginForm.cleaned_data.get('username')
            password = loginForm.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user == None:
                loginForm = LoginForm()
                return render(request, 'councilApp/login.html', {'loginForm':loginForm, 'wrong':True, 'active_tab':'login', 'config':config})
            else:
                login(request, user)
                try:
                    return redirect(request.GET['next'])
                except:
                    return redirect('/')
    else:
        loginForm = LoginForm()

    return render(request, 'councilApp/login.html', {'loginForm':loginForm, 'wrong':False, 'active_tab':'login', 'config':config})

def logoutCustom(request):
    logout(request)
    return redirect('/')