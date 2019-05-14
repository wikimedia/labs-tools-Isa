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

    $( function() {
        $( '.selectpicker' ).selectpicker();
    } );

    // we remove the auto-sliding of the carousel
    $( '.carousel' ).carousel( {
        interval: false
    } );
    // when the page loads, we hide the section for depict search 
    var current_slide = $( '.carousel-item' ).find( 'img' ).attr( 'alt' );

    // we get the language set for the depicts
    var depicts_language = $('#depicts_lang_select').val();
    // we convert the depicts seach box to a select field
    // which will make the Ajax call to Wikidata api

    function setUpDepictsForm(current_image){
        $( '#depicts_select_options' ).select2( {
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
                url: ' https://www.wikidata.org/w/api.php',
                data: function (params) {
                    var query = {
                        search: params.term,
                        action: 'wbsearchentities',
                        language: depicts_language,
                        format: 'json',
                        uselang: 'fr',
                        origin: '*'
                    }
                    return query
                },
                processResults: function (data) {
                    var depict_search_results = [];
                    var i=0;
                    for ( var item in data.search) {
                        depict_search_results.push( {
                            id: data.search[item].id +'|'+ $('.active').find('img').attr('alt'),
                            text: data.search[item].label + ':' + data.search[item].description
                        });
                        i++;
                    }
                    return {
                        results: depict_search_results
                    };
                }
            },
            escapeMarkup: function(markup) {
                return markup;
              },
        });
    }

	/**
	 * Populate images metadata.
	 *
	 * @param {String} filename - the name of the file.
	 */
    function populateImageMetadata( filename ) {
        var apiOptions = {
            action: 'query',
            titles: 'File:'+filename,
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
            var response_metadata = response.query.pages[0].imageinfo[0].extmetadata;
            $( '#image_name' ).text( response.query.pages[0].title );
            $( '#image_description' ).text( response_metadata.ImageDescription.value );
            $( '#image_categories' ).text( response_metadata.Categories.value );
            $( '#image_author' ).append( response_metadata.Artist.value );
        } );
    }
    
	/**
	 * Populate images structured data.
	 *
	 * @param {String} filename - the name of the file.
	 */
    function populateStructuredDataSection( filename ) {
        var entitiesApiOptions = {
            action: 'wbgetentities',
            titles: 'File:'+filename,
            sites: 'commonswiki',
            format: 'json',
            formatversion: 2,
            origin: '*'
        };
        $.ajax( {
            type: 'GET',
            url: 'https://commons.wikimedia.org/w/api.php',
            data: entitiesApiOptions
        } ).done( function( response ) {
            var m_number = Object.keys(response.entities)[0];
            var depictsStatements = {};

            if ( response.entities[m_number].statements === undefined ) {
                $( '#depicts_columns' ).empty();
                $( '#depicts_error_message' ).empty();
                $('#depicts_error_message').show();
                $( '#depicts_error_message' ).append( "<div class='text-center col-md-12 pt-0 pb-0 mr-auto'>" +
                    "<small>This image has no depicts</small></div>" );
            } else {
                depictsStatements = response.entities[m_number].statements.P180;
            }
            var wikidata_Q_values = [];
            for (let index = 0; index < depictsStatements.length; index++) {
                wikidata_Q_values.push(depictsStatements[index].mainsnak.datavalue.value.id);
            }
            var first_element =  wikidata_Q_values.pop(0);
            var split_array = wikidata_Q_values.join('|');
            var id_string = '';
            if ( wikidata_Q_values.length === 0 ) {
                id_string = first_element;
            } else {
                id_string = first_element + '|' + split_array;
            }
            // we make an api call and get depicts for this id
            var secondApiOptions = {
                action: 'wbgetentities',
                props: 'labels|descriptions',
                format: 'json',
                ids: id_string,
                languages: 'en|fr',
                formatversion: 2,
                origin: '*',
                languagefallback: ''
            };
            $.ajax( {
                type: 'GET',
                url: 'https://www.wikidata.org/w/api.php',
                data: secondApiOptions
                })
            .done( function ( response ) {
                // $( '#depicts_columns' ).empty();
                $('#depicts_error_message').show();
                for ( var qvalue in response.entities ) {
                    for ( var lang in response.entities[qvalue].labels) {
                        $( '#depicts_columns' ).append(
                            "<div class='col-sm-2 mr-auto'>" +
                            "<div class='chip lighten-1><i class='close fas fa-times'>" +
                            response.entities[qvalue].labels[lang].value + "</i></div>" +
                            "</div>"
                        ); 
                    }
                }
            } );
        } );
    }

    $( '#depicts_columns' ).empty();
    //  Populate  metadata for current slide
    // In this case, the carousel-item has not changed yet

    populateImageMetadata( current_slide );
    populateStructuredDataSection( current_slide );
    setUpDepictsForm(current_slide);
    // here we detect a change in the carousel item
    $( '#campaignPartcipateImageCarousel' ).bind( 'slide.bs.carousel', function (e) {
        $( '#depicts_columns' ).empty();
        $( '#depicts_error_message' ).empty();   
        // we get the previous slide
        
        var slideFrom = $(this).find( '.active' ).index();
        var totalItems = $( '.carousel-item' ).length;
        if( slideFrom < totalItems - 1 ) {
            var destination = $( '.carousel-item' ).eq( slideFrom + 1 ).find( 'img' ).attr( 'alt' );
            populateImageMetadata( destination );
            populateStructuredDataSection( destination );
            setUpDepictsForm( destination );
        }
        else{
            var current_slide = $( '.carousel-item' ).find( 'img' ).attr( 'alt' );
            populateImageMetadata( current_slide );
            populateStructuredDataSection( current_slide );
            setUpDepictsForm( current_slide );
        }
    } );

    $( '#depicts_search_form_section' ).slideUp();
    $( '#add_depict_btn' ).click(function (e) {
        $( '#depicts_search_form_section' ).slideDown();
        return false;
    });
} );

