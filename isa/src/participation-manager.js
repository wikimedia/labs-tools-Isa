
/*********** Manage the current participation session ***********/

// The initialData property contains an object with inital depicts and captions data retrieved from Commons
// Difference between current and initialData is used to determine unsavedChanges after each change made in UI 
//  - This allows us to update "publish" and "cancel" button states
//  - Also used for sending edits to Commons and ISA database when either submit is click 
// Data is sent via ajax post request instead of default form submit to prevent page reload

import {flashMessage} from './utils';
import {WIKI_URL} from './options';

export function ParticipationManager(images, campaignId, wikiLovesCountry, isUserLoggedIn) {
        var imageIndex = 0,
        imageFileName = '',
        imageRevId = 0,
        userCaptionLanguages = getUserLanguages(),
        initialData = {depicts: [], captions: []},
        unsavedChanges = {depicts: [], captions: []};
    

    this.imageMediaId = '';
    
    this.nextImage = function () {
        imageIndex = (imageIndex + 1) % (images.length);
        this.imageChanged();
    }

    this.previousImage = function () {
        imageIndex -= 1;
        // jump to end of list if previous image is called on index=0
        if (imageIndex < 0) imageIndex = images.length - 1;
        this.imageChanged();
    }

    // All actions to complete when a new image has loaded
    this.imageChanged = function () {
        var me = this;
        document.documentElement.scrollTop = 0;
        imageFileName = getImageFilename ()
        updateImage(imageFileName);
        this.populateMetadata(imageFileName);
        this.populateStructuredData(imageFileName, /*callbacks*/ {
            onInitialDataReady: saveInitialStructuredData,
            onUiRendered: function () {
                // run data change events to update button states and other settings
                // must be done once HTML is rendered as this is used to find differences to start data
                me.depictDataChanged();
                me.captionDataChanged();
            }
        });
    }

    this.addDepictStatement = function(item, label, description, isProminent, statementId) {
        var statementHtml = getStatementHtml(item, label, description, isProminent, statementId);
        $('.depict-tag-group').append(statementHtml);
        this.depictDataChanged();
    }

    // All actions to complete when depict statement is added/removed/edited
    this.depictDataChanged = function () {
        updateUnsavedDepictChanges();
        
        // Keep buttons inactive when user is not logged in
        if (isUserLoggedIn) updateButtonStates("depicts");
    }

    // All actions to complete when caption statement is added/removed/edited
    this.captionDataChanged = function () {
        updateUnsavedCaptionChanges();
        
        // Keep buttons inactive when user is not logged in
        if (isUserLoggedIn) updateButtonStates("captions");
    }

    this.resetDepictStatements = function () {
        $('.depict-tag-group').empty();
        var initialDepictsData = initialData.depicts;
        for (var i=0; i < initialDepictsData.length; i++) {
            var depictItem = initialDepictsData[i];
            var item = depictItem.item,
                label = depictItem.label,
                description = depictItem.description,
                isProminent = depictItem.isProminent,
                statementId = depictItem.statementId;
            this.addDepictStatement(item, label, description, isProminent, statementId)
        }
    }

    this.resetCaptions = function () {
        var initialCaptionsData = initialData.captions;
         $('.caption-input').val('');
        for (var i=0; i < initialCaptionsData.length; i++) {
            var caption = initialCaptionsData[i];
            var value = caption.value || '',
                language = caption.language;
            $('.caption-input[lang=' + language + ']').val(value)
        }
    }


    // Posts the current unsaved changes to the server as a JSON string
    this.postContribution = function(editType) {

        // Define data which is the same for all contribution types
        var additonalContributionData = {
            image: imageFileName,
            media_id: this.imageMediaId,
            campaign_id: campaignId,
            edit_type: editType,
            country: wikiLovesCountry
        }

        // Make deep copy of contribution data to keep original unchanged
        var contributions = $.extend(/*deep*/ true, [], unsavedChanges[editType]);

        contributions.map(function (contribution, index) {
            // Add common contribution data
            $.extend(contribution, additonalContributionData);
            
            // Get edit API call for this contribution
            var apiOptions = getEditApiOptions(contribution);
            
            // Add the revision id for the first contribution only;
            // the next api calls will need baserevid from previous call's response
            if (index === 0) apiOptions.baserevid = imageRevId;
            
            contribution.api_options = apiOptions;
            return contribution;
        })

        var contributionsData = JSON.stringify(contributions);

        var me = this;
        
        console.log(contributions)
        $.post({
            url: '../../api/post-contribution',
            data: contributionsData,
            contentType: 'application/json'
        }).done(function(response) {
            // Contribution accepted by server, now we can update initial data
            // Button states will return to disabled
            // Cancel buttons will now reset to the current image data
            
            imageRevId = response // server sends revision id from final edit as response
            if (editType === "depicts") {
                saveInitialStructuredData(getCurrentDepictStatements(), false);
                me.depictDataChanged();
                flashMessage('success', gettext('Success! Depicted items saved to Wikimedia Commons'))
            }
            if (editType === "captions") {
                saveInitialStructuredData(false, getCurrentCaptions());
                me.captionDataChanged();
                flashMessage('success', gettext('Success! Captions saved to Wikimedia Commons'))
            }

        }).fail( function(error) {
            flashMessage('danger', gettext('Oops! Something went wrong, your edits have not been saved to Wikimedia Commons'))
        })
    }
    
     /////////// Data populating functions ///////////

    this.populateMetadata = function(filename) {
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
            var metadata = response.query.pages[0].imageinfo[0].extmetadata;
            var title = response.query.pages[0].title;
            var escapedTitle = encodeURIComponent(title);
            var htmlStrippedDescription = $('<span>' + metadata.ImageDescription.value + '</span>').text();

            var cameraLocationHtml = '(unknown)',
                lat = metadata.GPSLatitude,
                long = metadata.GPSLongitude;

            if (lat && long) {
                var locationUrl = 'https://www.openstreetmap.org/?mlat=' + lat.value + '&mlon=' + long.value,
                    locationText = lat.value + ', ' + long.value;
                cameraLocationHtml = '<a href=' + locationUrl + '>' + locationText + '</a>';
            }

            // spacing between categories
            var categories = metadata.Categories.value.replace(/\|/g,' | ');

            $('#image_name').html('<a href=' + WIKI_URL + 'wiki/' + escapedTitle + ' target="_blank">' + title.replace("File:", "") + '</a>');
            $('#image_description').text(htmlStrippedDescription);
            $('#image_categories').text(categories);
            $('#image_author').html(metadata.Artist.value);
            $('#image_camera_location').html(cameraLocationHtml);
            $('#image_credit').html(metadata.Credit.value);
            $('#image_license').html('<a href=' + metadata.LicenseUrl.value + '>' + metadata.LicenseShortName.value + '</a>');

        } );
    }
    
    this.populateStructuredData = function(filename, callbacks) {
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
            imageRevId = response.entities[mediaId].lastrevid;
            var mediaStatements = response.entities[mediaId].statements || {};
            var mediaCaptions = response.entities[mediaId].labels || {};
            var depictItems = [];
            var captions = [];

            // process captions
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
                languages: 'en',
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
                        description = itemData.descriptions[descriptionLang].value,
                        isProminent = storedStatementData.isProminent,
                        statementId = storedStatementData.statementId;

                    intialStatementsHtml += getStatementHtml(qvalue, label, description, isProminent, statementId);

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

    /////////// Image utilities ///////////

    function getImageFilename () {
        return images[imageIndex];
    }

    function updateImage(filename) {
        $('.img-holder img').attr('src', WIKI_URL + 'wiki/Special:FilePath/' + filename + '?width=500')
    }

    /////////// Change tracking functions ///////////

    // Used to store starting data from Commons, or after changes have been saved
    function saveInitialStructuredData(depictsData, captionsData) {
        if (depictsData) initialData.depicts = depictsData;
        if (captionsData) initialData.captions = captionsData;
    }

    // Get the current depcits data as displayed in the UI
    function getCurrentDepictStatements () {
        var statements = []
        $('.depict-tag-item').each(function(index, element) {
            var item = $(element).find('.depict-tag-qvalue').text(),
                label = $(element).find('.depict-tag-label-text').text(),
                description = $(element).attr('title'),
                isProminent = $(element).find('.prominent-btn').hasClass('active'),
                statementId = $(element).attr('statement-id');
            statements.push({
                item: item,
                label: label,
                description: description,
                isProminent: isProminent,
                statementId: statementId || ''
            });
        })
        return statements;
    }

    // Get the current captions data as displayed in the UI
    function getCurrentCaptions () {
        var captions = [];
        $('.caption-input').each(function(index, element) {
            var caption = $(element).val(),
                language = $(element).attr('lang');
            if (caption) {
                captions.push({
                    language: language,
                    value: caption
                })
            }
        })
        return captions;
    }

    //todo: create generalised updateUnsavedChanges which work for depicts and captions
    function updateUnsavedDepictChanges () {
        // Compare current selection to initialData to see if there are any unsaved changes

        var depictStatements = getCurrentDepictStatements();
        var intialDepictStatements = initialData.depicts;
        var depictChanges = [];

        // Compare to initial state to find actual depcits edits

        // First find any new items, or changes to isProminent
        for (var i=0; i < depictStatements.length; i++) {
            var currentStatement = depictStatements[i],
                depictItem = currentStatement.item,
                isProminent = currentStatement.isProminent;
            var found = false;
            for (var j=0; j < intialDepictStatements.length; j++) {
                // check all intial statements to see if currentStatement q number was there
                var initialStatement = intialDepictStatements[j];

                if (depictItem === initialStatement.item) {
                    // the item was there to start with, now check if isProminent has changed
                    if (isProminent !== initialStatement.isProminent) {
                        // only isProminent has changed
                        depictChanges.push({
                            edit_action: "edit",
                            depict_item: depictItem,
                            depict_prominent: isProminent,
                            statement_id: currentStatement.statementId
                        })
                    } // else, no changes to statement

                    found = true;
                    break; // any changes for this item have now been found, no need to check more initial statements
                }
            }

            if (!found) {
                // The current depicts item has not been found, it must be an unsaved change
                depictChanges.push({
                    edit_action: "add",
                    depict_item: depictItem,
                    depict_prominent: isProminent,
                    statement_id: currentStatement.statementId
                })
            }
        } // check next statement...

        // Second, find any removed statements
        for (var i = 0; i < intialDepictStatements.length; i++) {
            var initialStatement = intialDepictStatements[i];
            var found = false;
            // for each initialStatement, check if it still exists in current depictStatements
            for (var j=0; j < depictStatements.length; j++) {
                var currentStatement = depictStatements[j];
                if (currentStatement.item === initialStatement.item) {
                    found = true;
                    break;
                }
            }

            if (!found) {
                depictChanges.push({
                    edit_action: "remove",
                    depict_item: initialStatement.item,
                    depict_prominent: initialStatement.isProminent,
                    statement_id: initialStatement.statementId
                })
            }
        } // check next initial statement...

        unsavedChanges.depicts = depictChanges;
    }

    function updateUnsavedCaptionChanges () {
        var captions = getCurrentCaptions();
        var intialCaptions = initialData.captions;
        var captionChanges = [];

        // get current captions fromt the UI
        // each language has a separate input
        // all inputs have class "caption-input" and custom "lang" attribute

        // First, find the added or edited captions
        for (var i=0; i < captions.length; i++) {
            var captionText = captions[i].value,
                captionLanguage = captions[i].language
                found = false;
            for (var j=0; j < intialCaptions.length; j++) {
                var initialCaption = intialCaptions[j];

                if (captionLanguage === initialCaption.language) {
                    // this language caption existed intially
                    // has the text changed?
                    if (captionText !== initialCaption.value) {
                         captionChanges.push({
                             edit_action: "edit",
                             caption_text: captionText,
                             caption_language: captionLanguage
                        })
                    } // else, no changes to caption
                    found = true;
                    break; // any changes for this item have now been found, no need to check more captions
                }
            }

            if (!found) {
                // The current caption has not been found, it must be an unsaved change
                captionChanges.push({
                    edit_action: "add",
                    caption_text: captionText,
                    caption_language: captionLanguage
                })
            }
        } // check next statement...

        // Second, find any removed caption
        for (var i = 0; i < intialCaptions.length; i++) {
            var initialCaption = intialCaptions[i];
            var found = false;
            // for each initialCaption, check if it still exists in current captions
            for (var j=0; j < captions.length; j++) {
                var currentCaption = captions[j];
                if (currentCaption.language === initialCaption.language) {
                    found = true;
                    break;
                }
            }

            if (!found) {
                captionChanges.push({
                    edit_action: "remove",
                    caption_text: initialCaption.value,
                    caption_language: initialCaption.language,
                })
            }
        } // check next initial statement...
        unsavedChanges.captions = captionChanges;
    }
    
    
    /////////// Edit API calls ///////////
    
    function getEditApiOptions(contribution) {
        var editType = contribution.edit_type,
            editAction = contribution.edit_action;
        
        // Depicts edit
        if (editType === 'depicts') {
            var depictItem = contribution.depict_item,
                depictProminent = contribution.depict_prominent,
                statementId = contribution.statement_id,
                claim;
            
            if (editAction === 'add' || editAction === 'edit') {
                //action = 'wbsetclaim'
                claim = {
                    "type": "statement",
                    "mainsnak": {
                        "snaktype": "value",
                        "property": "P180",
                        "datavalue": {
                            "type": "wikibase-entityid",
                            "value": {
                                "id": depictItem
                            }
                        }
                    },
                    "id": statementId,
                    "rank": (depictProminent) ? "preferred" : "normal"
                }
                
            } else if (editAction === 'remove') {
                claim = statementId;
            }
            return {
                action: (editAction === 'remove') ? 'wbremoveclaims' : "wbsetclaim",
                claim: claim
            };
        
        // Captions edit
        } else if (editType === 'captions') {
            return {
                action: "wbsetlabel",
                id: contribution.media_id,
                value: contribution.caption_text,
                language: contribution.caption_language,
            }
        };
        
        //else
        return console.log("edit type not recognised, edit API call not generated!");
    }
    

   

    /////////// General utilities ///////////

    function getStatementHtml(item, label, description, isProminent, statementId) {
        var statementIdAttribute = (statementId) ? 
            'statement-id=' + statementId : 
            '';
        var prominentHoverText = gettext('Mark this depicted item as prominent');
        var notProminentHoverText = gettext('Mark this depicted item as NOT prominent');
            
        var isProminentButtonHtml = isProminent ?
            '<button class="btn btn-sm prominent-btn active" title=' + notProminentHoverText + '><i class="fas fa-flag"></i></button>' :
            '<button class="btn btn-sm  prominent-btn" title=' + prominentHoverText  + '><i class="fas fa-flag"></i></button>';
        
        return [
            '<div class="depict-tag-item" ' + statementIdAttribute + ' title="' + description + '">',
            '<div class="depict-tag-label">', 
            '<div class="label btn-sm"><span class="depict-tag-label-text">' + label + '</span> <span class="depict-tag-qvalue">' + item + '</span></div>',
            isProminentButtonHtml,
            '<div class="depict-tag-btn">',
            '<button class="fas fa-trash btn-link btn" title="Remove this depicted item"></button></div>',
            '</div></div></div>'].join("");
    }

    function updateButtonStates(editType) {
        var currentChanges = unsavedChanges[editType],
            $publishBtns = $('.edit-publish-btn-group[edit-type=' + editType + '] button'),
            areButtonsDisabled = currentChanges.length === 0;
        $publishBtns.prop('disabled', areButtonsDisabled);
    }

    function populateCaption(language, text) {
        $('.caption-input[lang=' + language + ']').val(text);
    }

    function getUserLanguages() {
        var languages = []
        $('.caption-input').each(function() {
            languages.push( $(this).attr('lang'))
        })

        return languages;
    }
}
