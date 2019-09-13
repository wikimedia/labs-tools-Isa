import os

from flask import Blueprint, render_template, session, redirect, url_for, request
from flask_login import current_user

from isa import gettext
from isa.users.utils import add_user_to_db

main = Blueprint('main', __name__)


@main.route('/')
def home():
    username = session.get('username', None)
    directory = os.getcwd() + '/campaign_stats_files/'
    session_language = session.get('lang', None)
    if not os.path.exists(directory):
        os.makedirs(directory)
    if not session_language:
        session_language = 'en'
    username_for_current_user = add_user_to_db(username)
    session['next_url'] = request.url
    return render_template('main/home.html',
                           title='Home',
                           session_language=session_language,
                           username=username_for_current_user,
                           current_user=current_user)


@main.route('/help')
def help():
    username = session.get('username', None)
    session_language = session.get('lang', None)
    username_for_current_user = add_user_to_db(username)
    session['next_url'] = request.url
    if not session_language:
        session_language = 'en'
    return render_template('main/help.html',
                           title='Help',
                           session_language=session_language,
                           username=username_for_current_user,
                           current_user=current_user)


@main.route('/', methods=['GET', 'POST'])
def set_language(lang):
    session['lang'] = lang
    return redirect(url_for('main.home'))
