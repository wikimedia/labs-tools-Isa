
/*********** Campaign page ***********/

var i18nStrings = JSON.parse($('.hidden-i18n-text').text());

// Use presence of dropdown to test for WikiLoves campaign
var isWikiLovesCampaign = $('#campaign_countries').length === 1;
    
// Generate country dropdown list for WikiLoves campaigns 
if (isWikiLovesCampaign) {
    
    // Append country to participate URL for Wiki-loves campaign
    $('#get_started_btn').on('click', function(event) {
        event.preventDefault();
        var selection = $('#campaign_countries').val();
        var path = $(this).attr('href');
        window.location.href = path + '?country=' + selection;
    })
}

