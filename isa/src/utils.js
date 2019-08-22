
/*********** Utilities for any page  ***********/

export function getUrlParameters () {
    var parametersObject = {};
    var parameters = window.location.search.substr(1);
    if (parameters == "") return {};
    parameters = parameters.split('&');
    for (var i = 0; i < parameters.length; i++) {
        var splitParameters = parameters[i].split('=');
        parametersObject[ splitParameters[0] ] = splitParameters[1];
    }
    return parametersObject;
};

// Get unique values from array
export function unique(array) {
    var seen = {};
    return array.filter(function (item) {
        return seen.hasOwnProperty(item) ? false : (seen[item] = true);
    });
}

// Displays flash messages with fade in/out effect
// Needs one element for each type to exist in HTML (e.g. danger, success)
// Content is replaced when message is shown
var visibleFlashType,
    flashTimer;

export function flashMessage(type, content) {
    // prevent timeout close from previously open message of same type
    if (visibleFlashType === type) {
        clearTimeout(flashTimer);
    }
    var flashSelector = '.isa-flash-message.alert-' + type;
    $(flashSelector).html(content);
    $(flashSelector).slideDown().addClass('show');
    visibleFlashType = type;
    flashTimer = setTimeout(function() {
        $(flashSelector).slideUp().removeClass('show');
        visibleFlashType = undefined;
    }, 4000);
}


export function shuffle(array) {
    var m = array.length, t, i;
  
    // While there remain elements to shuffle…
    while (m) {
  
      // Pick a remaining element…
      i = Math.floor(Math.random() * m--);
  
      // And swap it with the current element.
      t = array[m];
      array[m] = array[i];
      array[i] = t;
    }
  
    return array;
  }

  export function getHtmlStripped(string) {
    return $('<span>' + string + '</span>').text()
  }

  export function truncate(input, charLimit) {
      charLimit = charLimit || 18;
      if (input.length > charLimit) {
          return input.substring(0,charLimit) + '...';
      }
      // else
      return input;
 };