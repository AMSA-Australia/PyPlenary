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
from .utils import *
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
    thisDelegateId = Delegate.objects.get(authClone=request.user).id if request.user.is_authenticated else None
    return render(request, 'councilApp/delegates.html', {'allDelegates':allDelegates, 'thisDelegateId':thisDelegateId, 
        'active_tab':'delegates', 'config':config})

@login_required
def proxy(request):
    delegate = Delegate.objects.get(authClone=request.user)

    proxiesForMe = Proxy.objects.filter(voter=delegate, active=True)
    proxiesIHold = Proxy.objects.filter(holder=delegate, active=True)

    allDelegates = sorted(Delegate.objects.exclude(id=delegate.id), key=lambda x:x.speakerNum)

    return render(request, 'councilApp/proxy.html', {'delegate':delegate, 'proxiesForMe':proxiesForMe, 'proxiesIHold':proxiesIHold,
        'allDelegates':allDelegates, 'active_tab':'proxy', 'config':config})

def proxyNominate(request):
    try:
        delegate = Delegate.objects.get(authClone=request.user)
        candidateId = request.GET.get('candidateId', None)
        holder = Delegate.objects.get(id=candidateId)
    except:
        return JsonResponse({'raise404':True, 'newProxy':None})
    
    proxiesForMe = Proxy.objects.filter(voter=delegate, active=True)
    if proxiesForMe:
        return JsonResponse({'raise404':True, 'newProxy':None})

    newProxy = Proxy()
    newProxy.voter = delegate
    newProxy.holder = holder
    newProxy.save()

    data = {'raise404':False, 'newProxy':[holder.name, holder.institution.shortName]}
    return JsonResponse(data)

def proxyRetract(request):
    try:
        delegate = Delegate.objects.get(authClone=request.user)
        proxiesForMe = Proxy.objects.filter(voter=delegate, active=True)
    except:
        return JsonResponse({'raise404':True, 'oldProxy':None})
    if len(proxiesForMe) != 1:
        return JsonResponse({'raise404':True, 'oldProxy':None})
    activeProxy = proxiesForMe[0]
    activeProxy.active = False
    activeProxy.expiryTime = timezone.now()
    activeProxy.save()

    data = {'raise404':False, 'oldProxy':[activeProxy.holder.name, activeProxy.holder.institution.shortName]}
    return JsonResponse(data)

def proxyResign(request):
    try:
        delegate = Delegate.objects.get(authClone=request.user)
        proxyId = request.GET.get('proxyId', None)
        activeProxy = Proxy.objects.get(id=proxyId)
    except:
        return JsonResponse({'raise404':True, 'oldProxy':None})
    if not activeProxy.active:
        return JsonResponse({'raise404':True, 'oldProxy':None})

    activeProxy.active = False
    activeProxy.expiryTime = timezone.now()
    activeProxy.save()

    data = {'raise404':False, 'oldProxy':[activeProxy.holder.name, activeProxy.holder.institution.shortName]}
    return JsonResponse(data)

@login_required
def vote(request):
    return render(request, 'councilApp/vote.html', {'active_tab':'vote', 'config':config})

@login_required
def poll(request):
    allPolls = sorted(Poll.objects.all(), key=lambda x:-x.id)
    delegate = Delegate.objects.get(authClone=request.user) if request.user.is_authenticated else None
    superadmin = delegate.superadmin if delegate is not None else False
    rep = delegate.rep if delegate is not None else False
    activePolls = [i for i in allPolls if i.active and eligibleToVote(delegate, i)]
    print(activePolls)
    return render(request, 'councilApp/poll.html', {'allPolls':allPolls, 'superadmin':superadmin, 'rep':rep, 'activePolls':activePolls,
        'active_tab':'poll', 'config':config})

@login_required
def createPoll(request):
    if not Delegate.objects.get(authClone = request.user):
        raise Http404()

    if request.method == 'POST':
        pollForm = StartPollForm(request.POST)
        if pollForm.is_valid():
            newPoll = Poll()
            newPoll.title = pollForm.cleaned_data.get('title')
            newPoll.anonymous = pollForm.cleaned_data.get('anonymous')
            newPoll.repsOnly = pollForm.cleaned_data.get('repsOnly')
            newPoll.weighted = pollForm.cleaned_data.get('weighted')
            newPoll.supermajority = pollForm.cleaned_data.get('majority') == 'super'
            newPoll.active = True
            newPoll.save()
            return redirect(f'/poll/{newPoll.id}')
    else:
        pollForm = StartPollForm()
        
    return render(request, 'councilApp/pollCreate.html', {'pollForm':pollForm, 'active':False, 'active_tab':'poll', 'config':config})
    
@login_required
def closePoll(request, pollId):
    if not Delegate.objects.get(authClone = request.user).superadmin:
        raise Http404()
    try:
        activePoll = Poll.objects.filter(id = pollId)[0]
    except:
        raise Http404()
    
    activePoll.endTime = timezone.now()

    votesInPoll = Vote.objects.filter(poll = activePoll)
    activePoll.yesVotes = sum([i.voteWeight for i in votesInPoll if i.vote == 2])
    activePoll.noVotes = sum([i.voteWeight for i in votesInPoll if i.vote == 1])
    activePoll.abstainVotes = sum([i.voteWeight for i in votesInPoll if i.vote == 0])
    multiplier = 2 if activePoll.supermajority else 1
    if activePoll.yesVotes > multiplier*activePoll.noVotes:
        activePoll.outcome = 1
    elif activePoll.yesVotes == multiplier*activePoll.noVotes:
        activePoll.outcome = 3
    else:
        activePoll.outcome = 2

    activePoll.active = False
    activePoll.save()
    
    return redirect(f'/poll/{activePoll.id}/')

def pollInfo(request, pollId):
    try:
        poll = Poll.objects.filter(id = pollId)[0]
    except:
        raise Http404()

    superadmin = True if request.user.is_authenticated and Delegate.objects.get(authClone=request.user).superadmin else False

    return render(request, 'councilApp/pollInfo.html', {'poll':poll, 'superadmin':superadmin, 'active_tab':'poll', 'config':config})

@login_required
def voteOnPoll(request, pollId):
    pass


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
