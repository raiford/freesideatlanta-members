/*
Some Basic javascript for the freeside member portal.
*/

function validate_email(field,alerttxt)
{
with (field)
  {
  apos=value.indexOf("@");
  dotpos=value.lastIndexOf(".");
  if (apos<1||dotpos-apos<2)
    {alert(alerttxt);return false;}
  else {return true;}
  }
}

function checkProfileForm(formdata)
{
with (formdata)
  {
  if (newpass.value!=newpassrepeat.value)
    {
    alert("New passwords don't match");
    newpass.value="";
    newpassrepeat.value="";
    newpass.focus();
    return false;
    }
  if(validate_email(email,"Not a valid email address.")==false)
    {
    email.focus();
    return false;
    }
  }
}
