function getActiveVotes(pollId) {
  $.ajax({
    url: '/ajax/getActiveVotes/',
    data: {
      'pollId':pollId
    },
    dataType: 'json',
    success: function (data) {
      if (data.raise404) {
        alert('An error occurred when fetching cast votes.');
      } else {
        toggleOn(data.activeVoteHTMLIds);
      }
    },
    error: function (data) {
      alert('An error occurred when fetching cast votes. Please refresh the page.');
    }
  });
};

function toggleOn(alreadyVoted) {
  for (var i = 0; i < alreadyVoted.length; i++) {
    console.log(alreadyVoted[i]);
    var toCheck = document.getElementById(alreadyVoted[i]);
    if (toCheck){
      toCheck.checked = true;
    }
  }
}

function voteSubmit(pollId) {
  var allCheckedRadios = $('input[type=radio]:checked');
  var checkedIds = [];
  for (var i = 0; i < allCheckedRadios.length; i++) {
    checkedIds.push(allCheckedRadios[i].id);
  }
  console.log(checkedIds)

  $.ajax({
    url: '/ajax/submitVotes/',
    data: {
      'pollId':pollId,
      'checkedIds': checkedIds
    },
    dataType: 'json',
    success: function (data) {
      if (data.raise404) {
        alert('lfmao');
      } else {
        if(!alert('Votes successfully recorded.')){window.location.replace("/poll/");;}
      }
    },
    error: function () {
      alert('An error occurred when submitting votes. Please refresh the page.');
    }
  });
}