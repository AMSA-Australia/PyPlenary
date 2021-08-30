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

  console.log(csvFile);

  Papa.parse(csvFile, {
        delimiter: ',',
        header: true,
        skipEmptyLines: true,
        complete: function (results) {
          var data = results;
          console.log(data);
        }
    });
}