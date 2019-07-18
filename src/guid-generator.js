// Generate GUID (Globla Unique Identifier) to be used for creating new statements
// Logic taken from wikibase utility GuidGenerator: utility https://github.com/wikimedia/mediawiki-extensions-Wikibase/blob/a3736ac4e00dc33f78cc87364fd6feb3ff2301f2/view/resources/wikibase/utilities/wikibase.utilities.GuidGenerator.js

export function generateGuid () {
    var template = 'xx-x-x-x-xxx',
        guid = '';

    for ( var i = 0; i < template.length; i++ ) {
        var character = template.charAt( i );

        if ( character === '-' ) {
            guid += '-';
            continue;
        }

        var hex;
        if ( i === 3 ) {
            hex = getRandomHex( 16384, 20479 );
        } else if ( i === 4 ) {
            hex = getRandomHex( 32768, 49151 );
        } else {
            hex = getRandomHex( 0, 65535 );
        }

        while ( hex.length < 4 ) {
            hex = '0' + hex;
        }

        guid += hex;
    }

    return guid;
}

function getRandomHex(min, max) {
    return ( Math.floor( Math.random() * ( max - min + 1 ) ) + min ).toString( 16 );
}