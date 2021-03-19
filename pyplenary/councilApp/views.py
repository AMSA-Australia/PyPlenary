import json
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core import mail
from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Max
from django.forms import formset_factory, ValidationError
from django.http import JsonResponse, FileResponse, Http404, HttpResponse, HttpResponseBadRequest
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
import requests

os.chdir(settings.BASE_DIR) # For loading agenda.yaml, etc.

channel_layer = get_channel_layer()

def index(request):
    return render(request, 'councilApp/index.html', {'active_tab':'index'})

@login_required
def speakerList(request):
    speakers = Speaker.objects.all()
    on_list = Speaker.objects.filter(delegate=request.user.delegate).exists()
    return render(request, 'councilApp/speaker_list.html', {'active_tab':'speaker_list', 'speakers':speakers,
        'on_list':on_list})

@login_required
def speakerListInner(request):
    speakers = Speaker.objects.all()
    return render(request, 'councilApp/speaker_list_inner.html', {'speakers':speakers})

@login_required
def speakerAdd(request):
    # FIXME: Acquire lock to prevent race conditions

    Speaker.objects.filter(delegate=request.user.delegate).delete()

    if request.POST['action'] == 'remove':
        async_to_sync(channel_layer.group_send)('speakerlist', {'type': 'speakerlist_updated'})
        return redirect('/speaker_list/')

    speaker = Speaker()
    speaker.delegate = request.user.delegate
    speaker.index = (Speaker.objects.all().aggregate(Max('index'))['index__max'] or 0) + 1

    if request.POST['action'] == 'add':
        speaker.point_of_order = False
    elif request.POST['action'] == 'point_order':
        speaker.point_of_order = True
    else:
        return HttpResponseBadRequest('Unknown action')

    speaker.save()

    async_to_sync(channel_layer.group_send)('speakerlist', {'type': 'speakerlist_updated'})
    return redirect('/speaker_list/')

def delegates(request):
    allDelegates = sorted(Delegate.objects.all(), key=lambda x:x.speakerNum)
    return render(request, 'councilApp/delegates.html', {'allDelegates':allDelegates, 
        'active_tab':'delegates'})

@login_required
def proxy(request):
    delegate = request.user.delegate

    proxiesForMe = Proxy.objects.filter(voter=delegate, active=True)
    proxiesIHold = Proxy.objects.filter(holder=delegate, active=True)

    allDelegates = sorted(Delegate.objects.exclude(id=delegate.id), key=lambda x:x.speakerNum)

    return render(request, 'councilApp/proxy.html', {'delegate':delegate, 'proxiesForMe':proxiesForMe, 'proxiesIHold':proxiesIHold,
        'allDelegates':allDelegates, 'active_tab':'proxy'})

def proxyNominate(request):
    try:
        delegate = request.user.delegate
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
        delegate = request.user.delegate
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
        delegate = request.user.delegate
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
    delegate = request.user.delegate if request.user.is_authenticated else None
    superadmin = delegate.superadmin if delegate is not None else False
    rep = delegate.rep if delegate is not None else False
    activePolls = [i for i in allPolls if i.active and eligibleToVote(delegate, i)]
    return render(request, 'councilApp/poll.html', {'allPolls':allPolls, 'superadmin':superadmin, 'rep':rep, 'activePolls':activePolls,
        'active_tab':'poll'})

@login_required
def createPoll(request):
    if not request.user.delegate:
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
    if not request.user.delegate.superadmin:
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
    superadmin = True if request.user.is_authenticated and request.user.delegate.superadmin else False

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

    delegate = request.user.delegate
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
        delegate = request.user.delegate
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
        delegate = request.user.delegate
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

cached_agenda = None

def agenda(request):
    global cached_agenda
    if cached_agenda is None:
        cached_agenda = yaml.load(requests.get(settings.PYPLENARY_AGENDA_URI).text)

    return render(request, 'councilApp/agenda.html', {'active_tab':'agenda', 'agenda':cached_agenda})

def loginCustom(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        loginForm = LoginForm(request.POST)
        if loginForm.is_valid():
            username = loginForm.cleaned_data.get('username').lower()
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

def passwordResetLinkRequest(request):
    logout(request)
    if request.method == 'POST':
        emailForm = PasswordChangeEmail(request.POST)
        if emailForm.is_valid():
            email = emailForm.cleaned_data.get('email').lower()

            userList = User.objects.filter(email=email)

            if len(userList) == 0:
                return render(request, 'councilApp/password/requestChange.html', {'emailForm':emailForm, 'done':True})
            
            user = userList[0]

            for oldToken in ResetToken.objects.filter(user=user):
                oldToken.active = False
                oldToken.save()

            token = generateToken()
            while len(ResetToken.objects.filter(token=token)) > 0:
                token = generateToken()
            ResetToken.objects.create(token = token, user = user)

            try:
                resetLink = f'{settings.WEB_DOMAIN}/password_reset/{token}'
                subject = 'Council Webapp Password Change Request'
                html_message = render_to_string('councilApp/password/passwordEmail.html', {'domain':settings.WEB_DOMAIN, 'resetLink':resetLink})
                plain_message = strip_tags(html_message)
                email_from = 'AMSA Council Webmaster'

                send_mail(subject, plain_message, email_from, [email], html_message=html_message)

                return render(request, 'councilApp/password/requestChange.html', {'emailForm':emailForm, 'done':True})

            except:
                return render(request, 'councilApp/password/requestChange.html', {'emailForm':emailForm, 'done':True})
    else:
        emailForm = PasswordChangeEmail()
    
    return render(request, 'councilApp/password/requestChange.html', {'emailForm':emailForm, 'done':False})


def passwordReset(request, token):
    logout(request)
    try:
        tokenObj = ResetToken.objects.get(token=token)
        user = tokenObj.user
        if not tokenObj.active:
            return render(request, 'councilApp/password/passwordReset.html', {'linkExpired':True, 'done':False})
    except:
        return render(request, 'councilApp/password/passwordReset.html', {'linkExpired':True, 'done':False})

    if request.method == 'POST':
        changeForm = SetPasswordForm(user, request.POST)
        if changeForm.is_valid():
            changeForm.save()
            tokenObj.active = False
            tokenObj.save()
            return render(request, 'councilApp/password/passwordReset.html', {'linkExpired':False, 'done':True})
    else:
        changeForm = SetPasswordForm(user)

    return render(request, 'councilApp/password/passwordReset.html', {'changeForm':changeForm, 'linkExpired':False, 'done':False, 'user':user})

def profile(request):
    return render(request, 'councilApp/profile.html', {'active_tab':'profile'})
