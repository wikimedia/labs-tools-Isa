/*********** Manage the current participation session ***********/

// The initialData property contains an object with inital depicts and captions data retrieved from Commons
// Difference between current and initialData is used to determine unsavedChanges after each change made in UI
//  - This allows us to update "publish" and "cancel" button states
//  - Also used for sending edits to Commons and ISA database when either submit is click
// Data is sent via ajax post request instead of default form submit to prevent page reload

import {flashMessage, getUrlParameters, getHtmlStripped} from '../utils';

export function ParticipationManager(images, campaignId, wikiLovesCountry, isUserLoggedIn) {
    var imageIndex = 0,
        initialData = {depicts: [], captions: []},
        unsavedChanges = {depicts: [], captions: []},
        csrf_token = "{{ csrf_token() }}";


    this.imageFileName = '';  
    this.imageMediaId = '';
    this.imageRevId = 0;
    this.uiLanguage = $('html').attr('lang');
    this.i18nStrings = JSON.parse($('.hidden-i18n-text').text());
    this.depictSuggestions = []; // Machine Vision suggestions;
    this.userRejectedSuggestions = [];
    this.machineVisionActive = !!getUrlParameters().mv;
    this.description = '';
    this.categories = '';
    this.isMobile = $(window).width() < 600 || $(window).height() < 600;

    this.nextImage = function() {
        if (!this.confirmImageNavigation()) return;
        imageIndex = (imageIndex + 1) % (images.length);
        this.imageChanged();
    }

    this.previousImage = function() {
        if (!this.confirmImageNavigation()) return;
        imageIndex -= 1;
        // jump to end of list if previous image is called on index=0
        if (imageIndex < 0) imageIndex = images.length - 1;
        this.imageChanged();
    }

    this.confirmImageNavigation = function () {
        if (areChangesUnsaved()) {
            return confirm(
                this.i18nStrings["Are you sure you want to navigate to another image? You have unsaved changes which will be lost."] + "\n" +
                this.i18nStrings["Click 'OK' to proceed anyway, or 'Cancel' if you want to save changes first."]
            )
        }
        return true;
    }

    this.setImageIndex = function(newIndex) {
        if (!this.confirmImageNavigation()) return;
        imageIndex = newIndex % (images.length);
        this.imageChanged();
    }

    // All actions to complete when a new image has loaded
    this.imageChanged = function() {
        var me = this;
        document.documentElement.scrollTop = 0;
        this.clearSuggestions();
        getImageFileInfo().done(function(imageData) {
            me.imageFileName = imageData.title;
            var imageInfo = imageData.imageinfo[0];
            var metadata = imageInfo.extmetadata;
            me.description = (metadata.ImageDescription) ? getHtmlStripped(metadata.ImageDescription.value) : '';
            me.categories = (metadata.Categories) ? metadata.Categories.value : '';
            me.imagesUrl = imageInfo.url
            updateImage(me.imageFileName);
            me.populateMetadata(me.imageFileName);
            me.populateStructuredData(me.imageFileName, /*callbacks*/ {
                onInitialDataReady: function(depictItems, captions) {
                    saveInitialStructuredData(depictItems, captions);
                    if (me.machineVisionActive) {
                        me.populateSuggestions();
                    }
                },
                onUiRendered: function() {
                    // run data change events to update button states and other settings
                    // must be done once HTML is rendered as this is used to find differences to start data
                    me.depictDataChanged();
                    me.captionDataChanged();
                }
            });
        });
    }

    this.addDepictStatement = function(item, label, description, isProminent, statementId) {
        var $statement = this.getStatement(
            item,
            label,
            description,
            isProminent,
            statementId
        );
        $('.depict-tag-group').append($statement);
        this.depictDataChanged();
    }

    // All actions to complete when depict statement is added/removed/edited
    this.depictDataChanged = function() {
        this.updateUnsavedDepictChanges();
        updateButtonStates("depicts");

        // Show depict helper text when any statements are present
        updateDepictHelperVisibility();

        // Highlight to show unsaved changes
        updateEditBoxHighlight("depicts");
        
        if (this.machineVisionActive) this.renderDepictSuggestions();
    }

    // All actions to complete when caption statement is added/removed/edited
    this.captionDataChanged = function () {
        updateUnsavedCaptionChanges();
        updateButtonStates("captions");

        // Highlight to show unsaved changes
        updateEditBoxHighlight("captions");
    }

    this.setDepictStatements = function(statements) {
        $('.depict-tag-group').empty();
        for (var i = 0; i < statements.length; i++) {
            var depictItem = statements[i];
            var item = depictItem.item,
                label = depictItem.label,
                description = depictItem.description,
                isProminent = depictItem.isProminent,
                statementId = depictItem.statementId;
            this.addDepictStatement(item, label, description, isProminent, statementId);
        }
        this.depictDataChanged();
    }

    this.setCaptions = function (captions) {
         $('.caption-input').val('');
        for (var i = 0; i < captions.length; i++) {
            var caption = captions[i];
            var value = caption.value || '',
                language = caption.language;
            $('.caption-input[lang=' + language + ']').val(value)
        }
        this.captionDataChanged();
    }

    this.resetDepictStatements = function() {
        this.setDepictStatements(initialData.depicts);
        if (this.machineVisionActive) this.resetDepictSuggestions();
    }

    this.resetCaptions = function() {
        this.setCaptions(initialData.captions);
    }

    this.getCaption = function(lang) {
        var captions = initialData.captions;
        for (var i=0; i<captions.length; i++) {
            if (captions[i].language === lang) return captions[i].value;
        }
    }

    this.redirectLogin = function() {
        var imageData = {
            fileName: this.imageFileName,
            depicts: getCurrentDepictStatements(),
            captions: getCurrentCaptions()
        }

        var newUrl = window.location.href;
        newUrl += newUrl.includes('?') ? '&' : '?';
        newUrl += 'imageData=' + JSON.stringify(imageData);

        $.get({
            url: '../../api/set-login-url',
            data: {
                url: newUrl
            }
        }).done(function(response) {
            window.location.href = '/login';
        });
    }

    // Posts the current unsaved changes to the server as a JSON string
    this.postContribution = function(editType) {

        if (!isUserLoggedIn) {
            this.redirectLogin();
            return;
        }

        // Define data which is the same for all contribution types
        var additonalContributionData = {
            image: this.imageFileName,
            media_id: this.imageMediaId,
            campaign_id: campaignId,
            edit_type: editType,
            country: wikiLovesCountry
        }

        // Make deep copy of contribution data to keep original unchanged
        var contributions = $.extend(/*deep*/ true, [], unsavedChanges[editType]);

        var me = this;
        contributions.map(function (contribution, index) {
            // Add common contribution data
            $.extend(contribution, additonalContributionData);

            // Get edit API call for this contribution
            var apiOptions = getEditApiOptions(contribution);

            // Add the revision id for the first contribution only;
            // the next api calls will need baserevid from previous call's response
            if (index === 0) apiOptions.baserevid = me.imageRevId;

            contribution.api_options = apiOptions;
            return contribution;
        })

        var contributionsData = JSON.stringify(contributions);

        var me = this;
        $.post({
            url: '../../api/post-contribution',
            data: contributionsData,
            contentType: 'application/json',
            headers: {
                "X-CSRFToken": csrf_token,
            },
        }).done(function(response) {
            // Contribution accepted by server, now we can update initial data
            // Button states will return to disabled
            // Cancel buttons will now reset to the current image data

            me.imageRevId = parseInt(response) // server sends revision id from final edit as response
            if (editType === "depicts") {
                saveInitialStructuredData(getCurrentDepictStatements(), false);
                me.depictDataChanged();
                flashMessage('success', me.i18nStrings['Success! Depicted items saved to Wikimedia Commons'])
            }
            if (editType === "captions") {
                saveInitialStructuredData(false, getCurrentCaptions());
                me.captionDataChanged();
                flashMessage('success', me.i18nStrings['Success! Captions saved to Wikimedia Commons'])
            }

        }).fail( function(error) {
            flashMessage('danger', me.i18nStrings['Oops! Something went wrong, your edits have not been saved to Wikimedia Commons'])
        })
    }

    /////////// Image utilities ///////////

    function getImageFileInfo () {
        var pageId = images[imageIndex];
        var deferred = $.Deferred();
        $.get({
            url: WIKI_URL + 'w/api.php',
            data: {
                action: 'query',
                prop: 'imageinfo',
                iiprop: 'extmetadata|url',
                pageids: pageId,
                format: 'json',
                formatversion: 2,
                origin: '*'
            }
        }).done((data) => {
            deferred.resolve(data.query.pages[0]);
        });

        return deferred;
    }

    function updateImage(filename) {
        $('.img-holder img').attr('src', WIKI_URL + 'wiki/Special:FilePath/' + filename + '?width=500');
        $('.img-holder').trigger('zoom.destroy');
        $('.img-holder').zoom({
            url: WIKI_URL + 'wiki/Special:FilePath/' + filename + '?width=500',
            magnify: 2
        });
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

    this.getCompleteClaim = function (item, intialClaims) {
        // use depict item and get initial depict from store
        for (var i = 0; i < intialClaims.length; i++) {
            if (intialClaims[i].item === item) {
                return intialClaims[i].completeClaim;
            }
        }
        return null
    }


    //todo: create generalised updateUnsavedChanges which work for depicts and captions
    this.updateUnsavedDepictChanges = function() {
        var depictStatements = getCurrentDepictStatements();
        var intialDepictStatements = initialData.depicts;
        var depictChanges = [];

        // Compare to initial state to find actual depcits edits

        // First find any new items, or changes to isProminent
        for (var i=0; i < depictStatements.length; i++) {
            var currentStatement = depictStatements[i],
                depictItem = currentStatement.item,
                isProminent = currentStatement.isProminent,
                ideps = JSON.parse(sessionStorage.getItem('intial_depicts'));

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
                            statement_id: currentStatement.statementId,
                            initial_claim: initialStatement.completeClaim != undefined ? initialStatement.completeClaim : this.getCompleteClaim(depictItem, ideps)
                        })
                    } // else, no changes to statement

                    found = true;
                    break; // any changes for this item have now been found, no need to check more initial statements
                }
            }

            if (!found) {
                // The current depicts item has not been found, it must be an unsaved change
                const suggestion = this.getDepictSuggestionByItem(depictItem);
                let isGoogleVision,
                    isMetadataToConcept,
                    googleVisionConfidence,
                    metadataToConceptConfidence;
                if (suggestion) {
                    isGoogleVision = suggestion.google_vision;
                    isMetadataToConcept = suggestion.metadata_to_concept;
                    googleVisionConfidence = suggestion.confidence.google;
                    metadataToConceptConfidence = suggestion.confidence.metadata_to_concept;
                }

                depictChanges.push({
                    edit_action: "add",
                    depict_item: depictItem,
                    depict_prominent: isProminent,
                    statement_id: currentStatement.statementId,
                    google_vision: isGoogleVision,
                    google_vision_confidence: googleVisionConfidence,
                    metadata_to_concept: isMetadataToConcept,
                    metadata_to_concept_confidence: metadataToConceptConfidence
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
                    caption_text: '',
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
                initialClaim = contribution.initial_claim,
                claim;

            switch (editAction) {
                case 'add':
                    claim = getAddClaimOptions(statementId, depictItem, depictProminent);
                    break;
                case 'edit':
                    claim = getEditClaimOptions(initialClaim, depictProminent);
                    break;
                case 'remove':
                    claim = statementId;
                    break;
                default:
                    console.error('Unrecognised edit type: ' + editAction);
                    return;
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

    function getAddClaimOptions(statementId, depictItem, isProminent) {   
        return {
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
            "rank": (isProminent) ? "preferred" : "normal"
        }
    }

    function getEditClaimOptions(initialClaim, isProminent) {
        var newClaim = $.extend(true, {}, initialClaim);
        newClaim.rank = (isProminent) ? "preferred" : "normal";
        return newClaim;
    }

    /////////// General utilities for Particiaption Manager /////////// 

    function areChangesUnsaved () {
        return areChangesUnsavedFor('depicts') || areChangesUnsavedFor('captions');
    }

    function areChangesUnsavedFor(editType) {
        return unsavedChanges[editType].length > 0;
    }

    function updateButtonStates(editType) {
        var $publishBtns = $('.edit-publish-btn-group[edit-type=' + editType + '] button'),
        areButtonsDisabled = !areChangesUnsavedFor(editType);
        $publishBtns.prop('disabled', areButtonsDisabled);
        return !areButtonsDisabled;
    }

    function updateEditBoxHighlight(editType) {
        var $editBox = $('.edit-publish-btn-group[edit-type=' + editType + ']').closest('.edit-box');
        if (areChangesUnsavedFor(editType)) {
            $editBox.addClass('active');
        } else {
            $editBox.removeClass('active');
        }
    }

    function updateDepictHelperVisibility() {
        var isVisible = $('.depict-tag-item').length > 0;
        if (isVisible) {
            $('.prom-help').addClass('d-block');
        } else {
            $('.prom-help').removeClass('d-block');
        }
    }
}
