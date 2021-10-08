from django.conf import settings
from django.core import mail
from django.core.mail import send_mail
from django.core.cache import caches
from django.core.exceptions import ValidationError
from django.http import JsonResponse, FileResponse, Http404, HttpResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import *

import csv
from io import StringIO
import json
import os
import random
import requests
import string
import yaml
import zipfile

def readConfigYAMLFromHTML(fileURL):
    x = yaml.safe_load(requests.get(fileURL).text)
    return x

def eligibleToVote(delegate, poll):
    if poll.repsOnly:
        if delegate is not None and delegate.rep:
            return True
        else:
            proxies = Proxy.objects.filter(holder = delegate, active=True)
            for i in proxies:
                if i.voter.rep:
                    return True
            return False
    return True

def bad_request(status, message):
    response = HttpResponse(json.dumps({'message': message}), 
        content_type='application/json')
    response.status_code = status
    return response

def calculateResults(poll):
    votesInPoll = Vote.objects.filter(poll = poll)
    yesVotes = sum([i.voteWeight for i in votesInPoll if i.vote == 1])
    noVotes = sum([i.voteWeight for i in votesInPoll if i.vote == 2])
    abstainVotes = sum([i.voteWeight for i in votesInPoll if i.vote == 0])
    return (abstainVotes, yesVotes, noVotes)

def generateToken():
    choice = string.ascii_lowercase + string.ascii_uppercase + string.digits
    token = ''
    for i in range(64):
        token += random.choice(choice)
    return token

def generateSpeakerListCSV(request):
    speakersIO = StringIO()
    writer = csv.writer(speakersIO)
    writer.writerow(['Speaker #', 'Name', 'Role', 'Institution', 'Pronouns'])
    for delegate in sorted(Delegate.objects.all(), key = lambda x:x.speakerNum):
        writer.writerow([delegate.speakerNum, delegate.name, delegate.role, delegate.institution.shortName, delegate.pronouns])

    pollsIO = StringIO()
    writer = csv.writer(pollsIO)
    writer.writerow(['Motion', 'Time concluded', 'Result', 'Votes for', 'Votes against', 'Abstentions', 'All votes for', 'All votes against', 'All abstentions'])
    resultDict = {0:'N/A',1:'Carried',2:'Lost',3:'Tied'}
    for poll in sorted(Poll.objects.all(), key = lambda x:x.endTime):
        allVotes = Vote.objects.filter(poll=poll)
        toWrite = [poll.title, poll.endTime, resultDict[poll.outcome], poll.yesVotes, poll.noVotes, poll.abstainVotes]
        toWrite.append("; ".join([f'{vote.voter.name} ({vote.voter.institution.shortName})' for vote in allVotes if vote.vote == 1]))
        toWrite.append("; ".join([f'{vote.voter.name} ({vote.voter.institution.shortName})' for vote in allVotes if vote.vote == 2]))
        toWrite.append("; ".join([f'{vote.voter.name} ({vote.voter.institution.shortName})' for vote in allVotes if vote.vote == 0]))
        writer.writerow(toWrite)

    agendaIO = StringIO()
    writer = csv.writer(agendaIO)
    writer.writerow(['Day', 'Time', 'Item'])
    cached_agenda = yaml.load(requests.get(settings.PYPLENARY_AGENDA_URI).text)
    for day, items in cached_agenda.items():
        for item in items:
            writer.writerow([day, 
                item['time'] if 'time' in item else '', 
                item['title'] if 'title' in item else ''])

    reportsIO = StringIO()
    writer = csv.writer(reportsIO)
    writer.writerow(['Group', 'Position', 'Name', 'Report link'])
    cached_reports = yaml.load(requests.get(settings.PYPLENARY_REPORTS_URI).text)
    for group in cached_reports:
        for report in group['reports']:
            writer.writerow([group['name'] if 'name' in group else '', 
                report['position'] if 'position' in report else '', 
                report['name'] if 'name' in report else '', 
                report['URL'] if 'URL' in report else ''])

    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=councilAppData.zip'

    z = zipfile.ZipFile(response,'w') 
    z.writestr("speakerList.csv", speakersIO.getvalue())
    z.writestr("polls.csv", pollsIO.getvalue())
    z.writestr("agenda.csv", agendaIO.getvalue())
    z.writestr("reports.csv", reportsIO.getvalue())
    z.close()

    return response

def addUserFromJSON(account, forceResend = False):
    try:
        account = dict(account)
        toReturn = {'success':False, 'errorCode':'',  'errorMsg':'',
            'name':account['Name'], 'email':account['Email'], 'inst':'', 'account':account}
        print(account)

        instNameLower = [(i.name.lower(), i.id) for i in Institution.objects.all()] + [(i.shortName.lower(), i.id) for i in Institution.objects.all()]

        institution = None
        for i in instNameLower:
            if account['Institution'].lower() == i[0]:
                institution = Institution.objects.get(id=i[1])
                toReturn['inst'] = institution.shortName
                break
        if not institution:
            toReturn['errorCode'] = 'Invalid Institution'
            toReturn['errorMsg'] = f"{account['Institution']} is an invalid institution"
            return toReturn
        
        [email, name, institution, role, pronouns, firstTime] = [''.join(account['Email'].lower().split()),
            account['Name'],
            institution,
            account['Role'] if account['Role'] else 'Delegate',
            account['Pronouns'],
            account['First time'] in ("1", 1, True, "Yes", "yes", "YES", "True", "true", "TRUE"),]
        
        if not name or not email:
            toReturn['errorCode'] = 'Missing Name Or Email'
            return toReturn

        if User.objects.filter(username=email):
            toReturn['errorCode'] = 'Account Already Created'
            return toReturn

        if not forceResend:
            if PendingRego.objects.filter(email=email, active=True):
                toReturn['errorCode'] = 'Duplicate'
                return toReturn

        for oldToken in PendingRego.objects.filter(email=email):
            oldToken.active = False
            oldToken.save()

        token = generateToken()
        while PendingRego.objects.filter(token=token):
            token = generateToken()

    except:
        toReturn['errorCode'] = 'Unknown Error'
        return toReturn
    
    try:
        activateLink = f'https://council.amsa.org.au/activate/{token}'
        subject = f'[ACTION REQUIRED] Webapp Acccount Activation, {settings.CUSTOM_CONFIGS["PYPLENARY_SITE_NAME"]}'
        html_message = render_to_string('councilApp/adminToolTemplates/emailTemplate.html', {'activateLink':activateLink, 'name':name})
        plain_message = strip_tags(html_message)
        email_from = 'AMSA Council Webmaster'
        send_mail(subject, plain_message, email_from, [email], html_message=html_message)
        PendingRego.objects.create(token=token, email=email, name=name, institution=institution, role=role, pronouns=pronouns, firstTime=firstTime)
        
        toReturn['success'] = True

    except:
        toReturn['errorCode'] = 'Email Error'
        toReturn['errorMsg'] = 'An error occurred when attempting to email an invitation.'
        return toReturn

    return toReturn
