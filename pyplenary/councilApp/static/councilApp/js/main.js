function searchDelegateTable() {
  // Declare variables
  var input, filter,  searchTerms, table, tr, td, i, j, k, trElements, txtValue, toDisplay, fulfilled;
  input = document.getElementById("delegateSearchInput");
  filter = input.value.toUpperCase();
  searchTerms = filter.split(/\s+/);
  table = document.getElementById("delegateTable");
  tr = table.getElementsByTagName("tr");

  // Loop through all table rows, and hide those who don't match the search query
  for (i = 1; i < tr.length; i++) {
    trElements = tr[i].getElementsByTagName("td")

    allFulfilled = true;
    for (j = 0; j < searchTerms.length; j++) {
      fulfilled = false;
      for (k = 0; k < trElements.length; k++) {
        td = trElements[k];
        if (td) {
          txtValue = td.textContent || td.innerText;
          if (txtValue.toUpperCase().indexOf(searchTerms[j]) > -1) {
            fulfilled = true;
            break
          }
        }
      }
      if (!fulfilled) {
        allFulfilled = false;
        break
      }
    }
    if (allFulfilled) {
      tr[i].style.display = "";
    } else {
      tr[i].style.display = "none";
    }
  }
}
