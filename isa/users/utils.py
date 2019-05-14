from isa.models import User
from isa import db
from isa.main.utils import testDbCommitSuccess


def check_user_existence(username):
    """
    Check if user exists already in db

    Keyword arguments:
    username -- the currently logged in user
    """
    user_exists = User.query.filter_by(username=username).first()
    if not user_exists:
        return True
    else:
        return False


def add_user_to_db(username):
    """
    Add user to database if they don't exist already

    Keyword arguments:
    username -- the currently logged in user
    """
    if check_user_existence(username):
        user = User(username=username, pref_lang='en,fr')
        db.session.add(user)
        if testDbCommitSuccess():
            return False
        else:
            return user.username
    else:
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
        user_pref_options = user.pref_lang
        return user_pref_options.split(',')


# TODO: The below functions are used to perform operations on the db tables
# def sum_all_user_contributions(users):
#     """
#     Sum contributions made by all users.

#     Keyword arguments:
#     users -- the users list
#     """
#     user_contribution_sum = 0
#     for user in users:
#         user_contribution_sum += get_user_contributions(user.id)
#     return user_contribution_sum
