from django.conf import settings
from django.core.cache import caches
from django.http import JsonResponse, FileResponse, Http404, HttpResponse
from .models import *
import json
import string
import random
import csv
import zipfile
import yaml

from io import StringIO
import requests

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
            print(item)
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