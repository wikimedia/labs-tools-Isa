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

ParticipationManager.prototype.getRejectedSuggestions = function() {
    return $.ajax({
        type: 'GET',
        url: '/api/get-rejected-statements?file=' + this.imageFileName,
    })
}

ParticipationManager.prototype.populateMachineVisionSuggestions = function() {
    var me = this;
    var mvPromise = this.getMachineVisionSuggestions();
    var rejectionPromise = this.getRejectedSuggestions();

    Promise.all([mvPromise, rejectionPromise]).then(function(responseArray){
        var data = responseArray[0];
        var rejections = responseArray[1];
        me.depictSuggestions = (data.query.pages[0].imagelabels || [])
            .filter(function(suggestion) {
                return suggestion.state === 'unreviewed' &&
                       !rejections.includes(suggestion.wikidata_id);
            })
            .sort(function(a,b) {return b.confidence.google - a.confidence.google})
            .map(suggestion => ({...suggestion, isGoogleVision: true }))
        me.renderDepictSuggestions();
    });
}

ParticipationManager.prototype.renderDepictSuggestions = function() {
    $('.depict-tag-suggestions').empty();
    var suggestions = this.depictSuggestions;

    if (this.areSuggestionsVisible()) {
        $('#depict-tag-suggestions-container').show();  
        for (var i=0; i<suggestions.length; i++) {
            if (suggestions[i].isAccepted) continue;
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
        confidence = Math.round(suggestionData.confidence.google * 100);

    var confidenceString = ' (' + confidence + "%) ";
    return [
        '<div class="depict-tag-suggestion" title="' + description + '">',
        '<div class="depict-tag-label">',
        '<div class="label btn-sm">',
        '<div class="suggestion">',
        suggestionData.isGoogleVision ? '<span class="service-type-gv"></span>' : '',
        suggestionData.isMetadataToConcept ? '<span class="service-type-md"></span>': '',
        '</div>',
        '<span class="depict-tag-label-text">'+ label + '</span> ' ,
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
