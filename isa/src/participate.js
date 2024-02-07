/*********** Participate page ***********/

import {ParticipationManager} from './participation-manager';
import {getUrlParameters, shuffle, flashMessage} from './utils';
import {generateGuid} from './guid-generator.js';

var i18nStrings = JSON.parse($('.hidden-i18n-text').text());

var campaignId = getCampaignId(),
    wikiLovesCountry = getWikiLovesCountry(),
    isWikiLovesCampaign = !!wikiLovesCountry, // todo: this should be read from get-campaign-categories api call
    isUserLoggedIn = false,
    csrf_token = "{{ csrf_token() }}",
    editSession;

///////// Campaign images /////////

// Check if user is logged in
$.getJSON('../../api/login-test')
    .then(function(response) {
        isUserLoggedIn = response.is_logged_in;
    })
    .then(function() {
        // todo: if it's a wiki loves campaign with no country selected, set all depth = 1 (ignore category depth settings)

        var imagesUrl = '../../campaigns/' + campaignId + "/images";
        if (isWikiLovesCampaign && wikiLovesCountry) {
            imagesUrl += "/" + wikiLovesCountry;
        }

        // Get images in categories
        $.get(imagesUrl).done(function(images) {
            // Now we have all images from processing each category with depth

            // Randomise image order
            shuffle(images);

            // Start a new editSession using the Participation Manager
            editSession = new ParticipationManager(images, campaignId, wikiLovesCountry, isUserLoggedIn);

            if (getUrlParameters().image) {
                var image = Number.parseInt(getUrlParameters().image);
                var imageIndex = images.indexOf(image);
                if (imageIndex !== -1) {
                    editSession.setImageIndex(imageIndex);
                }
            } else {
                // Trigger image changed event to populate the page
                editSession.imageChanged();
            }

            // Close loading overlay
            if (images.length > 0) {
                hideLoadingOverlay();
            } else {
                alert(i18nStrings["No images found for this campaign!"]);
                window.location.href = '../' + campaignId;
            }

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
    var $label = $("<span>")
        .addClass("search-result-label")
        .text(state.text);
    var $description = $("<span>")
        .addClass("search-result-description")
        .text(state.description);
    var $state = $("<div>").append(
        $label,
        $("<br>"),
        $description
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

///////// Rejecting statements /////////

function rejectStatement(item, element){
    var rejectedSuggestion = editSession.getDepictSuggestionByItem(item);
    var rejectedSuggestionData = JSON.stringify({
        file: editSession.imageFileName,
        campaign_id: getCampaignId(),
        depict_item: item,
        google_vision: rejectedSuggestion.google_vision || null,
        google_vision_confidence: rejectedSuggestion.confidence.google || null,
        metadata_to_concept: rejectedSuggestion.metadata_to_concept || null,
        metadata_to_concept_confidence: rejectedSuggestion.confidence.metadata_to_concept || null,
    });

    var conformRemoveMessageHead = i18nStrings['Are you sure you want to reject this suggestion?'],
        conformRemoveMessageExplain = i18nStrings['Are you sure explanation for reject suggestion'];

    if (confirm(conformRemoveMessageHead + "\n\n" + conformRemoveMessageExplain)) {
        $.post({
            url: '/api/reject-suggestion',
            data: rejectedSuggestionData,
            contentType: 'application/json',
            headers: {
                "X-CSRFToken": csrf_token,
            },
        }).done(function(response) {
            // Contribution accepted by server, we can remove suggestion from list
            rejectedSuggestion.isRejectedByUser = true;
            editSession.renderDepictSuggestions();
            flashMessage('success', i18nStrings['Suggestion removed from list']);
        }).fail( function(error) {
            flashMessage('danger', i18nStrings['Oops! Suggestion might not have been removed'])
        });
    }
}

///////// Event handlers /////////

$('#expand-meta-data').click(function() {
    $('.image-desc').toggleClass('expand');

    if ($('.image-desc').hasClass('expand')) {
        // expanded
        var minimiseText = i18nStrings['minimise metadata from Commons'];
        $('#expand-meta-data').html('<i class="fas fa-caret-up"></i>&nbsp; ' + minimiseText);
    } else {
        // collpased
        var maximiseText = i18nStrings['show all metadata from Commons'];
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

$('#depict-tag-suggestions-container').on('click', '.accept-depict', function() {
    var item = $(this).siblings('.depict-tag-qvalue').text();
    editSession.addDepictBySuggestionItem(item);
});

function displayModal(item, label, confidence){
    $('.modal-label-link').text(label);
    $('.modal-label-link').attr('href', 'https://www.wikidata.org/wiki/' + item);
    $('.modal-item').text(item);
    $('.modal-confidence').text(confidence);
    $('.modal').show();
    $('#depict-tag-suggestions-container').addClass('blur')
}

function clearModal(){
    $('.modal').hide();
    $('#depict-tag-suggestions-container').removeClass('blur');
}

$('.depict-tag-suggestions').on('click', '.depict-tag-suggestion', function(e){
    if (!editSession.isMobile) return;
    var suggestion = $(this);
    var item = suggestion.find('.depict-tag-qvalue').text();
    var label = suggestion.find('.depict-tag-label-text').text();
    var confidence = suggestion.find('.depict-tag-confidence').text();
    displayModal(item, label, confidence);
});

$('.modal').on('click', '.close-modal', function(){
   clearModal();
});

function getItemFromModal(){
    return $('.modal-item').text();
}

$('.modal').on('click', '.accept-depict-mobile', function(){
    var item = getItemFromModal();
    editSession.addDepictBySuggestionItem(item);
    clearModal();
});

$('.modal').on('click', '.reject-depict-mobile', function(){
    var item = getItemFromModal();
    rejectStatement(item, $(this));
    clearModal()
});

$('#depict-tag-suggestions-container').on('click', '.reject-depict', function() {
    var item = $(this).siblings('.depict-tag-qvalue').text();
    rejectStatement(item, $(this)); 
});


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

// Toggle display of suggested items
$("#suggest-toggle").click(function () {
    var toggleIndicator = $('#toggle-indicator'),
        toggleLabel = $('#toggle-label'),
        suggestionCntainer = $('.depict-tag-suggestions'),
        hideText = i18nStrings['Hide Suggestions'],
        showText = i18nStrings['Show Suggestions'];

    suggestionCntainer.toggleClass('collapsed');
    if(suggestionCntainer.hasClass('collapsed')){
        toggleIndicator.removeClass('fa-caret-up');
        toggleIndicator.addClass('fa-caret-down');
        toggleLabel.text(showText)
    }else{
        toggleIndicator.removeClass('fa-caret-down');
        toggleIndicator.addClass('fa-caret-up');
        toggleLabel.text(hideText)
    }
});