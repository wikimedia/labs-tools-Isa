$( function () {
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
        })
          .done( function( response ) {
                var response_metadata = response.query.pages[0].imageinfo[0].extmetadata;
                $( '#image_name' ).text( response.query.pages[0].title );
                $( '#image_description' ).text( response_metadata.ImageDescription.value );
                $( '#image_categories' ).text( response_metadata.Categories.value );
                $( '#image_author' ).append( response_metadata.Artist.value );

           // console.log( response_metadata );
          } )
          .fail(function( e ) {
            console.log( e );
          } );
    }
    //  Populate  metadata for current slide
    // In this case, the carousel-item has not changed yet
    var current_slide = $( '.carousel-item' ).find( 'img' ).attr( 'alt' );
    populateImageMetadata( current_slide );

    // here we detect a change in the carousel item
    $( '#campaignPartcipateImageCarousel' ).bind( 'slide.bs.carousel', function (e) {
        // we get the previous slide
        var slideFrom = $(this).find( '.active' ).index();
        var totalItems = $( '.carousel-item' ).length;
        if ( slideFrom < totalItems - 1 ) {
            var destination = $( '.carousel-item' ).eq( slideFrom + 1 ).find( 'img' ).attr( 'alt' );
            populateImageMetadata( destination );
        }
        else{
            var current_slide = $( '.carousel-item' ).find( 'img' ).attr( 'alt' );
            populateImageMetadata( current_slide );
        }
    } );
} );
