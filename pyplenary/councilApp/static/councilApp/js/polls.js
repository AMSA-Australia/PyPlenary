$(".form-check").add("br")
$(".form-check").addClass("form-switch")
$(".form-group").append("<br>")

$('#check_reps').change(function(){
  if ($(this).is(':checked')) {
    $('#check_weighted').attr("disabled", false)
  } else {
    $('#check_weighted').prop("checked", false)
    $('#check_weighted').attr("disabled", true)
  }
});