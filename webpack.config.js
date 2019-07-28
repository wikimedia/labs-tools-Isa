var path = require('path');

module.exports = {
    entry: {
        'participate': './src/participate.js',
        'campaign': './src/campaign.js',
        'campaign-directory': './src/campaign-directory.js',
        'campaign-form': './src/campaign-form.js',
        'user-settings': './src/user-settings.js',
        'main': './src/main.js'
    },
    output: {
        path: path.resolve(__dirname, 'isa/static/js'),
        filename: '[name].js',
    },
    
    // Show source files instead of bundle in browser console
    devtool: 'eval-source-map'
}