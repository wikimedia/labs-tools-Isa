import os

from flask import Blueprint, render_template, session, redirect, url_for
from flask_login import current_user
from isa import gettext


from isa.users.utils import add_user_to_db, get_user_language_preferences

main = Blueprint('main', __name__)


@main.route('/')
def home():
    username = session.get('username', None)
    directory = os.getcwd() + '/campaign_stats_files/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    if session['lang']:
        session_language = session['lang']
    username_for_current_user = add_user_to_db(username)
    return render_template('main/home.html',
                           title='Home',
                           session_language=session_language,
                           username=username_for_current_user,
                           user_pref_lang=get_user_language_preferences(username),
                           current_user=current_user)


@main.route('/', methods=['GET', 'POST'])
def set_language(lang):
    session['lang'] = lang
    return redirect(url_for('main.home'))
