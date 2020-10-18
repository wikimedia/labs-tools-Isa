
/*********** Campaign page ***********/

import {getWikiLovesCountries} from './wiki-loves-countries';

var i18nStrings = JSON.parse($('.hidden-i18n-text').text());

// Use presence of dropdown to test for WikiLoves campaign
var isWikiLovesCampaign = $('#campaign_countries').length === 1;
    
// Generate country dropdown list for WikiLoves campaigns 
if (isWikiLovesCampaign) {
    
    getWikiLovesCountries(getCampaignId(), function(wikiLovesCountries) {
        // once response received, append options to the drop-down list in the UI
        var options = '';

        // if the "unknown country" category exists, make it the first <option>
        if (wikiLovesCountries.hasUnknownCountry) {
            options += '<option value="Unknown" selected>' + i18nStrings['Unknown country'] + '</option>';
        }

        for (var i=0; i < wikiLovesCountries.list.length; i++) {
            var countryOption = wikiLovesCountries.list[i];
            var selected = '';
            if (i === 0 && !wikiLovesCountries.hasUnknownCountry) selected = 'selected';
            options += '<option value="'+ countryOption + '" ' + selected + '>' + countryOption + '</option>';
        }
        $('#campaign_countries').html(options);

        // 'get started' button is disabled initially for WikiLoves campaign
        // Re-enable now WikiLovesCountries have been found
        $('#get_started_btn').removeClass('disabled');
    
    })
    // Append country to participate URL for Wiki-loves campaign
    $('#get_started_btn').on('click', function(event) {
        event.preventDefault();
        var selection = $('#campaign_countries').val();
        var path = $(this).attr('href');
        window.location.href = path + '?country=' + selection;
    })
}

// Get campaignId from last part of url path
function getCampaignId () {
    var urlPathParts = window.location.pathname.split("/");
    return urlPathParts[urlPathParts.length - 1];
}



