$(document).ready( function () {

    // Retrieve the list of images from the Commons API
    // TODO: HARD CODED temporary category query - will be replaced with:
    // - getCapaignCategories(doneCallback, thenCallback)
    // - .done getSubcategories(categoriesArray) - asynch gets unique list of all subcategories for each campaign category (to specified depth). Includes the root categories as well
    // - .then getImagesFromCategories(allCatsAndSubcats, allCompleteCallback) - async request images for all subcategories and 
    // Note: both categorymember API calls will use generalised API call function, with cmtype=subcat / cmtype=file
    
    var apiOptions = {
        action: 'query',
        list: 'categorymembers',
        cmtitle: 'Category:Images from Wiki Loves Africa 2019',
        cmlimit: 'max',
        cmtype: 'file',
        format: 'json',
        origin: '*'
    };
    
    $.ajax({
        type: 'GET',
        url: 'https://commons.wikimedia.org/w/api.php',
        data: apiOptions
    }).done(function(response) {
        var results = response.query.categorymembers;
        var images = results.map(function(result) {
            var filename = result.title;
            return result.title;
        }).filter(function(filename) {
            // only include filenames with supported extensions
            var fileExtension = filename.split('.').pop().toLowerCase();
            var allowedExtensions = ["jpg", "jpeg", "png", "svg"];
            return allowedExtensions.includes(fileExtension);
        })
        
        // launch new participationManager using list of images in response from api
        window.participationManager = new ParticipationManager(images);
        participationManager.imageChanged();
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
              tags: true,
              multiple: true,
              tokenSeparators: [',', ' '],
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
                              id: result.id +'|'+ $('.active').find('img').attr('alt'),
                              text: result.label,
                              description: result.description || "" //use "" as default to avoid 'undefined' showing as description
                          });
                      }
                      return {
                          results: processedResults
                      };
                  }
            },
            templateResult: searchResultsFormat,
            createTag: function() {
                return undefined;
            }
        });
      })();


    $( '#add_depict_btn' ).click(function (e) {
        $( '#depicts_search_form_section' ).slideDown();
        return false;
    });
    
    
    // ParticipationManager class manages all aspects of the current participation session
    // The initialData property contains an object with inital depicts and captions data retrieved from Commons
    // Difference between current and initialData is used to determine unsavedChanges after each change made in UI 
    //  - This allows us to update "publish" and "cancel" button states
    //  - Also used for sending edits to Commons and ISA database when either submit is click 
    // Data is sent via ajax post request instead of default form submit to prevent page reload
    ParticipationManager = function(images) {
        var imageIndex = 0,
            countrySubcategory = getUrlParameters().country, //returns country or undefined
            initialData = {depicts: [], captions: []},
            unsavedChanges = {depicts: [], captions: []};
        
        this.nextImage = function() {
            imageIndex = (imageIndex + 1) % (images.length);
            this.imageChanged();
        }
        
        this.previousImage = function() {
            imageIndex -= 1;
            //jump to end of list if previous image is called on index=0
            if (imageIndex < 0) imageIndex = images.length - 1;
            this.imageChanged();
        }
        
        this.imageChanged = function() {
            // all actions to complete when a new image has loaded
            var file = getImageFilename()
            updateImage(file);
            populateMetadata(file);
            populateStructuredData(file, /*callback*/ saveInitialStructuredData);
        }
    
        function getImageFilename () {
            return images[imageIndex];
        }
        
        function saveInitialStructuredData(depictsData, captionsData) {
            // todo: store the results of the intial api call, so represents the live data before any changes
            initialData.depicts = depictsData;
            //initialData.captions = captionsData;
        }
        
        function updateUnsavedChanges() {
            // todo: compare current selection to initialData to see if there are any unsaved changes
        }
        
    
        function updateImage(filename) {
            $('.img-holder img').attr('src', 'https://commons.wikimedia.org/wiki/Special:FilePath/' + filename + '?width=500')
        }
        
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

        function populateStructuredData(filename, callback) {
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
                // todo: get captions data, and pass cleaned data to callback function (which saves initial state)
                var mediaId = Object.keys(response.entities)[0];
                var depictsStatements = [];
                // no depicts data
                // Todo: add "this item has no depicts statement yet" message to separate div

                var mediaStatements = response.entities[mediaId].statements;
                if ( !(mediaStatements && mediaStatements.P180) ) {
                    //todo: add message to new div
                    return console.log("this item has no depicts statements yet")
                }

                // convert results to list of Q numbers only
                // todo: switch to array of objects to store isProminent value for each 
                depictsItems = mediaStatements.P180.map(function(depictsStatement) {
                    return depictsStatement.mainsnak.datavalue.value.id;
                });
                if (callback) callback(depictsItems);
                if (depictsItems.length === 0) return;
                
                // now make another call to Wikidata to get the labels for each depcits item
                var secondApiOptions = {
                    action: 'wbgetentities',
                    props: 'labels|descriptions',
                    format: 'json',
                    ids: depictsItems.join("|"),
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
                    var intialStatementsHtml = "";
                    for (var qvalue in response.entities) {
                        var itemData = response.entities[qvalue],
                            labelLang = Object.keys(itemData.labels)[0],
                            label = itemData.labels[labelLang].value,
                            descriptionLang = Object.keys(itemData.descriptions)[0],
                            description = itemData.descriptions[descriptionLang].value;
                            //todo: access isProminent value
                        intialStatementsHtml += getStatementHtml(qvalue, label, description);
                    }
                    $('.depict-tag-group').html(intialStatementsHtml);
                });
            });
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
        
        function getStatementHtml(item, label, description, isProminent) {
            return [
                '<div class="depict-tag-item" title="' + description + '">',
                '<div class="depict-tag-label">', 
                '<div class="label btn-sm">' + label + ' <span class="depict-tag-item">' + item + '</span></div>',
                '<button class="btn btn-sm btn-warning mark-prominent-btn" title="Mark this depicted item as NOT prominent">Prominent</button>',
                '<div class="depict-tag-btn">',
                '<button class="fas fa-trash btn-link btn" title="Remove this depicted item"></button></div>',
                '</div></div></div>'].join("");
        }
    }
    
    /********* click handlers *********/
    $('#next-image-btn').click(function(ev) {
        participationManager.nextImage();
    })
    
    $('#previous-image-btn').click(function(ev) {
        participationManager.previousImage();
    })
    
});
    