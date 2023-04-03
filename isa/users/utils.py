from operator import itemgetter

from isa import db
from isa.main.utils import commit_changes_to_db
from isa.models import User, Contribution


def check_user_existence(username):
    """
    Check if user exists already in db

    Keyword arguments:
    username -- the currently logged in user
    """

    user = User.query.filter_by(username=username).first()
    if not user:
        return None
    return user


def add_user_to_db(username):
    """
    Add user to database if they don't exist already

    Keyword arguments:
    username -- the currently logged in user
    """

    user = check_user_existence(username)
    if not user:
        user = User(username=username, caption_languages='en,fr,,,,')
        db.session.add(user)
        if commit_changes_to_db():
            return user.username

    user = User.query.filter_by(username=username).first()
    return user.username


def get_user_language_preferences(username):
    """
    Get user language preferences for currently logged in user

    Keyword arguments:
    username -- the currently logged in user
    """

    user = User.query.filter_by(username=username).first()
    if user is None:
        return 'en,fr'.split(',')
    else:
        user_pref_options = []
        user_pref_langs = user.caption_languages.split(',')
        for lang in user_pref_langs:
            if lang != 'None' and lang != '':
                user_pref_options.append(lang)
        if len(user_pref_options) == 0:
            return ['en', 'fr']
        return user_pref_options


def get_user_ranking(all_contributors_data, username):
    """
    Get a particular user's ranking

    Keyword arguments:
    all_contributors_data -- sorted list of all users by their contributions
    username -- the user who's ranking is to be obtained
    """

    index = next((i for i, item in enumerate(all_contributors_data) if item['username'] == username), -1)
    return index + 1  # we shift from 0


def get_user_contrbition_per_campaign(username, campaign_id):
    """
    Get a particular user's contribution per Campaign

    Keyword arguments:
    username -- the user who's contributions is to be obtained
    campaign_id -- the campaign id
    """

    user = User.query.filter_by(username=username).first()
    user_contribs = Contribution.query.filter_by(user=user).all()
    user_contributed_files = []
    user_contribution_data = {}  # has keys username and images_improved
    for contrib in user_contribs:
        if contrib.campaign_id == campaign_id:
            user_contributed_files.append(contrib.file)
    user_contribution_data['username'] = username
    user_contribution_data['images_improved'] = len(user_contributed_files)
    return user_contribution_data


def get_all_users_contribution_data_per_campaign(Users, campaign_id):
    """
    Get all user contributions per Campaign

    Keyword arguments:
    Users -- List of all users who make contributions in a campaign
    campaign_id -- the campaign id
    """

    all_contributors_data = []
    for user in Users:
        if user is not None:
            all_contributors_data.append(get_user_contrbition_per_campaign(user.username, campaign_id))
    #  We sort the users and their contributions data in decreaasing order
    all_contributors_data = sorted(all_contributors_data, key=itemgetter('images_improved'), reverse=True)
    return all_contributors_data


def get_current_user_images_improved(all_contributors_data, username):
    """
    Get current user's ranking

    Keyword arguments:
    all_contributors_data -- sorted list of all users by their contributions
    username -- the user who's images improved is to be obtained
    """

    current_user_images_improved = 0
    for contributors_data in all_contributors_data:
        if contributors_data.get('username') == username:
            current_user_images_improved = contributors_data.get('images_improved')
    return current_user_images_improved


def build_user_pref_lang(lang_1, lang_2, lang_3, lang_4, lang_5, lang_6):
    """
    Build user preferred language string with language choices

    Keyword arguments:
    lang_1 -- Language option 1
    lang_2 -- Language option 2
    lang_3 -- Language option 3
    lang_4 -- Language option 4
    lang_5 -- Language option 5
    lang_6 -- Language option 6
    """
    return lang_1 + ',' + lang_2 + ',' + lang_3 + ',' + lang_4 + ',' + lang_5 + ',' + lang_6
