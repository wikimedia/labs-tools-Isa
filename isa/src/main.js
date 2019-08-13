/*********** All pages ***********/
// todo: use webpack instead of adding script to all pages

import {getUrlParameters} from './utils';

$(function () {
  $('[data-toggle="popover"]').popover()
});

// EXAMPLE: remove after testing!
console.log('Example js translation logged below, should change with language selection:')
console.log( __('You need to Login to update a campaign') ) 


/**********  SET THE LANGUAGE IN SESSION ***********/
function addLanguageToUrl(langCode) {
    var path = window.location.pathname;
    var parametersObject = getUrlParameters();
    parametersObject.lang = langCode; //will create or replace existing value
    window.location.search = '?' + $.param(parametersObject);
}

$("#language_select").change(function () {
    addLanguageToUrl($("#language_select").val());
});
