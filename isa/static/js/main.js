$(document).ready( function () {
    $( '#campaign_table' ).DataTable();
    
    $( '#campaign_table' ).css( {
        'width' : '1050px',
        'margin-top':'20px'
    } );

    $( 'input[ type = "search" ] ' ).css( {
        'float': 'right',
        'width': '800px'
    } );

    $( '.pagination' ).css(
        {
            'border' : '0.5px solid black'
        }
    );

    $( '.paginate_button' ).css(
        { 'border-right' : '0.5px solid black' }
    );

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

        
    function getUrlParameters () {
        var parametersObject = {};
        var parameters = window.location.search.substr(1);
        if (parameters == "") return {};
        parameters = parameters.split('&');
        for (var i = 0; i < parameters.length; i++) {
            var splitParameters = parameters[i].split("=");
            parametersObject[ splitParameters[0] ] = splitParameters[1];
        }
        return parametersObject;
    }

    function addLanguageToUrl(langCode) {  
        var path = window.location.pathname;
        var parametersObject = getUrlParameters();
        parametersObject.lang = langCode; //will create or replace existing value
        window.location.search = '?' + $.param(parametersObject);
    }

    $("#language_select").change( function () {
        addLanguageToUrl($("#language_select").val()); 
    });

});