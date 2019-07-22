import mwoauth
import json
import sys
from flask import Blueprint, redirect, url_for, flash, request, session, render_template
from flask_login import current_user, login_user, logout_user
# import pycountry

from isa import app, gettext
from isa.main.utils import testDbCommitSuccess
from isa.models import User
from isa.utils.languages import getLanguages
from isa.users.forms import CaptionsLanguageForm

from isa.users.utils import buildUserPrefLang, get_user_language_preferences

users = Blueprint('users', __name__)


@users.route('/login')
def login():
    """Initiate an OAuth login.
    
    Call the MediaWiki server to get request secrets and then redirect the
    user to the MediaWiki server to sign the request.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    else:
        consumer_token = mwoauth.ConsumerToken(
            app.config['CONSUMER_KEY'], app.config['CONSUMER_SECRET'])
        try:
            redirect_string, request_token = mwoauth.initiate(
                app.config['OAUTH_MWURI'], consumer_token)
        except Exception:
            app.logger.exception('mwoauth.initiate failed')
            return redirect(url_for('main.home'))
        else:
            session['request_token'] = dict(zip(
                request_token._fields, request_token))
            user = User.query.filter_by(username=session.get('username', 'Guest')).first()
            if user and user.username != 'Guest':
                login_user(user)
            return redirect(redirect_string)


@users.route('/oauth-callback')
def oauth_callback():
    """OAuth handshake callback."""
    if 'request_token' not in session:
        flash(gettext('OAuth callback failed. Are cookies disabled?'))
        return redirect(url_for('main.home'))

    consumer_token = mwoauth.ConsumerToken(
        app.config['CONSUMER_KEY'], app.config['CONSUMER_SECRET'])

    try:
        access_token = mwoauth.complete(
            app.config['OAUTH_MWURI'],
            consumer_token,
            mwoauth.RequestToken(**session['request_token']),
            request.query_string)

        identity = mwoauth.identify(
            app.config['OAUTH_MWURI'], consumer_token, access_token)
    except Exception:
        app.logger.exception('OAuth authentication failed')
    else:
        session['access_token'] = dict(zip(
            access_token._fields, access_token))
        session['username'] = identity['username']
        flash(gettext('Welcome  %(username)s!', username=session['username']), 'success')
        if session.get('next_url'):
            next_url = session.get('next_url')
            session.pop('next_url', None)
            return redirect(next_url)
    return redirect(url_for('main.home'))


@users.route('/logout')
def logout():
    """Log the user out by clearing their session."""
    logout_user()
    session.clear()
    flash(gettext('See you next time!'), 'info')
    return redirect(url_for('main.home'))


@users.route('/user-settings', methods=['GET', 'POST'])
def userSettings():
    username = session.get('username', None)
    session_language = session.get('lang', None)
    if not session_language:
        session_language = 'en'
    user_language_set = []
    # This will store the repeating languages
    repeated_language_values = []

    if not username:
        session['next_url'] = request.url
        flash(gettext('Please login to change your language preferences'), 'info')
        return redirect(url_for('main.home'))
    captions_lang_form = CaptionsLanguageForm()
    if captions_lang_form.is_submitted():
        caption_language_1 = str(request.form.get('language_select_1'))
        caption_language_2 = str(request.form.get('language_select_2'))
        caption_language_3 = str(request.form.get('language_select_3'))
        caption_language_4 = str(request.form.get('language_select_4'))
        caption_language_5 = str(request.form.get('language_select_5'))
        caption_language_6 = str(request.form.get('language_select_6'))

        # We now check if the user is trying to submit the same language in form

        user_language_set.append(caption_language_1)
        user_language_set.append(caption_language_2)
        user_language_set.append(caption_language_3)
        user_language_set.append(caption_language_4)
        user_language_set.append(caption_language_5)
        user_language_set.append(caption_language_6)

        repeated_languages = []
        for language in user_language_set:
            repeat_count = user_language_set.count(language)
            if repeat_count > 1 and language != '':
                repeated_languages.append(language)
        # we now get all the individual repeating languages
        repeated_languages = list(set(repeated_languages))

        if len(repeated_languages) > 0:
            # In this case at least on language repeats
            # We get the language from the the set of languages and tell the user

            language_options = getLanguages()
            for language_option in language_options:
                if language_option[0] in repeated_languages:
                    repeated_language_values.append(language_option[1])
        if len(repeated_language_values) > 0:
            # In this case there are repeating languages
            repeated_languages_text = ' - '.join(repeated_language_values)
            flash(gettext('Sorry you tried to enter %(rep_languages)s multiple times',
                          rep_languages=repeated_languages_text), 'danger')
            return redirect(url_for('users.userSettings'))
        else:
            user_pref_lang = buildUserPrefLang(caption_language_1, caption_language_2,
                                               caption_language_3, caption_language_4,
                                               caption_language_5, caption_language_6)
            # We select the user with username and update their pref_lang
            user = User.query.filter_by(username=username).first()
            user.pref_lang = user_pref_lang

            # commit failed
            if testDbCommitSuccess():
                flash(gettext('Captions languages could not be set'), 'danger')
            else:
                flash(gettext('Preferred Languages set Successfully'), 'success')
                # We make sure that the form data does not remain in browser
                return redirect(url_for('users.userSettings'))
    elif request.method == 'GET':
        user_langs = User.query.filter_by(username=username).first().pref_lang.split(',')
        captions_lang_form.language_select_1.data = str(user_langs[0])
        captions_lang_form.language_select_2.data = str(user_langs[1])
        captions_lang_form.language_select_3.data = str(user_langs[2])
        captions_lang_form.language_select_4.data = str(user_langs[3])
        captions_lang_form.language_select_5.data = str(user_langs[4])
        captions_lang_form.language_select_6.data = str(user_langs[5])
    else:
        flash(gettext('Language settings not available at the moment'), 'info')
    return render_template('users/user_settings.html',
                           title=gettext('%(username)s\'s - Settings', username=username),
                           current_user=current_user,
                           session_language=session_language,
                           user_pref_lang=get_user_language_preferences(username),
                           username=username,
                           captions_lang_form=captions_lang_form)


@users.route('/api/login-test', methods=['GET', 'POST'])
def checkUserLogin():
    username = session.get('username', None)
    response_data = {
        'username': username,
        'is_logged_in': bool(username is not None)
    }
    return json.dumps(response_data)
