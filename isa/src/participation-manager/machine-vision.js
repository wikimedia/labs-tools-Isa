/*********** Machine Vision API depict suggestions ***********/

import {ParticipationManager} from './base';
import {generateGuid} from '../guid-generator.js';

ParticipationManager.prototype.getMachineVisionSuggestions = function() { 
    var apiOptions = {
        action: 'query',
        titles: this.imageFileName,
        prop: 'imagelabels',
        uselang: this.uiLanguage,
        format: 'json',
        formatversion: 2,
        origin: '*'
    };

    return $.ajax({
        type: 'GET',
        url: WIKI_URL + 'w/api.php',
        data: apiOptions
    })
}

function getM2CAttr(key, value) {
    return {
        key: key,
        value: value
    }
}

function extractName(filename) {
    return filename.slice(0, filename.lastIndexOf("."));
}


// Requires captions to have been retrieved already for best suggestions
ParticipationManager.prototype.getM2CSuggestions = function() {
    var filename = this.imageFileName.split(":")[1];
    var name = extractName(filename);
    var apiOptions = {
        file: filename,
        attrs: [
            getM2CAttr("name", name),
            getM2CAttr("description", this.description),
            getM2CAttr("categories", this.categories.replaceAll('|', ';')),
        ]
    }
    var captionEn = this.getCaption("en");
    if (captionEn) apiOptions.attrs.push(getM2CAttr("caption", captionEn))

    return $.ajax({
        type: 'POST',
        contentType: 'application/json',
        url: 'https://m2c.wikimedia.se/extract/',
        data: JSON.stringify(apiOptions)
    });
}

ParticipationManager.prototype.getRejectedSuggestions = function() {
    return $.ajax({
        type: 'GET',
        url: '/api/get-rejected-statements?file=' + this.imageFileName,
    })
}

ParticipationManager.prototype.appendSuggestions = function (newSuggestions) {
    for (var i=0; i<newSuggestions.length; i++) {
        var newSuggestion = newSuggestions[i],
            item = newSuggestion.wikidata_id,
            currentSuggestion = this.getDepictSuggestionByItem(item);
        if (!currentSuggestion) {
            // new suggestion is not currently loaded
            this.depictSuggestions.push(newSuggestion);
            continue;
        }
        // else, add properties to existing suggestion object
        $.extend(true /*deep*/, currentSuggestion, newSuggestion) 
    }
}

ParticipationManager.prototype.clearSuggestions = function () {
    this.depictSuggestions = [];
    this.renderDepictSuggestions();
}

ParticipationManager.prototype.populateSuggestions = function() {
    this.getRejectedSuggestions().then(userRejectedSuggestions => {
        this.populateMachineVisionSuggestions(userRejectedSuggestions);
        this.populateM2CSuggestions(userRejectedSuggestions);
    })
}

ParticipationManager.prototype.populateMachineVisionSuggestions = function(userRejectedSuggestions=[]) {
    var requestedImage = this.imageFileName;
    this.getMachineVisionSuggestions().then(mvData => {
        var mvSuggestionData = (mvData.query.pages[0].imagelabels || [])
            .filter(suggestion => suggestion.state === 'unreviewed')
            .sort((a,b) => b.confidence.google - a.confidence.google)
            .map(suggestion => {
                var mappedSuggestion = {
                    ...suggestion,
                    google_vision: true
                }
                if (userRejectedSuggestions.includes(mappedSuggestion.wikidata_id)) {
                    mappedSuggestion.isRejectedByUser = true;
                }
                return mappedSuggestion;
            });

        if (this.imageFileName !== requestedImage) return; // abort if image has changed
        this.appendSuggestions(mvSuggestionData);
        this.renderDepictSuggestions();
    });
}

ParticipationManager.prototype.populateM2CSuggestions = function(userRejectedSuggestions=[]) {
    var requestedImage = this.imageFileName;
    this.getM2CSuggestions().then(m2cData => {
        var suggestions = Object.values(m2cData.items)
            .filter(suggestion => !!suggestion.qid)
            .map(suggestion => {
                var mappedSuggestion = {
                    label: suggestion.item,
                    wikidata_id: suggestion.qid,
                    confidence: {metadata_to_concept: 0}, // to be added once available
                    metadata_to_concept: true
                }
                if (userRejectedSuggestions.includes(mappedSuggestion.wikidata_id)) {
                    mappedSuggestion.isRejectedByUser = true;
                }
                return mappedSuggestion;
            })
        if (this.imageFileName !== requestedImage) return; // abort if image has changed
        this.appendSuggestions(suggestions);
        this.renderDepictSuggestions();
    });
}

ParticipationManager.prototype.renderDepictSuggestions = function() {
    $('.depict-tag-suggestions').empty();
    var suggestions = this.depictSuggestions;
    if (this.areSuggestionsVisible()) {
        $('#depict-tag-suggestions-container').show();  
        for (var i=0; i<suggestions.length; i++) {
            if (suggestions[i].isAccepted || suggestions[i].isRejectedByUser) continue;
            this.addSuggestionTag(suggestions[i]);
        }  
    } else {
        $('#depict-tag-suggestions-container').hide();
    }
}

ParticipationManager.prototype.addSuggestionTag = function(suggestionData) {
    $('.depict-tag-suggestions').append(this.getSuggestionHtml(suggestionData))
}

ParticipationManager.prototype.getSuggestionHtml = function(suggestionData) {
    var item = suggestionData.wikidata_id,
        label = suggestionData.label,
        description = 'State: ' + suggestionData.state + '\n\n' + suggestionData.description,
        confidenceData = suggestionData.confidence,
        confidence = confidenceData.google || confidenceData.metadata_to_concept,
        confidenceRounded = Math.round(confidence * 100);

    var confidenceString = ' (' + confidenceRounded + "%) ";
    return [
        '<div class="depict-tag-suggestion" title="' + description + '">',
        '<div class="depict-tag-label">',
        '<div class="label btn-sm">',
        '<div class="suggestion">',
        suggestionData.google_vision ? '<span class="service-type-gv"></span>' : '',
        suggestionData.metadata_to_concept ? '<span class="service-type-md"></span>': '',
        '</div>',
        '<span class="depict-tag-label-text"><a href="https://www.wikidata.org/wiki/'+ item +'" target="_blank">'+ label + '</a></span> ' ,
        '<span class="depict-tag-qvalue">' + item + '</span>',
        '<span class="depict-tag-confidence">' + confidenceString + '</span>',
        '<button class="accept-depict fa fa-check-circle"></button>',
        '<button class="reject-depict fa fa-times-circle"></button>',
        '</div></div></div>'].join("");
}

ParticipationManager.prototype.addDepictFromSuggestion = function(suggestionData) {
    var item = suggestionData.wikidata_id,
        label = suggestionData.label,
        description = suggestionData.description,
        statementId = this.imageMediaId + '$' + generateGuid();
    this.addDepictStatement(item, label, description, /*isProminent*/ false, statementId)
    suggestionData.isAccepted = true;

    // redraw suggestion to show removed suggestion
    this.renderDepictSuggestions();
}

ParticipationManager.prototype.addDepictBySuggestionItem = function(wikidataId) {
    var suggestion = this.getDepictSuggestionByItem(wikidataId);
    if (suggestion) this.addDepictFromSuggestion(suggestion);
}

ParticipationManager.prototype.areSuggestionsVisible = function() {
    for (var i=0; i<this.depictSuggestions.length; i++) {
        if (!this.depictSuggestions[i].isAccepted) return true;
    }
    return false;
}

ParticipationManager.prototype.getDepictSuggestionByItem = function(wikidataId) {
    for (var i=0; i<this.depictSuggestions.length; i++) {
        if (this.depictSuggestions[i].wikidata_id === wikidataId) {
            return this.depictSuggestions[i];
        }
    }
    return null;
}

ParticipationManager.prototype.resetDepictSuggestions = function(wikidataId) {
    for (var i=0; i<this.depictSuggestions.length; i++) {
        this.depictSuggestions[i].isAccepted = false;
    }
    this.renderDepictSuggestions();
}
