var path = require('path');
var webpack = require('webpack');
var I18nPlugin = require("i18n-webpack-plugin");
var languages = {
	en: null,
	fr: require(getLangJsonPath('fr'))
};

module.exports = Object.keys(languages).map(function(language) {
    return {
        name: language,
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
            path: path.resolve(__dirname, 'isa/static/js/' + language),
            filename: '[name].js',
        },
        plugins: [
            new I18nPlugin(languages[language], {
                'functionName': 'gettext'
            }),
            new webpack.DefinePlugin({
                UI_LANGUAGE: JSON.stringify(language),
                WIKI_URL: JSON.stringify('https://commons.wikimedia.org/')
            })
        ]
    }
})

function getLangJsonPath(langCode) {
    return path.resolve(__dirname, 'isa/translations/') + '/' + langCode + '/LC_MESSAGES/messages.json' ;
}