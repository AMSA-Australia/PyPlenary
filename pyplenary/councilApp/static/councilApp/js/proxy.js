function nominateProxyAJAX(candidateId) {
  $.ajax({
    url: '/ajax/nominateProxy/',
    data: {
      'candidateId': candidateId
    },
    dataType: 'json',
    success: function (data) {
      if (data.raise404) {
        if(!alert('An error occurred.')){window.location.reload();}
      } else {
        if(!alert('Proxy successfully assigned.')){window.location.reload();}
      }
    },
    failure: function (data) {
      if(!alert('An error occurred.')){window.location.reload();}
    }
  });
};

function retractProxyAJAX(candidateId) {
  $.ajax({
    url: '/ajax/retractProxy/',
    data: {},
    dataType: 'json',
    success: function (data) {
      if (data.raise404) {
        if(!alert('An error occurred.')){window.location.reload();}
      } else {
        if(!alert('Proxy successfully retracted.')){window.location.reload();}
      }
    },
    failure: function (data) {
      if(!alert('An error occurred.')){window.location.reload();}
    }
  });
};

function resignProxyAJAX(proxyId) {
  $.ajax({
    url: '/ajax/resignProxy/',
    data: {
      'proxyId': proxyId
    },
    dataType: 'json',
    success: function (data) {
      if (data.raise404) {
        if(!alert('An error occurred.')){window.location.reload();}
      } else {
        if(!alert('Proxy successfully relinquished.')){window.location.reload();}
      }
    },
    failure: function (data) {
      if(!alert('An error occurred.')){window.location.reload();}
    }
  });
};