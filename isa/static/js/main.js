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
    
    /*********** Get WikiLoves country list for dropdown ***********/
    
    // Get the categories for the campaign using internal /api
    // Generate list of subcategory ajax requests, one for for each campaign category
    // Run them asynchronously and track when all complete
    // Each response is an array of subcategories
    // When all ajax requests are complete, process the list to create a unique, combined list of countries
   
    var isWikiLovesCampaign = $('#campaign_countries').length === 1; //dropdown only exists on WikiLoves campaign
    var wikiLovesCountries = [];
    var campaignCategories = []; // e.g. [{name: "Category:Images from Wiki Loves Love 2018", depth:2}, ...]
    var campaignId = "";
    
    // Get campaignId from last part of url path
    var urlPathParts = window.location.pathname.split("/");
    campaignId = urlPathParts[urlPathParts.length - 1];
    
    //only if it's a WikiLoves campaign, extract the country list
    if (isWikiLovesCampaign) {
        updateWikiLovesCountries();
    }
    
    function updateWikiLovesCountries() {
        var countries = [];
        //find out which categories the campaign has
        $.getJSON("../../api/get-campaign-categories?campaign=" + campaignId)
            .done( function(response) {
            return response.categories;
        })
            .then( function(data) {
            //asynchronously get country subcategories for each campaign category found
            campaignCategories = data.categories;
            getSubcategoryAjaxRequests(campaignCategories);
         })
            .fail( function() {
             console.log("no category data found for campaign_id = ", campaignId);
             return false
         })
    }
    
    // generates array of all subcategory ajax requests to be made
    function getSubcategoryAjaxRequests(categories) {
        var subcategoryAjaxRequests = [];
        for (var i=0; i < categories.length; i++) {
            var categoryName = categories[i].name;
            var apiOptions = {
                action: 'query',
                list: 'categorymembers',
                cmtitle: categoryName,
                cmtype: 'subcat',
                cmlimit: 'max', //todo: this only gets up to 500 results, add continue params and logic for the rest
                format: 'json',
                origin: '*'
            };
            var ajaxRequest = $.ajax({
                type: 'GET',
                url: 'https://commons.wikimedia.org/w/api.php',
                data: apiOptions
            })
                .done(function(response) {
                   //next steps for each request can be added here, e.g. more results
                });
            
            subcategoryAjaxRequests.push(ajaxRequest);
        }
        
        combineCountriesFromAjaxRequests(subcategoryAjaxRequests);
    }
    
    // Combine results of multiple ajax requests to create unique list of countries
    // Waits for success of all responses in the requests array
    function combineCountriesFromAjaxRequests(requests) {
        $.when.apply(null, requests).done(function() {
        //Runs when all of the requests have completed successfully
        //We now have one list of subcategories for each root category
        
        for (var i=0; i < requests.length; i++) {
            //reduce each result object to subcategory name only
            var subcategories = requests[i].responseJSON.query.categorymembers.map(function(currentValue) {
                return currentValue.title;
            });
            //find the root category, which is in the same order as requests array;
            var campaignCategory = campaignCategories[i].name.replace(/_/g," "); //
            //filter out subcategories that don't match WikiLoves country syntax
            var countries = subcategories.filter(function(currentCategory) { 
                return currentCategory.startsWith(campaignCategory + " in ");
            })
            //remove the text before the country name
            countries = countries.map(function(currentSubcat) {
                return currentSubcat.replace(campaignCategory + " in ", "");
            })
            //append countries from this request to wikiLovesCountries array
            wikiLovesCountries = wikiLovesCountries.concat(countries);
        };
            //sort alphabetically and remove duplicate country names
            wikiLovesCountries = uniqe(wikiLovesCountries.sort());
            
            //append options to the drop-down list in the UI
            var option = '';
            for (var i=0;i<wikiLovesCountries.length;i++){
                option += '<option value="'+ wikiLovesCountries[i] + '">' + wikiLovesCountries[i] + '</option>';
            }
            $('#campaign_countries').append(option);   
            
        });
    }
    
    // On selecting a country, append it to the participate URL
    $('#campaign_countries').on('change', function(event) {
        var selection = $(this).val();
        var path = window.location.pathname;
        //only add country parameter to href when one has been selected
        var participateUrl = (selection === "all") ? path : path + '?country=' + selection;
        $('#get_started_btn').attr("href", participateUrl);
    })
    
    /*********** Utils ***********/
    
    //get unique values from array
    function uniqe(array) {
        var seen = {};
        return array.filter(function (item) {
            return seen.hasOwnProperty(item) ? false : (seen[item] = true);
        });
    }

});