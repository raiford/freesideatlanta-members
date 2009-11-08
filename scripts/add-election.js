goog.require('goog.dom');
goog.require('goog.ui.InputDatePicker');

(function() {
  var pattern = "MM'/'dd'/'yyyy";
  var formatter = new goog.i18n.DateTimeFormat(pattern);
  var parser = new goog.i18n.DateTimeParse(pattern);

  var inputs = ['nomination_start', 'nomination_end', 'vote_start', 'vote_end'];
  for (var i = 0; i < inputs.length; i++) {
    var inputEl = goog.dom.$(inputs[i]);
    if (inputEl) {
      var idp = new goog.ui.InputDatePicker(formatter, parser);
      idp.decorate(inputEl);
    }
  }
 })();
