
/*********** Participate page ***********/

import {ParticipationManager} from './participation-manager';
import {getImagesFromApi} from './category-members';
import {getUrlParameters} from './utils';
import {generateGuid} from './guid-generator.js';

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
            categories.forEach(function(category) {
                category.name += ' in ' + wikiLovesCountry;
                category.depth = 0;
            })
        }

        // Get images in categories 
        getImagesFromApi(categories, function(images) {
            // Now we have all images from processing each category with depth
            // Start a new editSession using the Participation Manager
            console.log("Images retrieved!", images.length)
            editSession = new ParticipationManager(images, campaignId, wikiLovesCountry, isUserLoggedIn);

            // Trigger image changed event to populate the page
            editSession.imageChanged();
           
            // Close loading overlay
            if (images.length > 0) {
                hideLoadingOverlay();
            } else {
                alert(gettext("No images found for this campaign!"));
                window.location.href = '../' + campaignId;
            }
            
            // Update image count for campaign on each edit session to keep updated with changes
            // Do not post when a WikiLoves country has been selected as this is a reduced list of images
            if (!wikiLovesCountry) postCampaignImageCount(images.length);
        })
    })
    .fail(function(err) {
        console.log("error retrieving campaign categories", err)
        alert(gettext("Something went wrong getting campaign images"));
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
          placeholder: gettext('Search for things you see in the image'),
          delay: 250,
          minimumResultsForSearch: 1,
          maximumSelectionLength: 4,
          ajax: {
              type: 'GET',
              dataType:'json',
              url: 'https://www.wikidata.org/w/api.php',
              data: function (params) {
                  var query = {
                      search: params.term,
                      action: 'wbsearchentities',
                      language: 'en',
                      format: 'json',
                      uselang: 'en',
                      origin: '*'
                  };
                  return query;
              },
              processResults: function (data) {
                  var processedResults = [],
                      results = data.search;
                  for (var i=0; i < results.length; i++) {
                      var result = results[i];
                      processedResults.push({
                          id: result.id,
                          text: result.label || "(no label)",
                          description: result.description || "" //use "" as default to avoid 'undefined' showing as description
                      });
                  }
                  return {
                      results: processedResults
                  };
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
        $(this).val(null).trigger('change');
    })
  })();

///////// Event handlers /////////

$('#expand-meta-data').click(function() {
    $('.image-desc').toggleClass('expand');

    if ($('.image-desc').hasClass('expand')) {
        // expanded
        var minimiseText = gettext('minimise metadata from commons');
        $('#expand-meta-data').html('<i class="fas fa-caret-up"></i>&nbsp; ' + minimiseText);
    } else {
        // collpased
        var maximiseText = gettext('show all metadata from commons');
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
    $(this).parents('.depict-tag-item').remove();
    editSession.depictDataChanged();
})

// Click to change isProminent for depicts tags
$('.depict-tag-group').on('click','.prominent-btn', function(ev) {
    $(this).toggleClass('active');
    editSession.depictDataChanged();
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
