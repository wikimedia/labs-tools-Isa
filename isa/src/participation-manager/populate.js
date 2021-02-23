/*********** Data populating functions ***********/

// Get data about an image and populate HTML elements on the page

import {ParticipationManager} from './base';
import {getHtmlStripped, truncate} from '../utils';

ParticipationManager.prototype.populateMetadata = function(filename) {
    var apiOptions = {
        action: 'query',
        titles: filename,
        prop: 'imageinfo',
        iiprop: 'extmetadata',
        format: 'json',
        formatversion: 2,
        origin: '*'
    };

    $.ajax( {
        type: 'GET',
        url: WIKI_URL + 'w/api.php',
        data: apiOptions
    } )
    .done( function( response ) {
        var metadata = response.query.pages[0].imageinfo[0].extmetadata,
        title = response.query.pages[0].title,
        escapedTitle = encodeURIComponent(title),
        description = (metadata.ImageDescription) ? getHtmlStripped(metadata.ImageDescription.value) : '',
        author = (metadata.Artist) ? getHtmlStripped(metadata.Artist.value) : '',
        credit = (metadata.Credit) ? getHtmlStripped(metadata.Credit.value) : '',
        license = (metadata.LicenseShortName) ? metadata.LicenseShortName.value : '',
        cameraLocationHtml = '(unknown)',
        lat = metadata.GPSLatitude,
        long = metadata.GPSLongitude;

        if (lat && long) {
            var locationUrl = 'https://www.openstreetmap.org/?mlat=' + lat.value + '&mlon=' + long.value,
                locationText = lat.value + ', ' + long.value;
            cameraLocationHtml = '<a href=' + locationUrl + '>' + locationText + '</a>';
        }

        // Spacing between categories
        var categories = metadata.Categories.value.replace(/\|/g,' | ');

        // Main metadata elements
        $('#image_name').html('<a href=' + WIKI_URL + 'wiki/' + escapedTitle + ' target="_blank">' + title.replace("File:", "") + '</a>');
        $('#image_description').text(description);
        $('#image_categories').text(categories);
        $('#image_camera_location').html(cameraLocationHtml);

        // Metadata elements floating inset within the image
        $('#image_author').text(truncate(author));
        $('#image_credit').text(truncate(credit));
        $('#image_license').text(truncate(license));

    } );
}

ParticipationManager.prototype.populateStructuredData = function(filename, callbacks) {
    var me = this;
    $('.depict-tag-group').empty(); //clear previous
    var entitiesApiOptions = {
        action: 'wbgetentities',
        titles: filename,
        // sites = 'commonswiki' not supported on test-commons
        // but any supported wiki option chosen will still retrieve the image (strangely!)
        sites: (WIKI_URL === "https://test-commons.wikimedia.org/") ? 'enwiki' : 'commonswiki',
        format: 'json',
        origin: '*'
    };
    $.ajax( {
        type: 'GET',
        url: WIKI_URL + 'w/api.php',
        data: entitiesApiOptions
    } ).done( function( response ) {
        // store imageMediaId for access within ParticipationManager
        var mediaId = me.imageMediaId = Object.keys(response.entities)[0];
        me.imageRevId = response.entities[mediaId].lastrevid;
        var mediaStatements = response.entities[mediaId].statements || {};
        var mediaCaptions = response.entities[mediaId].labels || {};
        var depictItems = [];
        var captions = [];

        // process captions
        var userCaptionLanguages = getCaptionLanguages();
        for (var i=0; i < userCaptionLanguages.length; i++) {
            var userLang = userCaptionLanguages[i];
            var caption = mediaCaptions[userLang];
            if (caption) {
                captions.push(caption);
                populateCaption(userLang, caption.value)
            } else {
                populateCaption(userLang, "")
            }
        }

        // process statements
        if ( mediaStatements.P180 ) {
            // convert results to array of {item, isProminent} objects
            depictItems = mediaStatements.P180.map(function(depictStatement) {
                return {
                    item: depictStatement.mainsnak.datavalue.value.id,
                    isProminent: depictStatement.rank === "preferred",
                    statementId: depictStatement.id
                }
            });
        } else {
            //todo: add message to statements container
            //console.log("this item has no depicts statements yet")
        }

        // run callback now that data has been retreived
        if (callbacks.onInitialDataReady) callbacks.onInitialDataReady(depictItems, captions);

        if (depictItems.length === 0) {
            // fire the UiRendered event now and return as there are no items to get labels for
            if (callbacks.onUiRendered) callbacks.onUiRendered();
            return;
        }
        // now make another call to Wikidata to get the labels for each depcits item
        var qvalues = depictItems.map(function(statement) {
            return statement.item;
        });
        var secondApiOptions = {
            action: 'wbgetentities',
            props: 'labels|descriptions',
            format: 'json',
            ids: qvalues.join("|"),
            languages: me.uiLanguage,
            origin: '*',
            languagefallback: ''
        };
        $.ajax( {
            type: 'GET',
            url: 'https://www.wikidata.org/w/api.php',
            data: secondApiOptions
            })
        .done( function (response) {
            // now we have the labels, populate the statements area to show existing depicts items
            // we need to extract isProminent from results of previous API call to Commons
            // and add the labels and descriptions found to the existing stored data
            var intialStatementsHtml = "";
            for (var qvalue in response.entities) {
                var storedStatementData = getStoredStatementData(qvalue);

                var itemData = response.entities[qvalue],
                    labelLang = Object.keys(itemData.labels)[0],
                    label = itemData.labels[labelLang].value,
                    descriptionLang = Object.keys(itemData.descriptions)[0],
                    description = (descriptionLang) ? itemData.descriptions[descriptionLang].value : '',
                    isProminent = storedStatementData.isProminent,
                    statementId = storedStatementData.statementId;

                intialStatementsHtml += me.getStatementHtml(qvalue, label, description, isProminent, statementId);

                // save label and description
                storedStatementData.label = label;
                storedStatementData.description = description;
            }
            $('.depict-tag-group').html(intialStatementsHtml);

            if (callbacks.onUiRendered) callbacks.onUiRendered(); // fires when the the actual HTML has finsihed being added to the page

            function getStoredStatementData(qvalue) {
                //uses depictItems from previous API call to Commons
                for (var i=0; i < depictItems.length; i++) {
                    if (depictItems[i].item === qvalue) return depictItems[i];
                }
            }
        });
    });
}

ParticipationManager.prototype.getStatementHtml = function(item, label, description, isProminent, statementId) {
    var statementIdAttribute = (statementId) ?
        'statement-id=' + statementId :
        '';
    var prominentHoverText = this.i18nStrings['Mark this depicted item as prominent'];
    var notProminentHoverText = this.i18nStrings['Mark this depicted item as NOT prominent'];

    var isProminentButtonHtml = isProminent ?
        '<button class="btn btn-sm prominent-btn active" title=' + notProminentHoverText + '><i class="fas fa-flag"></i></button>' :
        '<button class="btn btn-sm  prominent-btn" title=' + prominentHoverText  + '><i class="fas fa-flag"></i></button>';

    return [
        '<div class="depict-tag-item" ' + statementIdAttribute + ' title="' + description + '">',
        '<div class="depict-tag-label">',
        '<div class="label btn-sm"><span class="depict-tag-label-text"><a href="//www.wikidata.org/wiki/' + item + '" target="_blank">' + label + '</a></span> <span class="depict-tag-qvalue">' + item + '</span></div>',
        isProminentButtonHtml,
        '<div class="depict-tag-btn">',
        '<button class="fas fa-trash btn-link btn" title="' + this.i18nStrings['Remove this depicted item']  + '"></button></div>',
        '</div></div></div>'].join("");
}

function populateCaption(language, text) {
    $('.caption-input[lang=' + language + ']').val(text);
}

function getCaptionLanguages() {
    var languages = []
    $('.caption-input').each(function() {
        languages.push( $(this).attr('lang'))
    })
    return languages;
}