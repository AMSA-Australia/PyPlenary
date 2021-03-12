from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core import mail
from django.core.mail import send_mail
from django.forms import formset_factory, ValidationError
from django.http import JsonResponse, FileResponse, Http404, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.cache import never_cache
from django.views.decorators.http import last_modified
from datetime import datetime

from .forms import *
from .models import *
import toml
import os

# Load config
os.chdir(settings.BASE_DIR)
print(os.getcwd())
with open('../config.toml', 'r', encoding='utf8') as f:
	config = toml.load(f)

def index(request):
    return render(request, 'councilApp/index.html', {'active_tab':'index', 'config':config})

def speakerList(request):
    return render(request, 'councilApp/speaker_list.html', {'active_tab':'speaker_list', 'config':config})

def delegates(request):
    allDelegates = sorted(Delegate.objects.all(), key=lambda x:x.speakerNum)
    thisDelegateId = None
    if request.user.is_authenticated:
        thisDelegateId = Delegate.objects.get(authClone=request.user).id
    return render(request, 'councilApp/delegates.html', {'allDelegates':allDelegates, 'thisDelegateId':thisDelegateId, 
        'active_tab':'delegates', 'config':config})

def profile(request):
    return render(request, 'councilApp/profile.html', {'active_tab':'profile', 'config':config})

@login_required
def vote(request):
    return render(request, 'councilApp/vote.html', {'active_tab':'vote', 'config':config})

def poll(request):
    pass

@login_required
def createPoll(request):
    delegate = Delegate.objects.get(authClone = request.user)
    if not delegate.superadmin:
        raise Http404()

    allPolls = Poll.objects.all()
    active = sum([i.active for i in allPolls])

    if not active:
        if request.method == 'POST':
            pollForm = StartPollForm(request.POST)
            if pollForm.is_valid():
                for i in Poll.objects.all():
                    i.active = False
                    i.save()
                newPoll = Poll()
                newPoll.title = pollForm.cleaned_data.get('title')
                newPoll.anonymous = pollForm.cleaned_data.get('anonymous')
                newPoll.repsOnly = pollForm.cleaned_data.get('repsOnly')
                newPoll.weighted = pollForm.cleaned_data.get('weighted')
                newPoll.supermajority = pollForm.cleaned_data.get('majority') == 'super'
                newPoll.active = True
                newPoll.save()
                return redirect('/poll/')
        else:
            pollForm = StartPollForm()
            
        return render(request, 'councilApp/poll.html', {'pollForm':pollForm, 'active':False, 'active_tab':'poll', 'config':config})
    
    else:
        return redirect('/poll/')



@login_required
def closePoll(request):
    if not Delegate.objects.get(authClone = request.user).superadmin:
        raise Http404()
    activePoll = Poll.objects.get(active = True)
    if not activePoll:
        raise Http404()
    
    activePoll.endTime = timezone.now()

    votesInPoll = Vote.objects.filter(poll = activePoll)
    activePoll.yesVotes = sum([i.voteWeight for i in votesInPoll if i.vote == 2])
    activePoll.noVotes = sum([i.voteWeight for i in votesInPoll if i.vote == 1])
    activePoll.abstainVotes = sum([i.voteWeight for i in votesInPoll if i.vote == 0])
    activePoll.outcome = False
    if activePoll.supermajority:
        if activePoll.yesVotes > 2*activePoll.noVotes:
            activePoll.outcome = True
    else:
        if activePoll.yesVotes > activePoll.noVotes:
            activePoll.outcome = True
        
    activePoll.active = False
    activePoll.save()

    for i in Poll.objects.all():
        i.active = False
        i.save()
    
    return redirect(f'/poll/{activePoll.id}/')

def endedPollInfo(request, pollId):
    poll = Poll.objects.get(id=pollId)
    if not poll:
        raise Http404()

    return render(request, 'councilApp/pollInfo.html', {'poll':poll, 'active_tab':'poll', 'config':config})


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
