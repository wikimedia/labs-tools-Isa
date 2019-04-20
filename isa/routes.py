from datetime import datetime

import mwoauth
import pycountry
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import current_user, login_user, logout_user

from isa import app, db
from isa.forms import CampaignForm, UpdateCampaignForm
from isa.models import Campaign, Contribution, User


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


@app.route('/')
def home():
    username = session.get('username', None)
    username_for_current_user = add_user_to_db(username)
    return render_template('home.html',
                           title='Home',
                           username=username_for_current_user,
                           user_pref_lang=get_user_language_preferences(username),
                           current_user=current_user)


@app.route('/campaigns')
def getCampaigns():
    campaigns = Campaign.query.all()
    username = session.get('username', None)
    return render_template('campaigns.html',
                           title='Campaigns',
                           username=username,
                           campaigns=campaigns,
                           today_date=datetime.date(datetime.utcnow()),
                           datetime=datetime,
                           user_pref_lang=get_user_language_preferences(username),
                           current_user=current_user)


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


@app.route('/campaigns/<string:campaign_name>')
def getCampaignById(campaign_name):
    # We get the current user's user_name
    username = session.get('username', None)
    # We select the campaign and the manager here
    campaign = Campaign.query.filter_by(campaign_name=campaign_name).first()
    campaign_manager = User.query.filter_by(id=campaign.user_id).first()
    # We get all the contributions from the ddatabase
    all_contributions = Contribution.query.all()
    # contributions for campaign
    campaign_contributions = 0
    # Editor for a particular campaign
    campaign_editors = 0
    # participantids for this campaign
    campaign_users_ids = []
    # We are querrying all the users who participate in the campaign
    contribs_for_campaign = Contribution.query.filter_by(campaign_id=campaign.id).all()
    for campaign_contribution in contribs_for_campaign:
        campaign_users_ids.append(campaign_contribution.user_id)
    # we get the unique ids so as not to count an id twice
    campaign_users_ids_set = set(campaign_users_ids)
    campaign_editors = len(campaign_users_ids_set)
    # We then re-initialize the ids array
    campaign_users_ids = []
    # We now get the contributor count for this campaign
    for contrib in all_contributions:
        if (contrib.campaign_id == campaign.id):
            campaign_contributions += 1
    return render_template('campaign.html', title='Campaign - ' + campaign_name,
                           campaign=campaign,
                           campaign_manager=campaign_manager.username,
                           username=username,
                           campaign_editors=campaign_editors,
                           campaign_contributions=campaign_contributions,
                           user_pref_lang=get_user_language_preferences(username),
                           current_user=current_user)


def get_country_from_code(country_code):
    """
    Get country label from country code.

    Keyword arguments:
    country_code -- the code of the country (e.g 'FR' for France)
    """
    country = []
    countries = [(country.alpha_2, country.name) for country in pycountry.countries]
    for country_index in range(len(countries)):
        # index 0 is the country code selected from the form
        if(countries[country_index][0] == country_code):
            country.append(countries[country_index])
    return country[0][1]


def compute_campaign_status(end_date):
    """
    Computes the campaign status (Open or closed).

    Keyword arguments:
    end_date -- the end date of the campaign
    """
    status = bool('False')
    if (end_date.strftime('%Y-%m-%d %H:%M') < datetime.now().strftime('%Y-%m-%d %H:%M')):
        status = bool('True')
    return status


def testDbCommitSuccess():
    """
    Test for the success of a database commit operation.

    """
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        # for resetting non-commited .add()
        db.session.flush()
        return True
    return False


@app.route('/campaigns/create', methods=['GET', 'POST'])
def CreateCampaign():
    # We get the current user's user_name
    username = session.get('username', None)
    form = CampaignForm()
    if form.is_submitted():
        # We add the campaign information to the database
        # TODO: Add current userid for user who created campaign
        campaign = Campaign(
            campaign_country=get_country_from_code(form.campaign_country.data),
            campaign_name=form.campaign_name.data,
            categories=form.categories.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            status=compute_campaign_status(form.end_date.data),
            description=form.description.data,
            user_id=1)
        db.session.add(campaign)
        # commit failed
        if testDbCommitSuccess():
            flash('Campaign exists already in {}'.format(
                  form.campaign_country.data), 'danger')
        else:
            flash('{} Campaign created!'.format(form.campaign_name.data), 'success')
            return redirect(url_for('getCampaigns'))
    return render_template('create_campaign.html', title='Create a campaign',
                           form=form, datetime=datetime,
                           username=username,
                           user_pref_lang=get_user_language_preferences(username),
                           current_user=current_user)


@app.route('/campaigns/<string:campaign_name>/participate')
def contributeToCampaign(campaign_name):
    # We get the current user's user_name
    username = session.get('username', None)
    return render_template('campaign_entry.html', title=campaign_name + ' - Contribute',
                           campaign_name=campaign_name,
                           user_pref_lang=get_user_language_preferences(username),
                           current_user=current_user)


@app.route('/login')
def login():
    """Initiate an OAuth login.
    
    Call the MediaWiki server to get request secrets and then redirect the
    user to the MediaWiki server to sign the request.
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    else:
        consumer_token = mwoauth.ConsumerToken(
            app.config['CONSUMER_KEY'], app.config['CONSUMER_SECRET'])
        try:
            redirect_string, request_token = mwoauth.initiate(
                app.config['OAUTH_MWURI'], consumer_token)
        except Exception:
            app.logger.exception('mwoauth.initiate failed')
            return redirect(url_for('home'))
        else:
            session['request_token'] = dict(zip(
                request_token._fields, request_token))
            user = User.query.filter_by(username=session.get('username', 'Guest')).first()
            if user and user.username != 'Guest':
                login_user(user)
            return redirect(redirect_string)


@app.route('/oauth-callback')
def oauth_callback():
    """OAuth handshake callback."""
    if 'request_token' not in session:
        flash(u'OAuth callback failed. Are cookies disabled?')
        return redirect(url_for('home'))

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
        flash(' Welcome  {}!'.format(session['username']), 'success')
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    """Log the user out by clearing their session."""
    logout_user()
    session.clear()
    flash('See you next time!', 'success')
    return redirect(url_for('home'))


@app.route('/campaigns/<string:campaign_name>/update', methods=['GET', 'POST'])
def updateCampaign(campaign_name):
    # We get the current user's user_name
    username = session.get('username', 'Guest')
    form = UpdateCampaignForm()

    # when the form is submitted, we update the campaign
    # TODO: Check if campaign is closed so that it cannot be edited again
    # This is a potential issue/Managerial
    if form.is_submitted():
        campaign = Campaign.query.filter_by(campaign_name=campaign_name).first()
        campaign.campaign_name = form.campaign_name.data
        campaign.description = form.description.data
        campaign.categories = form.categories.data
        campaign.campaign_country = get_country_from_code(form.campaign_country.data)
        campaign.start_date = form.start_date.data
        campaign.end_date = form.end_date.data
        if testDbCommitSuccess():
            flash('Please check the country for this Campaign!', 'danger')
        else:
            flash('Updated Succesfull!', 'success')
            return redirect(url_for('getCampaigns'))
    # User requests to edit so we update the form with Campaign details
    elif request.method == 'GET':
        # we get the campaign data to place in form fields
        campaign = Campaign.query.filter_by(campaign_name=campaign_name).first()
        form.campaign_name.data = campaign.campaign_name
        form.description.data = campaign.description
        form.categories.data = campaign.categories
        form.campaign_country.data = campaign.campaign_country
        form.start_date.data = campaign.start_date
        form.end_date.data = campaign.end_date
    else:
        flash('Booo! {} Could not be updated!'.format(
              form.campaign_name.data), 'danger')
    return render_template('update_campaign.html', title=campaign_name + ' - Update',
                           form=form,
                           user_pref_lang=get_user_language_preferences(username),
                           current_user=current_user)
