import json
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core import mail
from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
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
import os
import yaml
from .utils import *

os.chdir(settings.BASE_DIR) # For loading agenda.yaml, etc.

def index(request):
    return render(request, 'councilApp/index.html', {'active_tab':'index'})

def speakerList(request):
    return render(request, 'councilApp/speaker_list.html', {'active_tab':'speaker_list'})

def delegates(request):
    allDelegates = sorted(Delegate.objects.all(), key=lambda x:x.speakerNum)
    thisDelegateId = Delegate.objects.get(authClone=request.user).id if request.user.is_authenticated else None
    return render(request, 'councilApp/delegates.html', {'allDelegates':allDelegates, 'thisDelegateId':thisDelegateId, 
        'active_tab':'delegates'})

@login_required
def proxy(request):
    delegate = Delegate.objects.get(authClone=request.user)

    proxiesForMe = Proxy.objects.filter(voter=delegate, active=True)
    proxiesIHold = Proxy.objects.filter(holder=delegate, active=True)

    allDelegates = sorted(Delegate.objects.exclude(id=delegate.id), key=lambda x:x.speakerNum)

    return render(request, 'councilApp/proxy.html', {'delegate':delegate, 'proxiesForMe':proxiesForMe, 'proxiesIHold':proxiesIHold,
        'allDelegates':allDelegates, 'active_tab':'proxy'})

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
        activeProxy = Proxy.objects.get(id=proxyId, active=True)
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
def poll(request):
    allPolls = sorted(Poll.objects.all(), key=lambda x:-x.id)
    delegate = Delegate.objects.get(authClone=request.user) if request.user.is_authenticated else None
    superadmin = delegate.superadmin if delegate is not None else False
    rep = delegate.rep if delegate is not None else False
    activePolls = [i for i in allPolls if i.active and eligibleToVote(delegate, i)]
    return render(request, 'councilApp/poll.html', {'allPolls':allPolls, 'superadmin':superadmin, 'rep':rep, 'activePolls':activePolls,
        'active_tab':'poll'})

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
        
    return render(request, 'councilApp/pollCreate.html', {'pollForm':pollForm, 'active':False, 'active_tab':'poll'})
    
@login_required
def closePoll(request, pollId):
    if not Delegate.objects.get(authClone = request.user).superadmin:
        raise Http404()
    try:
        activePoll = Poll.objects.filter(id = pollId, active=True)[0]
    except:
        raise Http404()
    
    activePoll.endTime = timezone.now()

    pollResults = calculateResults(activePoll)
    (activePoll.abstainVotes, activePoll.yesVotes, activePoll.noVotes) = pollResults

    if not activePoll.supermajority:
        # Ordinary majority
        if activePoll.yesVotes > activePoll.noVotes:
            activePoll.outcome = 1
        elif activePoll.yesVotes < activePoll.noVotes:
            activePoll.outcome = 2
        else:
            activePoll.outcome = 3
    else:
        # 2/3 supermajority
        if activePoll.yesVotes >= 2*activePoll.noVotes:
            activePoll.outcome = 1
        else:
            activePoll.outcome = 2
        # NB: A casting vote is not exercisable on a supermajority - Renton 2005, para 8.16

    activePoll.active = False
    activePoll.save()
    
    return redirect(f'/poll/{activePoll.id}/')

def pollInfo(request, pollId):
    try:
        poll = Poll.objects.filter(id = pollId)[0]
    except:
        raise Http404()

    allVotes = Vote.objects.filter(poll=poll)
    pollResults = calculateResults(poll)
    superadmin = True if request.user.is_authenticated and Delegate.objects.get(authClone=request.user).superadmin else False

    yetToVote = []
    if poll.repsOnly:
        allInstitutions = Institution.objects.exclude(name="N/A")
        for institution in allInstitutions:
            if len([i for i in allVotes if i.voter.institution == institution]) == 0:
                yetToVote.append(institution)

    return render(request, 'councilApp/pollInfo.html', {'poll':poll, 'superadmin':superadmin, 'allVotes':allVotes, 'pollResults':pollResults, 
        'sumResults':sum(pollResults[1:3]), 'yetToVote':yetToVote, 'active_tab':'poll'})

@login_required
def voteOnPoll(request, pollId):
    try:
        activePoll = Poll.objects.filter(id = pollId, active=True)[0]
    except:
        raise Http404()

    activeVoteHTMLIds = []

    delegate = Delegate.objects.get(authClone=request.user)
    delegateHasProxy = Proxy.objects.filter(voter=delegate, active=True)
    delegateProxy = delegateHasProxy[0] if delegateHasProxy else None
    delegateHasVote = Vote.objects.filter(voter=delegate, poll=activePoll)
    delegateVote = delegateHasVote[0] if delegateHasVote else None
    delegateInfo = {'delegate':delegate, 'delegateProxy':delegateProxy, 'delegateVote':delegateVote}
    if delegateVote:
        activeVoteHTMLIds.append(f"ownRadio_{delegateVote.vote}")

    proxies = Proxy.objects.filter(holder=delegate, active=True)

    proxiesInfo = []
    for proxyObj in proxies:
        proxyHasVote = Vote.objects.filter(proxy=proxyObj,poll=activePoll)
        proxyVote = proxyHasVote[0] if proxyHasVote else None
        if proxyVote:
            activeVoteHTMLIds.append(f"proxyRadio_{proxyVote.vote}_{proxyObj.id}")
        proxiesInfo.append({'proxyObj':proxyObj, 'proxyVote':proxyVote})

    HTMLIdsJSON = json.dumps(activeVoteHTMLIds, cls=DjangoJSONEncoder)

    return render(request, 'councilApp/vote.html', {'activePoll':activePoll, 'delegateInfo':delegateInfo, 'proxiesInfo':proxiesInfo,
        'active_tab':'vote'})

def ajaxGetCastVotes(request):
    try:
        pollId = request.GET.get('pollId', None)
        activePoll = Poll.objects.filter(id = pollId, active=True)[0]
        delegate = Delegate.objects.get(authClone=request.user)
    except:
        return JsonResponse({'raise404':True})

    activeVoteHTMLIds = []

    delegateHasProxy = Proxy.objects.filter(voter=delegate, active=True)
    delegateProxy = delegateHasProxy[0] if delegateHasProxy else None
    delegateHasVote = Vote.objects.filter(voter=delegate, poll=activePoll)
    delegateVote = delegateHasVote[0] if delegateHasVote else None
    if delegateVote:
        activeVoteHTMLIds.append(f"ownRadio_{delegateVote.vote}")

    proxies = Proxy.objects.filter(holder=delegate, active=True)
    for proxyObj in proxies:
        proxyHasVote = Vote.objects.filter(voter=proxyObj.voter, poll=activePoll)
        proxyVote = proxyHasVote[0] if proxyHasVote else None
        if proxyVote:
            activeVoteHTMLIds.append(f"proxyRadio_{proxyVote.vote}_{proxyObj.id}")

    data = {'raise404':False, 'activeVoteHTMLIds':activeVoteHTMLIds}
    return JsonResponse(data)

def ajaxSubmitVotes(request):
    try:
        pollId = request.GET.get('pollId', None)
        activePoll = Poll.objects.filter(id = pollId, active=True)[0]
        delegate = Delegate.objects.get(authClone=request.user)
        checkedIds = request.GET.getlist('checkedIds[]', None)
    except:
        return JsonResponse({'raise404':True})

    for HTMLId in checkedIds:
        splitId = HTMLId.split('_')
        if 'own' in splitId[0]:
            existingVotes = Vote.objects.filter(voter=delegate, poll=activePoll)
            thisVote = existingVotes[0] if existingVotes else Vote()
            thisVote.voter = delegate
            thisVote.proxy = None
            thisVote.voteWeight = delegate.institution.votesWeight if activePoll.weighted else 1
        elif 'proxy' in splitId[0]:
            proxyId = splitId[2]
            proxyObj = Proxy.objects.get(id=proxyId, active=True)
            existingVotes = Vote.objects.filter(voter=proxyObj.voter, poll=activePoll)
            thisVote = existingVotes[0] if existingVotes else Vote()
            thisVote.voter = proxyObj.voter
            thisVote.proxy = proxyObj
            thisVote.voteWeight = proxyObj.voter.institution.votesWeight if activePoll.weighted else 1
        else: 
            return JsonResponse({'raise404':True})

        thisVote.poll = activePoll
        thisVote.vote = int(splitId[1])
        thisVote.voteTime = timezone.now()
        thisVote.save()

    return JsonResponse({'raise404':False})

def agenda(request):
    # TODO: Cache the agenda
    
    with open('agenda.yaml', 'r') as f:
        agenda = yaml.load(f)
    
    return render(request, 'councilApp/agenda.html', {'active_tab':'agenda', 'agenda':agenda})

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
                return render(request, 'councilApp/login.html', {'loginForm':loginForm, 'wrong':True, 'active_tab':'login'})
            else:
                login(request, user)
                try:
                    return redirect(request.GET['next'])
                except:
                    return redirect('/')
    else:
        loginForm = LoginForm()

    return render(request, 'councilApp/login.html', {'loginForm':loginForm, 'wrong':False, 'active_tab':'login'})

def logoutCustom(request):
    logout(request)
    return redirect('/')
