/*
 * Some Basic javascript for the freeside member portal.
 */

function validateEmail(field, alertText) {
  var atPos = field.value.indexOf("@");
  var dotPos = field.value.lastIndexOf(".");
  if (atPos < 1 || dotPos - atPos < 2) {
    window.alert(alertText);
    return false;
  } else {
    return true;
  }
}

function checkProfileForm(formData) {
  with (formData) {
    window.console.log(formData);
    if (newpass.value != newpassrepeat.value) {
      window.alert("New passwords don't match");
      newpass.value = "";
      newpassrepeat.value = "";
      newpass.focus();
      return false;
    }

    if (validateEmail(email, "Not a valid email address.") == false) {
      email.focus();
      return false;
    }
  }
}
