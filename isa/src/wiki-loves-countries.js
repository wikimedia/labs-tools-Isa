
/*********** Get WikiLoves country list from campaign ID ***********/

// Get the categories for the campaign using internal /api
// Generate list of subcategory ajax requests, one for for each campaign category
// Run them asynchronously and track when all complete
// Each response is an array of subcategories
// When all ajax requests are complete, process the list to create a unique, combined list of countries

import {unique} from './utils';

var wikiLovesCountries = [],
    campaignCategories = []; // e.g. [{name: "Category:Images from Wiki Loves Love 2018", depth:2}, ...]

export function getWikiLovesCountries(campaignId, callback) {
   
    var countries = [];
    // find out which categories the campaign has
    $.getJSON("../api/get-campaign-categories?campaign=" + campaignId)
        .done( function(categories) {
        // add "Cateogry:" prefix
        campaignCategories = categories.map(function(element) {
            return {
                name: "Category:" + element.name,
                depth: element.depth
            }
        });

        // asynchronously get country subcategories for each campaign category found
        getSubcategoryAjaxRequests(campaignCategories, callback);
    })
        .fail( function(err) {
         console.log("error retrieving campaign categories", err);
         return false
     })
}

// generates array of all subcategory ajax requests to be made
function getSubcategoryAjaxRequests(categories, callback) {
    var subcategoryAjaxRequests = [];
    for (var i=0; i < categories.length; i++) {
        var categoryName = categories[i].name;
        var apiOptions = {
            action: 'query',
            list: 'categorymembers',
            cmtitle: categoryName,
            cmtype: 'subcat',
            cmlimit: 'max', // todo: this only gets up to 500 results, probably enough but add continue params if not
            format: 'json',
            origin: '*'
        };
        var ajaxRequest = $.ajax({
            type: 'GET',
            url: WIKI_URL + 'w/api.php',
            data: apiOptions
        })
        .done(function(response) {
            // next steps for each request can be added here, e.g. more results
        })
        .fail(function(err) {
            console.log("error retrieving subcategories", err);
            return false 
        })
        subcategoryAjaxRequests.push(ajaxRequest);
    }
    combineCountriesFromAjaxRequests(subcategoryAjaxRequests, callback);
}

// Combine results of multiple ajax requests to create unique list of countries
// Waits for success of all responses in the requests array
function combineCountriesFromAjaxRequests(requests, callback) {
    
    $.when.apply(null, requests).done(function() {
    // Runs when all of the requests have completed successfully
    // We now have one list of subcategories for each root category
    var hasUnknownCountry = false;
    for (var i=0; i < requests.length; i++) {
        // reduce each result object to subcategory name only
        var subcategories = requests[i].responseJSON.query.categorymembers.map(function(currentValue) {
            return currentValue.title;
        });

        // find the root category, which is in the same order as requests array;
        var campaignCategory = campaignCategories[i].name;

        // filter out subcategories that don't match WikiLoves country syntax
        var countries = subcategories.filter(function(currentCategory) { 
            if (currentCategory === campaignCategory + " with unknown country") hasUnknownCountry = true;
            return currentCategory.startsWith(campaignCategory + " in ")
                   
        })
        // remove the text before the country name
        countries = countries.map(function(currentSubcat) {
            return currentSubcat.replace(campaignCategory + " in ", "");
        })
        // append countries from this request to wikiLovesCountries array
        wikiLovesCountries = wikiLovesCountries.concat(countries);
    };

    // sort alphabetically and remove duplicate country names
    wikiLovesCountries = unique(wikiLovesCountries.sort());

    if (callback) callback({list: wikiLovesCountries, hasUnknownCountry: hasUnknownCountry});
    });
}