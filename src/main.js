
/*********** All pages ***********/
// todo: use webpack instead of adding script to all pages

import {getUrlParameters} from './utils';

$(function () {
  $('[data-toggle="popover"]').popover()
});

$('#campaign_table').DataTable({
    responsive: true,
    columnDefs: [{
        responsivePriority: 1,
        targets: 0
    }, {
        responsivePriority: 2,
        targets: -1
    }]
});

$('#captions_lang_select_1').select2({
    tags: false
});
$('#captions_lang_select_2').select2({
    tags: false
});
$('#captions_lang_select_3').select2({
    tags: false
});
$('#captions_lang_select_4').select2({
    tags: false
});
$('#captions_lang_select_5').select2({
    tags: false
});
$('#captions_lang_select_6').select2({
    tags: false
});

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
