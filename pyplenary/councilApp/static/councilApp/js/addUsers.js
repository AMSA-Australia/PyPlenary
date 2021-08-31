var failedSendCSVArr = [];
var logStr = '';

var form = document.getElementById("CSVUploadForm");
function handleForm(event) { event.preventDefault(); } 
form.addEventListener('submit', handleForm);

function submitCSVForm() {
  document.getElementById("CSVFileUploadErrorMessage").style.display = "none";
  var CSVFileUploadBox = document.getElementById("CSVFileUploadBox");
  if (CSVFileUploadBox.files.length == 1) {
    var csvFile = CSVFileUploadBox.files[0];
    if (csvFile['name'].substring(csvFile['name'].length-4, csvFile['name'].length) != '.csv') {
      document.getElementById("CSVFileUploadErrorMessage").style.display = "block";
      return (alert("Error: please ensure you upload a valid CSV file!"));
    }
  }
  else {
    document.getElementById("CSVFileUploadErrorMessage").style.display = "block";
    return (alert("Error: please ensure you upload a valid CSV file!"));
  }

  // on new upload, clear all previous stuff
  var data = null;
  var liveLog = document.getElementById("liveLog");
  liveLog.innerHTML = ''
  var logMsg = document.createElement("samp");
  logMsg.textContent = '...Uploading users...';
  liveLog.appendChild(logMsg);
  document.getElementById("uploadSpinner").style.display = "block";
  document.getElementById("downloadBtns").style.display = "none";
  failedSendCSVArr = [];
  logStr = '';

  // parse uploaded CSV
  Papa.parse(csvFile, {
        delimiter: ',',
        header: true,
        skipEmptyLines: true,
        complete: function (results) {
          papaParseSuccess(results, document.getElementById("reissueInviteCheck").checked);
        }
  }); 
}

function papaParseSuccess(results, reissue) {
  document.getElementById("uploadLogContainer").style.display = "block";
  var totalToAdd = results.data.length;
  var curAdded = 0;
  for (var i = 0; i < totalToAdd; i++) {
    // ajax send every field
    $.ajax({
      url: '/ajax/addOneUser/',
      data: {
        'userInfo': JSON.stringify(results.data[i]),
        'reissue': reissue,
      },
      dataType: 'json',
      success: function (data) {
        var liveLog = document.getElementById("liveLog");
        var logMsg = document.createElement("samp");
        console.log(data)
        if (data.result.errorCode) {
          if (data.result.errorCode == 'Duplicate') {
            logMsg.innerHTML = `DUPLICATE: Invitation already exists for ${data.result.name} (${data.result.inst}) at ${data.result.email}.<br>`;
            logStr = logStr + logMsg.innerHTML
          }
          else {
            logMsg.innerHTML = `ERROR: Invitation not sent to ${data.result.name} (${data.result.inst}) at ${data.result.email}.<br>&emsp;&emsp;&emsp;&emsp;ERROR CODE: ${data.result.errorCode}.<br>&emsp;&emsp;&emsp;&emsp;ERROR MESSSAGE: ${data.result.errorMsg}<br>`;
            logStr = logStr + logMsg.innerHTML
            failedSendCSVArr.push(data.result.account)
          }
        } else {
          logMsg.innerHTML = `SUCCESSFULLY sent invitation to ${data.result.name} (${data.result.inst}) at ${data.result.email}.<br>`;
          logStr = logStr + logMsg.innerHTML
        }
        liveLog.removeChild(liveLog.lastChild);
        liveLog.appendChild(logMsg);
        var logMsg2 = document.createElement("samp");
        logMsg2.innerHTML = '...Uploading users...';
        liveLog.appendChild(logMsg2);

        curAdded++;
        if (curAdded >= totalToAdd) {finishAdding(totalToAdd);}
      },
      failure: function (data) {
        logMsg.innerHTML = `ERROR: Invitation not sent to ${results.data[i]['Name']} (${results.data[i]['Institution']}) at ${results.data[i]['Email']}.<br>&emsp;&emsp;&emsp;&emsp;ERROR CODE: Unknown Error.<br>&emsp;&emsp;&emsp;&emsp;ERROR MESSSAGE: <br>`;
        logStr = logStr + logMsg.innerHTML;
        failedSendCSVArr.push(results.data[i]);

        liveLog.removeChild(liveLog.lastChild);
        liveLog.appendChild(logMsg);
        var logMsg2 = document.createElement("samp");
        logMsg2.innerHTML = '...Uploading users...';
        liveLog.appendChild(logMsg2);

        curAdded++;
        if (curAdded >= totalToAdd) {finishAdding(totalToAdd);}
      }
    });
  }
}

function finishAdding(totalToAdd) {
  var liveLog = document.getElementById("liveLog");
  liveLog.removeChild(liveLog.lastChild);
  var logMsg = document.createElement("samp");
  logMsg.textContent = '...FINISHED uploading users...';
  liveLog.appendChild(logMsg);
  document.getElementById("uploadSpinner").style.display = "none";
  document.getElementById("downloadBtns").style.display = "block";
}

function downloadReviewCSV () {
  var x = Papa.unparse(failedSendCSVArr, {
        delimiter: ',',
        complete: function (results) {
          console.log(results)
        }
  }); 
  download('failed_sends.csv', x)
}

function downloadLogTxt () {
  var x = logStr.replaceAll('<br>','\n');
  download('add_user_log.txt', x)
}

