import mwoauth

import sys
from flask import Blueprint, redirect, url_for, flash, request, session
from flask_login import current_user, login_user, logout_user
# import pycountry

from isa import app, gettext
from isa.models import User


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
        flash(gettext(' Welcome  %(username)s!', username=session['username']), 'success')
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
