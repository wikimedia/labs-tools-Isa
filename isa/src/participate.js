
/*********** Participate page ***********/

import {ParticipationManager} from './participation-manager';
import {getImagesFromApi} from './category-members';
import {getUrlParameters, shuffle} from './utils';
import {generateGuid} from './guid-generator.js';

var i18nStrings = JSON.parse($('.hidden-i18n-text').text());

var campaignId = getCampaignId(),
    wikiLovesCountry = getWikiLovesCountry(),
    isWikiLovesCampaign = !!wikiLovesCountry, // todo: this should be read from get-campaign-categories api call
    isUserLoggedIn = false,
    editSession;

///////// Campaign images /////////

// Check if user is logged in
$.getJSON('../../api/login-test')
    .then(function(response) {
        isUserLoggedIn = response.is_logged_in;

        // Then get campaign categories and depth settings from the server
        return $.getJSON("../../api/get-campaign-categories?campaign=" + campaignId);
    })
    .then(function(categories) {
        // todo: if it's a wiki loves campaign with no country selected, set all depth = 1 (ignore category depth settings)

        // Add Category: prefix
        categories.forEach(function(category) {
            category.name = "Category:" + category.name;
        })

        if (isWikiLovesCampaign && wikiLovesCountry) {
            // Construct country subcategory for each campaign category

            var categoryEndString = (wikiLovesCountry === 'Unknown') ?
                ' with unknown country' :
                ' in ' + wikiLovesCountry;
            categories.forEach(function(category) {
                category.name += categoryEndString;
                category.depth = 0;
            })
        }

        // Get images in categories
        getImagesFromApi(categories, function(images) {
            // Now we have all images from processing each category with depth

            // Randomise image order
            shuffle(images);

            // Start a new editSession using the Participation Manager
            editSession = new ParticipationManager(images, campaignId, wikiLovesCountry, isUserLoggedIn);

            // Trigger image changed event to populate the page
            editSession.imageChanged();

            // Close loading overlay
            if (images.length > 0) {
                hideLoadingOverlay();
            } else {
                alert(i18nStrings["No images found for this campaign!"]);
                window.location.href = '../' + campaignId;
            }

            if (getUrlParameters().imageData) {
                var imageData = JSON.parse(decodeURIComponent(getUrlParameters().imageData));
                for (var i = 0; i < images.length; i++) {
                    if (images[i] === imageData.fileName) {
                        editSession.setImageIndex(i);

                        editSession.setDepictStatements(imageData.depicts);
                        editSession.setCaptions(imageData.captions);
                        
                        break;
                    }
                }
            }

            // Update image count for campaign on each edit session to keep updated with changes
            // Do not post when a WikiLoves country has been selected as this is a reduced list of images
            if (!wikiLovesCountry) postCampaignImageCount(images.length);
        })
    })
    .fail(function(err) {
        console.log("error retrieving campaign categories", err)
        alert(i18nStrings["Something went wrong getting campaign images"]);
        window.location.href = '../' + campaignId;
    })


///////// Depicts search box /////////

function searchResultsFormat(state) {
    if (!state.id) {
      return state.text;
    }
    var $state = $(
      '<span class="search-result-label">' + state.text + '</span> <br> <span class="search-result-description">' + state.description + '</span>'
    );
    return $state;
  }

(function setUpDepictsSearch(){
    $( '#depicts-select' ).select2( {
        placeholder: i18nStrings['Search for things you see in the image'],
        delay: 250,
        minimumResultsForSearch: 1,
        maximumSelectionLength: 4,
        ajax: {
            type: 'GET',
            dataType: 'json',
            url: function(t) {
                return '../../api/search-depicts/' + campaignId;
            }
        },
        templateResult: searchResultsFormat,
    });

    $('#depicts-select').on('select2:select', function(ev) {
        // Add new depict statement to the UI when user selects result
        var selected = ev.params.data;

        // Generate a new unique statement ID
        var statementId = generateStatementId(editSession.imageMediaId);

        editSession.addDepictStatement (
            selected.id,
            selected.text,
            selected.description,
            false /* isProminent */,
            statementId
        );
        if (editSession.machineVisionActive) {
            var suggestion = editSession.getDepictSuggestionByItem(selected.id);
            if (suggestion) suggestion.isAccepted = true;
            editSession.renderDepictSuggestions();
        }
        $(this).val(null).trigger('change');
    })
  })();

///////// Event handlers /////////

$('#expand-meta-data').click(function() {
    $('.image-desc').toggleClass('expand');

    if ($('.image-desc').hasClass('expand')) {
        // expanded
        var minimiseText = i18nStrings['minimise metadata from commons'];
        $('#expand-meta-data').html('<i class="fas fa-caret-up"></i>&nbsp; ' + minimiseText);
    } else {
        // collpased
        var maximiseText = i18nStrings['show all metadata from commons'];
        $('#expand-meta-data').html('<i class="fas fa-caret-down"></i>&nbsp; ' + maximiseText);
    }
})

$('.next-image-btn').click(function(ev) {
    editSession.nextImage();
})

$('.previous-image-btn').click(function(ev) {
    editSession.previousImage();
})

$('.caption-input').on('input', function() {
    editSession.captionDataChanged();
})

// Click to remove depicts tags
$('.depict-tag-group').on('click','.depict-tag-btn', function(ev) {
    if (editSession.machineVisionActive) {
        // Todo: move to new participation manager method
        var item = $(this).siblings('.label').children('.depict-tag-qvalue').text(); // todo: fix messy way to retreive item
        var suggestion = editSession.getDepictSuggestionByItem(item);
        if (suggestion) suggestion.isAccepted = false;
    }
    $(this).parents('.depict-tag-item').remove();
    editSession.depictDataChanged();
})

// Click to change isProminent for depicts tags
$('.depict-tag-group').on('click','.prominent-btn', function(ev) {
    $(this).toggleClass('active');
    editSession.depictDataChanged();
})

// Click to add Machine Vision depict suggestions
$('.depict-tag-suggestions').on('click','.depict-tag-suggestion', function(ev) {
    var item = $(this).find('.depict-tag-qvalue').text(); // todo: fix messy way to retreive item
    editSession.addDepictBySuggestionItem(item);
})

$('.edit-publish-btn-group').on('click', 'button', function() {
    var editType = $(this).parent().attr('edit-type');

    if ( $(this).hasClass('cancel-edits-btn') ) {
        if (editType === "depicts") {
            editSession.resetDepictStatements();
        }
        if (editType === "captions") {
            editSession.resetCaptions();
        }
    }

    if ( $(this).hasClass('publish-edits-btn') ) {
        editSession.postContribution(editType)
    }

})

function getCampaignId () {
    var parts = window.location.pathname.split("/");
    return parseInt(parts[parts.length - 2]);
}

function getWikiLovesCountry () {
    var country = getUrlParameters().country;
    return (country) ? decodeURIComponent(country) : '';
}

function populateCaption(language, text) {
    $('.caption-input[lang=' + language + ']').val(text);
}

function getUserLanguages() {
    var languages = []
    $('.caption-input').each(function() {
        languages.push( $(this).attr('lang'))
    })
    return languages
}

function generateStatementId(mediaId) {
    return mediaId + '$' + generateGuid();
}

function hideLoadingOverlay() {
    $('.loading').fadeOut('slow');
}

function postCampaignImageCount(imageCount) {
    $.post({
        url: '../../api/update-campaign-images/' + campaignId,
        data: JSON.stringify({campaign_images: imageCount}),
        contentType: 'application/json'
    }).done(function(response) {

    }).fail( function(error) {
        console.log("Error updating image count for campaign")
    })
}
