$(document).ready( function () {
    var campaignId = getCampaignId(),
        wikiLovesCountry = getWikiLovesCountry(),
        isWikiLovesCampaign = !!wikiLovesCountry; // todo: this should be read from get-campaign-categories api call 
    
    // Retrieve campaign categories with depth from internal API
    $.getJSON("../../api/get-campaign-categories?campaign=" + campaignId)
        .done(function(categories) {
            console.log(isWikiLovesCampaign, wikiLovesCountry)
        
            // todo: if it's a wiki loves campaign with no country selected, set all depth = 1 (ignore category depth settings)
            // Add Category: prefix
            categories.forEach(function(category) {
                category.name = "Category:" + category.name;
                })
            
            if (isWikiLovesCampaign && wikiLovesCountry) {
                categories.forEach(function(category) {
                    category.name += ' in ' + wikiLovesCountry;
                    category.depth = 0;
                })
            }
            
            // Get images in categories
            CategoryMembers.getImages(categories, function(images) {
                // Now we have all images from processing each category with depth
                // Start a new editSession using the Participation Manager
                console.log("Images retrieved!", images)
                window.editSession = new ParticipationManager(images);
                
                // Trigger image changed event to populate the page
                editSession.imageChanged();
            })
        })
        .fail(function(err) {
            console.log("error retrieving campaign categories", err)
        })

    
    
    // Initialise the depicts search box
    // Results populated via api call

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
              placeholder: 'Search for depicts',
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
            editSession.addDepictStatement(selected.id, selected.text, selected.description)
        })
      })();
    
    // ParticipationManager class manages all aspects of the current participation session
    // The initialData property contains an object with inital depicts and captions data retrieved from Commons
    // Difference between current and initialData is used to determine unsavedChanges after each change made in UI 
    //  - This allows us to update "publish" and "cancel" button states
    //  - Also used for sending edits to Commons and ISA database when either submit is click 
    // Data is sent via ajax post request instead of default form submit to prevent page reload
    ParticipationManager = function(images) {
        var imageIndex = 0,
            imageFileName = '',
            userCaptionLanguages = ['en', 'fr', 'de', 'es'], // todo: update on startup from user preferences 
            initialData = {depicts: [], captions: []},
            unsavedChanges = {depicts: [], captions: []};
            
           
        
        this.nextImage = function () {
            imageIndex = (imageIndex + 1) % (images.length);
            this.imageChanged();
        }
        
        this.previousImage = function () {
            imageIndex -= 1;
            //jump to end of list if previous image is called on index=0
            if (imageIndex < 0) imageIndex = images.length - 1;
            this.imageChanged();
        }
        
        // All actions to complete when a new image has loaded
        this.imageChanged = function () {
            var me = this;
            var file = getImageFilename ()
            imageFileName = file;
            updateImage(file);
            populateMetadata(file);
            populateStructuredData(file, /*callbacks*/ {
                onInitialDataReady: saveInitialStructuredData,
                onUiRendered: function () {
                    // run data change events to update button states and other settings
                    // must be done once HTML is rendered as this is used to find differences to start data
                    me.depictDataChanged();
                    me.captionDataChanged();
                }
            });
        }
        
        this.addDepictStatement = function (item, label, description, isProminent) {
            var statementHtml = getStatementHtml(item, label, description, isProminent);
            $('.depict-tag-group').append(statementHtml);
            this.depictDataChanged();
        }
        
        // All actions to complete when depict statement is added/removed/edited
        this.depictDataChanged = function () {
            updateUnsavedDepictChanges();
            updateButtonStates("depicts");
        }
        
        // All actions to complete when caption statement is added/removed/edited
        this.captionDataChanged = function () {
            updateUnsavedCaptionChanges();
            updateButtonStates("captions");
        }
        
        this.resetDepictStatements = function () {
            $('.depict-tag-group').empty();
            var initialDepictsData = initialData.depicts;
            for (var i=0; i < initialDepictsData.length; i++) {
                var depictItem = initialDepictsData[i];
                var item = depictItem.item,
                    label = depictItem.label,
                    description = depictItem.description,
                    isProminent = depictItem.isProminent;
                this.addDepictStatement(item, label, description, isProminent)
            }
        }
        
        this.resetCaptions = function () {
            $('.caption-input').val('');
            //todo: complete once caption data is populated at startup
            
        }
        
        // Posts the current unsaved changes to the server as a JSON string
        this.postContribution = function(editType) {
            
            // now extend the unsavedChanged data with properties that are the same for all contribution types
            var additonalContributionData = {
                image: imageFileName,
                campaign_id: campaignId,
                edit_type: editType,
                country: wikiLovesCountry
            }
            
            //make deep copy of contribution data to keep original unchanged
            var contributions = $.extend(/*deep*/ true, [], unsavedChanges[editType]);
            
            contributions.map(function (contribution) {
                return $.extend(contribution, additonalContributionData);
            })
            
            var contributionsData = JSON.stringify(contributions);
            
            var me = this;
            $.post({
                url: '../../api/post-contribution',
                data: contributionsData,
                contentType: 'application/json'
            }).done(function(response) {
                console.log("Contribution posted - ", response, contributionsData)
                
                // Contribution accepted by server, now we can update initial data
                // Button states will return to disabled
                // Cancel buttons will now reset to the current image data
                if (editType === "depicts") {
                    saveInitialStructuredData(getCurrentDepictStatements(), false);
                    me.depictDataChanged();
                }
                if (editType === "captions") {
                    saveInitialStructuredData(false, getCurrentCaptions());
                    me.captionDataChanged();
                }
                
            }).fail( function(error) {
                console.log("Unable to post contributions to ISA server", error)
            })
        }
        
        /*---------- Image utilities ----------*/
        
        function getImageFilename () {
            return images[imageIndex];
        }
    
        function updateImage(filename) {
            $('.img-holder img').attr('src', 'https://commons.wikimedia.org/wiki/Special:FilePath/' + filename + '?width=500')
        }
        
        /*---------- Change tracking functions ----------*/
        
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
                    isProminent = $(element).find('.prominent-btn').hasClass('active');
                statements.push({
                    item: item,
                    label: label,
                    description: description,
                    isProminent: isProminent
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
                var currentStatement = depictStatements[i];
                var editContent = {item: currentStatement.item, isProminent: currentStatement.isProminent};
                var found = false;
                for (var j=0; j < intialDepictStatements.length; j++) {
                    // check all intial statements to see if currentStatement q number was there
                    var initialStatement = intialDepictStatements[j];
                    
                    if (initialStatement.item === currentStatement.item) {
                        // the item was there to start with, now check if isProminent has changed
                        if (currentStatement.isProminent !== initialStatement.isProminent) {
                            // only isProminent has changed
                            depictChanges.push({
                                edit_action: "edit",
                                edit_content: editContent,
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
                        edit_content: editContent,
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
                        edit_content: {item: initialStatement.item, isProminent: initialStatement.isProminent},
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
                var currentCaption = captions[i],
                    found = false;
                for (var j=0; j < intialCaptions.length; j++) {
                    var initialCaption = intialCaptions[j];
                    
                    if (currentCaption.language === initialCaption.language) {
                        // this language caption existed intially
                        // has the text changed?
                        if (currentCaption.value !== initialCaption.value) {
                             captionChanges.push({
                                edit_action: "edit",
                                edit_content: currentCaption,
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
                        edit_content: currentCaption,
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
                        edit_content: initialCaption,
                    })
                }
            } // check next initial statement...
            unsavedChanges.captions = captionChanges;
        }
    
        /*---------- Data populating functions ----------*/
        
        function populateMetadata(filename) {
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
                url: 'https://commons.wikimedia.org/w/api.php',
                data: apiOptions
            } )
            .done( function( response ) {
                var metadata = response.query.pages[0].imageinfo[0].extmetadata;
                var title = response.query.pages[0].title;
                var escapedTitle = encodeURIComponent(title);
                var htmlStrippedDescription = $('<span>' + metadata.ImageDescription.value + '</span>').text();
                $('#image_name').html('<a href=' + "https://commons.wikimedia.org/wiki/" + escapedTitle + ' target="_blank">' + title.replace("File:", "") + '</a>');
                $('#image_description').html(htmlStrippedDescription);
                $('#image_categories').text(metadata.Categories.value);
                $('#image_author').html(metadata.Artist.value);
            } );
        }

        function populateStructuredData(filename, callbacks) {
            $('.depict-tag-group').empty(); //clear previous
            var entitiesApiOptions = {
                action: 'wbgetentities',
                titles: filename,
                sites: 'commonswiki',
                format: 'json',
                origin: '*'
            };
            $.ajax( {
                type: 'GET',
                url: 'https://commons.wikimedia.org/w/api.php',
                data: entitiesApiOptions
            } ).done( function( response ) {
               
                var mediaId = Object.keys(response.entities)[0];
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
                    }
                }
                
                // process statements
                if ( mediaStatements.P180 ) {
                    // convert results to array of {item, isProminent} objects
                    depictItems = mediaStatements.P180.map(function(depictStatement) {
                        return {
                            item: depictStatement.mainsnak.datavalue.value.id,
                            isProminent: depictStatement.rank === "preferred"
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
                        var storedItemData = getStoredItemData(qvalue);
                        
                        var itemData = response.entities[qvalue],
                            labelLang = Object.keys(itemData.labels)[0],
                            label = itemData.labels[labelLang].value,
                            descriptionLang = Object.keys(itemData.descriptions)[0],
                            description = itemData.descriptions[descriptionLang].value,
                            isProminent = storedItemData.isProminent;
                            //todo: access isProminent value
                        intialStatementsHtml += getStatementHtml(qvalue, label, description, isProminent);
                        
                        // save label and description
                        storedItemData.label = label;
                        storedItemData.description = description;
                    }
                    $('.depict-tag-group').html(intialStatementsHtml);
                    
                    if (callbacks.onUiRendered) callbacks.onUiRendered(); // fires when the the actual HTML has finsihed being added to the page
                    
                    function getStoredItemData(qvalue) {
                        //uses depictItems from previous API call to Commons
                        for (var i=0; i < depictItems.length; i++) {
                            if (depictItems[i].item === qvalue) return depictItems[i];
                        }
                    }
                });
            });
        }
        
        /*---------- General utilities ----------*/
        
        function getStatementHtml(item, label, description, isProminent) {
            var isProminentButtonHtml = isProminent ?
                '<button class="btn btn-sm btn-warning prominent-btn active" title="Mark this depicted item as NOT prominent">Prominent</button>' :
                '<button class="btn btn-sm btn-warning prominent-btn" title="Mark this depicted item as prominent">Prominent</button>'
            return [
                '<div class="depict-tag-item" title="' + description + '">',
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
    }
    
    
    function getCampaignId () {
        var parts = window.location.pathname.split("/");
        return parseInt(parts[parts.length - 2]);
    }
    
    function getWikiLovesCountry () {
        var country = getUrlParameters().country;
        return (country) ? decodeURIComponent(country) : '';
    }
    
    
    function getUrlParameters () {
        var parametersObject = {};
        var parameters = window.location.search.substr(1);
        if (parameters == "") return {};
        parameters = parameters.split('&');
        for (var i = 0; i < parameters.length; i++) {
            var splitParameters = parameters[i].split('=');
            parametersObject[ splitParameters[0] ] = splitParameters[1];
        }
        return parametersObject;
    };



    /********* event handlers *********/
    $('#next-image-btn').click(function(ev) {
        editSession.nextImage();
    })
    
    $('#previous-image-btn').click(function(ev) {
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
    
});
    