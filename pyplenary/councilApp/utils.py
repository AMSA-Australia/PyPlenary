def eligibleToVote(delegate, poll):
	if poll.repsOnly:
		if delegate is not None and delegate.rep:
			return True
		else:
			return False
	return True