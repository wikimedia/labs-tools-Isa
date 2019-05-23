$(document).ready( function () {
    $( '.selectpicker' ).selectpicker();
    function categorySearchResultsFormat(state) {
        if (!state.id) {
          return state.text;
        }
        var $state = $( '<span class="search-result-label">' + state.text + '</span>');
        return $state;
    }

    $( '#categories_select_options' ).select2( {
        placeholder: 'Search for Categories here',
        delay: 250,
        tags: true,
        multiple: true,
        tokenSeparators: [','],
        minimumResultsForSearch: 1,
        ajax: {
            type: 'GET',
                dataType:'json',
                url: 'https://commons.wikimedia.org/w/api.php',
                data: function (params) {
                    var query = {
                        search: params.term,
                        action: 'opensearch',
                        namespace: 14,
                        format: 'json',
                        origin: '*'
                    }
                    return query
                },
                processResults: function (data) {
                    var processedResults = [],
                        results = data[1];
                    for (var i=0; i < results.length; i++) {
                        var result = results[i];
                        console.log(result);
                        processedResults.push({
                            id: result,
                            text: result
                        });
                    }
                    return {
                        results: processedResults
                    };
                }
            },
        templateResult: categorySearchResultsFormat
    });
});