$(document).ready( function () {

    $( function() {
        $( '.selectpicker' ).selectpicker();
    } );

    function categorySearchResultsFormat(state) {
        if (!state.id) {
          return state.text;
        }
        var $state = $( '<span class="search-result-label">' + state.text + '</span>');
        return $state;
    }

    $( '#category-search' ).select2( {
        placeholder: 'Search for Categories here',
        delay: 250,
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
        templateResult: categorySearchResultsFormat,
    });
    
    $( '#category-search' ).on('select2:select', function(ev) {
        var category = $(this).val();
        addSelectedCategory(category);
        $(this).val(null).trigger('change'); // clear the search selection 
        $(this).select2("close"); // close the dropdown
    })
    
    // Main function to add the UI elements for a new category row
    // Used when category is added via search, or populating from existing campaign categories
    function addSelectedCategory(name, depth) {
        var depth = depth || 0;
        var shortName = name.replace("Category:","");
        $('#selected-categories-content').append(getCategoryRowHtml(shortName, depth))
        // show the table header if it's not visible already
        $('#selected-categories-header').show();
    } 
    
    // Click event for removing categories
    $('#selected-categories-content').on("click", "button.close", function(event) {
        // remove the .selected-category parent container the button is within
        $(this).closest(".selected-category").remove();
        
        //after removing the element, we must hide the table header if there are no rows left
       if ( $('.selected-category').length < 1 ) {
           $('#selected-categories-header').hide();
       }
    })
    
    // Returns the html for an individual category row, including depth option and remove button
    function getCategoryRowHtml(name, depth) {
        var depth = depth || 0;
        var nameHtml = '<td class="category-name">' + name + '</td>';
        var depthHtml = '<td> <input type="number" min="0" max="5" class="category-depth-input" value=' + depth + '> </td>';
        var buttonHtml = '<td> <button type="button" class="close" aria-label="Close"> <span aria-hidden="true"> × </span> </button> </td>';
        return '<tr class="selected-category">' + nameHtml + depthHtml + buttonHtml + '</tr>';
    }
    
    // Returns category data that can be submitted to the server
    function getJsonCategoryData() {
        var categoryData = [];
        $('.selected-category').each(function(index, element) {
            var name = $(element).find('.category-name').text();
            var depth = $(element).find('.category-depth-input').val();
            categoryData.push({
                name: name,
                depth: depth
            })
        })
        return JSON.stringify(categoryData);
    }

    $('form').submit(function(event, data) {
        $('#categories-data')[0].value = getJsonCategoryData();
    })
    
});