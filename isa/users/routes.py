import mwoauth

import sys
from flask import Blueprint, redirect, url_for, flash, request, session, render_template
from flask_login import current_user, login_user, logout_user
# import pycountry

from isa import app, gettext
from isa.main.utils import testDbCommitSuccess
from isa.models import User
from isa.users.forms import CaptionsLanguageForm

from isa.users.utils import buildUserPrefLang

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
    captions_lang_form = CaptionsLanguageForm()
    if captions_lang_form.is_submitted():
        caption_language_1 = request.form.get('language_select_1')
        caption_language_2 = request.form.get('language_select_2')
        caption_language_3 = request.form.get('language_select_3')
        caption_language_4 = request.form.get('language_select_4')
        caption_language_5 = request.form.get('language_select_5')
        caption_language_6 = request.form.get('language_select_6')
        user_pref_lang = buildUserPrefLang(caption_language_1, caption_language_2,
                                           caption_language_3, caption_language_4,
                                           caption_language_5, caption_language_6)
        # We select the user with username and update their pref_lang
        current_user = User.query.filter_by(username=username).first()
        current_user.pref_lang = user_pref_lang
        # commit failed
        if testDbCommitSuccess():
            flash(gettext('Captions languages could not be set'), 'danger')
        else:
            flash(gettext('Prefered Languages set Successfully'), 'success')
            # We make sure that the form data does not remain in browser
            return redirect(url_for('main.home'))
    elif request.method == 'GET':
        current_user_langs = User.query.filter_by(username=username).first().pref_lang.split(',')
        captions_lang_form.language_select_1.data = str(current_user_langs[0])
        captions_lang_form.language_select_2.data = str(current_user_langs[1])
        captions_lang_form.language_select_3.data = str(current_user_langs[2])
        captions_lang_form.language_select_4.data = str(current_user_langs[3])
        captions_lang_form.language_select_5.data = str(current_user_langs[4])
        captions_lang_form.language_select_6.data = str(current_user_langs[5])
    else:
        flash(gettext('Language settings not available at the moment'), 'info')
    return render_template('users/user_settings.html',
                           title=gettext('%(username)s\'s - Settings', username=username),
                           captions_lang_form=captions_lang_form)
