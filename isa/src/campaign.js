
/*********** Campaign page ***********/

import {getWikiLovesCountries} from './wiki-loves-countries';

// Use presence of dropdown to test for WikiLoves campaign
var isWikiLovesCampaign = $('#campaign_countries').length === 1;
    
// Generate country dropdown list for WikiLoves campaigns 
if (isWikiLovesCampaign) {
    getWikiLovesCountries(getCampaignId(), function(wikiLovesCountries) {
        // once response received, append options to the drop-down list in the UI
        console.log("callback fired", wikiLovesCountries)
        var options = '';
        for (var i=0; i < wikiLovesCountries.length; i++) {
            options += '<option value="'+ wikiLovesCountries[i] + '">' + wikiLovesCountries[i] + '</option>';
        }
        $('#campaign_countries').append(options);
    });
    
    // On selecting a country, append it to the participate URL
    $('#campaign_countries').on('change', function(event) {
        var selection = $(this).val();
        var path = window.location.pathname + '/participate';
        //only add country parameter to href when one has been selected
        var participateUrl = (selection === "all") ? path : path + '?country=' + selection;
        $('#get_started_btn').attr("href", participateUrl);
    })

    function getCampaignId () {
        // Get campaignId from last part of url path
        var urlPathParts = window.location.pathname.split("/");
        return urlPathParts[urlPathParts.length - 1];
    }
}


