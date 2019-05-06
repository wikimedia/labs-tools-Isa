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

    $('.carousel').carousel({
        interval: false
    });
} );
