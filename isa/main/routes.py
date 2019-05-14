from flask import Blueprint, render_template, session
from flask_login import current_user

from isa.users.utils import add_user_to_db, get_user_language_preferences

main = Blueprint('main', __name__)


@main.route('/')
def home():
    username = session.get('username', None)
    username_for_current_user = add_user_to_db(username)
    return render_template('main/home.html',
                           title='Home',
                           username=username_for_current_user,
                           user_pref_lang=get_user_language_preferences(username),
                           current_user=current_user)
