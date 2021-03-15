from django.http import JsonResponse, FileResponse, Http404, HttpResponse
from .models import *
import json

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