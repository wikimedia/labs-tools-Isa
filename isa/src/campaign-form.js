import {getImagesFromApi} from './category-members';

var isWikiLovesCampaign = $('#campaign_type')[0].checked;
var categoriesAreValid = false;

$('#start_date_datepicker').attr({'data-toggle': 'datetimepicker', 'data-target': '#start_date_datepicker'});
$('#start_date_datepicker').datetimepicker({
    format: 'YYYY-MM-DD',
    useCurrent: false
});

$('#end_date_datepicker').attr({'data-toggle': 'datetimepicker', 'data-target': '#end_date_datepicker'});
$('#end_date_datepicker').datetimepicker({
    format: 'YYYY-MM-DD',
    useCurrent: false
});

// Populate existing categories in the UI if data present in hidden field (on update route)
var initialCategoryData = $('#categories-data').val();
if ( initialCategoryData ) {
    var categories = JSON.parse(initialCategoryData);
    for (var i=0; i < categories.length; i++) {
        addSelectedCategory(categories[i].name, categories[i].depth);
    }
}

// Setup category search box
function categorySearchResultsFormat(state) {
    if (!state.id) {
      return state.text;
    }
    var $state = $( '<span class="search-result-label">' + state.text + '</span>');
    return $state;
}

$( '#category-search' ).select2( {
    placeholder: '',
    delay: 250,
    minimumResultsForSearch: 1,
    ajax: {
        type: 'GET',
            dataType:'json',
            url: WIKI_URL + 'w/api.php',
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
    if (isWikiLovesCampaign) validateWikiLovesCategories();
}

// Click event for removing categories
$('#selected-categories-content').on("click", "button.close", function(event) {
    // remove the .selected-category parent container the button is within
    $(this).closest(".selected-category").remove();

    if (isWikiLovesCampaign) validateWikiLovesCategories();

    // after removing the element, we must hide the table header if there are no rows left
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
function getCategoryData() {
    var categoryData = [];
    $('.selected-category').each(function(index, element) {
        var name = $(element).find('.category-name').text();
        var depth = $(element).find('.category-depth-input').val();
        categoryData.push({
            name: name,
            depth: depth
        })
    })
    return categoryData;
}

// Check if each category in the UI has the correct syntax for Wiki Loves campaign
// Add class to show valid/ivalid with green/red border
function validateWikiLovesCategories() {
    var hasValidationErrors = false;
    var isValid;
    $('.selected-category').each(function() {
        isValid = validateWikiLovesCategory(this);
        if (!isValid) hasValidationErrors = true;
    })

    if (hasValidationErrors) {
        $('.invalid-wiki-loves-warning').show();
    } else {
        $('.invalid-wiki-loves-warning').hide();
    }
    categoriesAreValid = !hasValidationErrors;
}

function validateWikiLovesCategory(element) {
    var categoryName = $(element).find('.category-name').text();
    var isValid = isValidWikiLovesSyntax(categoryName);
    if (isValid) {
        $(element).removeClass('invalid-category').addClass('valid-category');
    } else {
        $(element).removeClass('valid-category').addClass('invalid-category');
    }
    return isValid;
}

function isValidWikiLovesSyntax(categoryName) {
    var syntaxReg = /Images from Wiki Loves [A-Za-z]* \d{4}$/;
    return syntaxReg.test(categoryName);
}

function clearWikiLovesValidation() {
    $('.selected-category').each(function() {
        $(this).removeClass('invalid-category').removeClass('valid-category');
        $('.invalid-wiki-loves-warning').hide();
    })
}

//////////// Form submission ////////////

// Using click instead of submit event, as this triggers form validation
// Submit event is fired manually once categories have been checked
// Once categories confirmed checked or unchanged, refire the submit click
// but this time continue with default submit bahaviour
// Also continue with default submit if form is invalid to trigger browser warnings
// Todo: Setup custom validation for all fields as separate function
var categoriesChecked = false,
    formIsValid = false;
$('#submit').click(function(ev) {

    // Checks the simple "required" form fileds
    formIsValid = $('form')[0].checkValidity();

    if (!categoriesChecked && formIsValid) {
        // Prevent form submission if categories not checked yet
        ev.preventDefault();
        var categorySelections = getCategoryData();

        if (categorySelections.length === 0) {
            return alert(gettext('You must select at least one category for your campaign.'));
        }
        if (isWikiLovesCampaign && !categoriesAreValid) {
            return alert(gettext('Some of the categories you have chosen do not have the correct syntax for a Wiki Loves Campaign.') + '\n' +
                gettext('Please check your selections and try again.'));
        }

        var metadataTypesAreValid = $.makeArray($('.metadata-type-checkbox')).some(function(element) {
            return element.checked;
        })
        if (!metadataTypesAreValid) return alert(gettext('Please select at least one type from the "Metadata to collect" section'));

        var finalCategoryData = $('#categories-data')[0].value = JSON.stringify(categorySelections);

        if (finalCategoryData !== initialCategoryData) {
            // Categories are newly added or have changed
            // Show "checking categories" notice
            $('#category-checking-notice').removeClass("d-none");

            // Add Category: prefix
            categorySelections.forEach(function(category) {
                category.name = "Category:" + category.name;
            })

            getImagesFromApi(categorySelections, function(images) {
                $('#campaign-image-count')[0].value = images.length;
                categoriesChecked = true;

                // Re-submit form now image count has been added to form
                $('#submit').click();
            })
        } else {
            // No change to category selections
            categoriesChecked = true;
            $('#submit').click();
        }
    }
    // Categories checked, continue default submit, OR
    // Form is invalid, default submit to show browser warnings
})


$('#campaign_type').on("change", function() {
    isWikiLovesCampaign = this.checked;

    if (isWikiLovesCampaign) {
        validateWikiLovesCategories();
    } else {
        clearWikiLovesValidation();
    }
})
