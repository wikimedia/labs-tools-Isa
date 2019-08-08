var path = require('path');

module.exports = {
    entry: {
        'participate': './isa/src/participate.js',
        'campaign': './isa/src/campaign.js',
        'campaign-directory': './isa/src/campaign-directory.js',
        'campaign-form': './isa/src/campaign-form.js',
        'user-settings': './isa/src/user-settings.js',
        'main': './isa/src/main.js'
    },
    output: {
        path: path.resolve(__dirname, 'isa/static/js'),
        filename: '[name].js',
    },
    
    // Show source files instead of bundle in browser console
    devtool: 'eval-source-map'
}