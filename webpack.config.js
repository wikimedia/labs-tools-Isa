var path = require('path');
var webpack = require('webpack');

module.exports = {
    entry: {
        'participate': './isa/src/participate.js',
        'campaign': './isa/src/campaign.js',
        'campaign-directory': './isa/src/campaign-directory.js',
        'campaign-form': './isa/src/campaign-form.js',
        'user-settings': './isa/src/user-settings.js',
        'main': './isa/src/main.js',
        'stats': './isa/src/stats.js'
    },
    output: {
        path: path.resolve(__dirname, 'isa/static/js/'),
        filename: '[name].js',
    },
    plugins: [
        new webpack.DefinePlugin({
            WIKI_URL: JSON.stringify('https://commons.wikimedia.org/')
        })
    ]
}