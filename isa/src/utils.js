
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
