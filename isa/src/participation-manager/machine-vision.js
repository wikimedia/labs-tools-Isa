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

ParticipationManager.prototype.populateMachineVisionSuggestions = function() {
    var me = this;
    this.getMachineVisionSuggestions().then(function(data) {
        me.depictSuggestions = (data.query.pages[0].imagelabels || [])
            .filter(function(suggestion) {return suggestion.state === 'unreviewed';})
            .sort(function(a,b) {return b.confidence.google - a.confidence.google})
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
        
    var confidenceString = ' (' + confidence + "%)";
    return [
        '<div class="depict-tag-suggestion" title="' + description + '">',
        '<div class="depict-tag-label">',
        '<div class="label btn-sm">',
        '<span class="depict-tag-label-text">'+ label + '</span> ' ,
        '<span class="depict-tag-qvalue">' + item + '</span>',
        '<span class="depict-tag-confidence">' + confidenceString + '</span>',
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
