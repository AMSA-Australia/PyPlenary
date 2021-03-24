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
from django.core.cache import caches
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
    on_list = Speaker.objects.filter(delegate=request.user.delegate).exists()
    return render(request, 'councilApp/speaker_list.html', {'active_tab':'speaker_list', 'on_list':on_list})

@login_required
def ajaxSpeakerAdd(request):
    # FIXME: Acquire lock to prevent race conditions

    Speaker.objects.filter(delegate=request.user.delegate).delete()

    if request.GET['action'] == 'remove':
        speakers = [s.to_json() for s in Speaker.objects.all()]
        async_to_sync(channel_layer.group_send)('speakerlist', {'type': 'speakerlist_updated', 'speakerlist': speakers})
        return HttpResponse()

    speaker = Speaker()
    speaker.delegate = request.user.delegate
    speaker.index = (Speaker.objects.all().aggregate(Max('index'))['index__max'] or 0) + 1

    if request.GET['action'] == 'add':
        speaker.point_of_order = False
    elif request.GET['action'] == 'point_order':
        speaker.point_of_order = True
    else:
        return HttpResponseBadRequest('Unknown action')

    speaker.save()

    speakers = [s.to_json() for s in Speaker.objects.all()]
    async_to_sync(channel_layer.group_send)('speakerlist', {'type': 'speakerlist_updated', 'speakerlist': speakers})
    return HttpResponse()

def delegates(request):
    if request.user.is_authenticated:
        allDelegates = [request.user.delegate] + list(Delegate.objects.exclude(authClone=request.user).order_by('speakerNum'))
    else:
        allDelegates = Delegate.objects.order_by('speakerNum')
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
    if not request.user.delegate.superadmin:
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

def agenda(request):
    # Check cache for agenda
    cache1 = caches['default']
    cached_agenda = cache1.get('agenda')
    if cached_agenda is None or request.GET.get('refresh', '0') == '1':
        cached_agenda = yaml.load(requests.get(settings.PYPLENARY_AGENDA_URI).text)
        cache1.set('agenda', cached_agenda, timeout=None)

    return render(request, 'councilApp/councilInfo/agenda.html', {'active_tab':'agenda', 'active_tab2': 'info', 'agenda':cached_agenda})

def reports(request):
    cache1 = caches['default']
    cached_reports = cache1.get('reports')
    if cached_reports is None or request.GET.get('refresh', '0') == '1':
        cached_reports = yaml.load(requests.get(settings.PYPLENARY_REPORTS_URI).text)
        cache1.set('reports', cached_reports, timeout=None)

    return render(request, 'councilApp/councilInfo/reports.html', {'active_tab':'reports', 'active_tab2': 'info', 'allGroups':cached_reports})

def socials(request):
    cache1 = caches['default']
    cached_socials = cache1.get('socials')
    if cached_socials is None or request.GET.get('refresh', '0') == '1':
        cached_socials = yaml.load(requests.get(settings.PYPLENARY_SOCIALS_URI).text)
        cache1.set('socials', cached_socials, timeout=None)

    return render(request, 'councilApp/councilInfo/socials.html', {'active_tab':'socials', 'active_tab2': 'info', 'allCities':cached_socials})

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
                return render(request, 'councilApp/authTemplates/login.html', {'loginForm':loginForm, 'wrong':True, 'active_tab':'login'})
            else:
                login(request, user)
                try:
                    return redirect(request.GET['next'])
                except:
                    return redirect('/')
    else:
        loginForm = LoginForm()

    return render(request, 'councilApp/authTemplates/login.html', {'loginForm':loginForm, 'wrong':False, 'active_tab':'login'})

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
                return render(request, 'councilApp/authTemplates/requestChange.html', {'emailForm':emailForm, 'done':True})
            
            user = userList[0]

            for oldToken in ResetToken.objects.filter(user=user):
                oldToken.active = False
                oldToken.save()

            token = generateToken()
            while len(ResetToken.objects.filter(token=token)) > 0:
                token = generateToken()
            ResetToken.objects.create(token = token, user = user, active=True)

            try:
                resetLink = f'{settings.WEB_DOMAIN}/password_reset/{token}'
                subject = 'Council Webapp Password Change Request'
                html_message = render_to_string('councilApp/authTemplates/passwordEmail.html', {'domain':settings.WEB_DOMAIN, 'resetLink':resetLink})
                plain_message = strip_tags(html_message)
                email_from = 'AMSA Council Webmaster'

                send_mail(subject, plain_message, email_from, [email], html_message=html_message)

                return render(request, 'councilApp/authTemplates/requestChange.html', {'emailForm':emailForm, 'done':True})

            except:
                return render(request, 'councilApp/authTemplates/requestChange.html', {'emailForm':emailForm, 'done':True})
    else:
        emailForm = PasswordChangeEmail()
    
    return render(request, 'councilApp/authTemplates/requestChange.html', {'emailForm':emailForm, 'done':False})


def passwordReset(request, token):
    logout(request)
    try:
        tokenObj = ResetToken.objects.get(token=token)
        user = tokenObj.user
        if not tokenObj.active:
            return render(request, 'councilApp/authTemplates/passwordReset.html', {'linkExpired':True, 'done':False})
    except:
        return render(request, 'councilApp/authTemplates/passwordReset.html', {'linkExpired':True, 'done':False})

    if request.method == 'POST':
        changeForm = SetPasswordForm(user, request.POST)
        if changeForm.is_valid():
            changeForm.save()
            tokenObj.active = False
            tokenObj.save()
            return render(request, 'councilApp/authTemplates/passwordReset.html', {'linkExpired':False, 'done':True})
    else:
        changeForm = SetPasswordForm(user)

    return render(request, 'councilApp/authTemplates/passwordReset.html', {'changeForm':changeForm, 'linkExpired':False, 'done':False, 'user':user})

def regoRequest(request):
    if not settings.REGO_OPEN:
        return render(request, 'councilApp/authTemplates/noRego.html', {'active_tab':'registration'})

    logout(request)
    if request.method == 'POST':
        regoForm = RegoForm(request.POST)

        if regoForm.is_valid():

            [email, name, institution, role, pronouns, firstTime] = [regoForm.cleaned_data.get('email').lower(),
                regoForm.cleaned_data.get('name'),
                regoForm.cleaned_data.get('institution'),
                regoForm.cleaned_data.get('role'),
                regoForm.cleaned_data.get('pronouns'),
                regoForm.cleaned_data.get('firstTime'),]

            role = role if role else 'Delegate'

            if User.objects.filter(username=email):
                return render(request, 'councilApp/authTemplates/rego.html', {'regoForm':None, 'email':None, 'done':True, 'error':1, 'active_tab':'registration'})

            for oldToken in PendingRego.objects.filter(email=email):
                oldToken.active = False
                oldToken.save()

            token = generateToken()
            while len(PendingRego.objects.filter(token=token)) > 0:
                token = generateToken()
            PendingRego.objects.create(token=token, email=email, name=name, institution=institution, role=role, pronouns=pronouns, firstTime=firstTime)

            try:
                activateLink = f'{settings.WEB_DOMAIN}/activate/{token}'
                subject = 'Council Webapp Acccount Activation'
                html_message = render_to_string('councilApp/authTemplates/activationEmail.html', {'activateLink':activateLink, 'name':name})
                plain_message = strip_tags(html_message)
                email_from = 'AMSA Council Webmaster'

                send_mail(subject, plain_message, email_from, [email], html_message=html_message)

                return render(request, 'councilApp/authTemplates/rego.html', {'regoForm':None, 'email':email, 'done':True, 'error':0, 'active_tab':'registration'})

            except:
                return render(request, 'councilApp/authTemplates/rego.html', {'regoForm':None, 'email':None, 'done':True, 'error':2, 'active_tab':'registration'})
    else:
        regoForm = RegoForm()
    
    return render(request, 'councilApp/authTemplates/rego.html', {'regoForm':regoForm, 'email':None, 'done':False, 'error':0, 'active_tab':'registration'})

def regoSetPassword(request, token):
    logout(request)
    try:
        tokenObj = PendingRego.objects.get(token=token)
        if not tokenObj.active:
            return render(request, 'councilApp/authTemplates/regoPassword.html', {'error':2, 'done':False})
    except:
        return render(request, 'councilApp/authTemplates/regoPassword.html', {'error':1, 'done':False})

    if not User.objects.filter(username=tokenObj.email):
        user = User.objects.create(username=tokenObj.email, password=os.environ.get('USER_TEMP_PASSWORD'), email=tokenObj.email)
    else:
        user = User.objects.get(username=tokenObj.email)

    if request.method == 'POST':
        pwdForm = SetPasswordForm(user, request.POST)
        if pwdForm.is_valid():
            pwdForm.save()

            Delegate.objects.create(
                authClone=user,
                name=tokenObj.name,
                email=tokenObj.email,
                institution=tokenObj.institution,
                role=tokenObj.role,
                speakerNum=max([i.speakerNum for i in Delegate.objects.all()])+1,
                pronouns=tokenObj.pronouns,
                first_time=tokenObj.firstTime)

            tokenObj.active = False
            tokenObj.save()

            return render(request, 'councilApp/authTemplates/regoPassword.html', {'error':0,  'done':True})
    else:
        pwdForm = SetPasswordForm(user)

    return render(request, 'councilApp/authTemplates/regoPassword.html', {'pwdForm':pwdForm, 'email':tokenObj.email, 'error':0, 'done':False})

@login_required
def profile(request):
    user = request.user
    delegate = request.user.delegate
    done = False
    emailChanged = False

    changeDetailForm = RegoForm({
        'name': delegate.name,
        'email': delegate.email,
        'institution': delegate.institution,
        'role': delegate.role,
        'pronouns': delegate.pronouns,
        'firstTime': delegate.first_time})

    if request.method == 'POST':
        changeDetailForm = RegoForm(request.POST)

        if changeDetailForm.is_valid():
            email = changeDetailForm.cleaned_data.get('email').lower()

            if email != user.username:
                if User.objects.filter(username=email):
                    return render(request, 'councilApp/profile.html', {'changeDetailForm':changeDetailForm, 'error':1, 'active_tab':'profile'})
                [delegate.email, user.username, user.email] = [email, email, email]
                emailChanged = True

            [delegate.email, delegate.name, delegate.institution, delegate.role, delegate.pronouns, delegate.first_time] = [
                email,
                changeDetailForm.cleaned_data.get('name'),
                changeDetailForm.cleaned_data.get('institution'),
                changeDetailForm.cleaned_data.get('role'),
                changeDetailForm.cleaned_data.get('pronouns'),
                changeDetailForm.cleaned_data.get('firstTime'),]

            delegate.role = delegate.role if delegate.role else 'Delegate'

            delegate.save()
            user.save()

            done = True

    return render(request, 'councilApp/profile.html', {'changeDetailForm':changeDetailForm, 'emailChanged': emailChanged, 'done':done, 'error':0, 'active_tab':'profile'})

@login_required
def passwordResetLoggedIn(request):
    user = request.user
    if request.method == 'POST':
        changeForm = SetPasswordForm(user, request.POST)
        if changeForm.is_valid():
            changeForm.save()
            return render(request, 'councilApp/authTemplates/passwordResetLoggedIn.html', {'done':True})
    else:
        changeForm = SetPasswordForm(user)

    return render(request, 'councilApp/authTemplates/passwordResetLoggedIn.html', {'changeForm':changeForm, 'done':False, 'user':user})

def loaderio_token(request):
    return HttpResponse('loaderio-' + settings.LOADERIO_TOKEN, content_type='text/plain')
