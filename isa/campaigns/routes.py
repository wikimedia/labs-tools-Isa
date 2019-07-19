import os
import csv
import sys
import json
import shutil
import glob

from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, session, Blueprint, send_file
from isa import gettext
from flask_login import current_user

from io import StringIO
from isa import db
from isa.campaigns.forms import CampaignForm, UpdateCampaignForm
from isa.models import Campaign, Contribution, User
from isa.campaigns.utils import (constructEditContent, get_campaign_category_list, get_country_from_code,
                                 compute_campaign_status, buildCategoryObject, create_campaign_country_stats_csv,
                                 create_campaign_contributor_stats_csv, create_campaign_all_stats_csv,
                                 get_all_camapign_stats_data)
from isa.main.utils import testDbCommitSuccess, getCampaignCountryData
from isa.users.utils import (get_user_language_preferences,
                             getAllUsersContributionsPerCampaign, getUserRanking, getCurrentUserImagesImproved)
from isa.utils.languages import getLanguages


campaigns = Blueprint('campaigns', __name__)


@campaigns.route('/campaigns')
def getCampaigns():
    campaigns = Campaign.query.all()
    username = session.get('username', None)
    session_language = session.get('lang', None)
    if not session_language:
        session_language = 'en'
    return render_template('campaign/campaigns.html',
                           title=gettext('Campaigns'),
                           username=username,
                           session_language=session_language,
                           campaigns=campaigns,
                           today_date=datetime.date(datetime.utcnow()),
                           datetime=datetime,
                           user_pref_lang=get_user_language_preferences(username),
                           current_user=current_user)


@campaigns.route('/campaigns/<int:id>')
def getCampaignById(id):
    # We get the current user's user_name
    username = session.get('username', None)
    session_language = session.get('lang', None)
    if not session_language:
        session_language = 'en'
    campaign = Campaign.query.filter_by(id=id).first()
    if not campaign:
        flash(gettext('Campaign with id %(id)s does not exist', id=id), 'info')
        return redirect(url_for('campaigns.getCampaigns'))

    # We get all the contributions from the ddatabase
    all_contributions = Contribution.query.all()
    # contributions for campaign
    campaign_contributions = 0
    # Editor for a particular campaign
    campaign_editors = 0
    # participantids for this campaign
    campaign_user_names = []
    # We are querrying all the users who participate in the campaign
    contribs_for_campaign = Contribution.query.filter_by(campaign_id=campaign.id).all()
    for campaign_contribution in contribs_for_campaign:
        campaign_user_names.append(campaign_contribution.username)
    # we get the unique ids so as not to count an id twice
    campaign_user_names_set = set(campaign_user_names)
    campaign_editors = len(campaign_user_names_set)
    # We then re-initialize the ids array
    campaign_user_names = []
    # We now get the contributor count for this campaign
    for contrib in all_contributions:
        if (contrib.campaign_id == campaign.id):
            campaign_contributions += 1

    # We now obtain the ranking for all the users in the system and their files improved
    all_camapign_users_list = []
    #  We iterate the individual participants id in a campaign and get the user info
    for user_name in campaign_user_names_set:
        user = User.query.filter_by(username=user_name).first()
        all_camapign_users_list.append(user)

    # We get the users and their contribution data
    all_contributors_data = getAllUsersContributionsPerCampaign(all_camapign_users_list, id)
    current_user_rank = getUserRanking(all_contributors_data, username)
    current_user_images_improved = getCurrentUserImagesImproved(all_contributors_data, username)

    # We add rank to all contributor's data
    for user_data in all_contributors_data:
        user_data['rank'] = getUserRanking(all_contributors_data, user_data['username'])

    # We get all the campaign coountry sorted data
    all_campaign_country_statistics_data = getCampaignCountryData(id)

    campaign_stats = {}
    campaign_stats['all_contributors_data'] = all_contributors_data
    campaign_stats['all_campaign_country_statistics_data'] = all_campaign_country_statistics_data

    # Delete the files in the campaign directory
    stats_path = os.getcwd() + '/campaign_stats_files/' + str(campaign.id)
    files = glob.glob(stats_path + '/*')
    if len(files) > 0:
        for f in files:
            os.remove(f)
            # print('Deleted Existing Campaign file'+ f, file=sys.stderr)

    # We create the campaign stats directory if it does not exist
    if not os.path.exists(stats_path):
        os.makedirs(stats_path)

    # We build the campaign statistucs file here with the contributor stats
    # 1 - country contribution file

    campaign_name = campaign.campaign_name
    stats_file_directory = stats_path
    country_fields = ['rank', 'country', 'images_improved']
    country_stats_data = campaign_stats['all_campaign_country_statistics_data']

    country_csv_file = create_campaign_country_stats_csv(stats_file_directory, campaign_name,
                                                         country_fields, country_stats_data)

    # 2 - contributors file
    contributor_fields = ['rank', 'username', 'images_improved']
    contributor_stats_data = campaign_stats['all_contributors_data']
    
    contributor_csv_file = create_campaign_contributor_stats_csv(stats_file_directory,
                                                                 campaign_name,
                                                                 contributor_fields,
                                                                 contributor_stats_data)

    # 3 - We create the all_stats download file
    # The field in the stats file will be as thus
    all_stats_fields = ['username', 'file', 'edit_type', 'edit_action', 'country', 'depict_item',
                        'depict_prominent', 'caption_text', 'caption_language']
    campaign_all_stats_data = get_all_camapign_stats_data(id)
    campaign_all_stats_csv_file = create_campaign_all_stats_csv(stats_file_directory, campaign_name,
                                                                all_stats_fields, campaign_all_stats_data)

    # We prepare the campaign stats data to be sent to the next page (stats route)
    campaign_stats_data = {}
    campaign_stats_data['campaign_editors'] = campaign_editors
    campaign_stats_data['campaign_contributions'] = campaign_contributions
    campaign_stats_data['all_contributors_data'] = all_contributors_data
    campaign_stats_data['all_campaign_country_statistics_data'] = all_campaign_country_statistics_data
    campaign_stats_data['campaign_all_stats_csv_file'] = campaign_all_stats_csv_file

    campaign.campaign_participants = campaign_editors
    campaign.campaign_contributions = campaign_contributions
    if testDbCommitSuccess():
        print('Campaign info updated successfully!')
    return (render_template('campaign/campaign.html', title=gettext('Campaign - ') + campaign.campaign_name,
                            campaign=campaign,
                            campaign_manager=campaign.campaign_manager,
                            username=username,
                            session_language=session_language,
                            campaign_editors=campaign_editors,
                            campaign_contributions=campaign_contributions,
                            user_pref_lang=get_user_language_preferences(username),
                            current_user=current_user,
                            is_wiki_loves_campaign=campaign.campaign_type,
                            all_contributors_data=all_contributors_data,
                            current_user_rank=current_user_rank,
                            all_campaign_country_statistics_data=all_campaign_country_statistics_data,
                            current_user_images_improved=current_user_images_improved,
                            contributor_csv_file=contributor_csv_file,
                            country_csv_file=country_csv_file),
            campaign_stats_data)


@campaigns.route('/campaigns/<int:id>/stats')
def getCampaignStatsById(id):
    # We get the current user's user_name
    username = session.get('username', None)
    session_language = session.get('lang', None)
    if not session_language:
        session_language = 'en'
    campaign = Campaign.query.filter_by(id=id).first()
    if not campaign:
        flash(gettext('Campaign with id %(id)s does not exist', id=id), 'info')
        return redirect(url_for('campaigns.getCampaigns'))

    # We get the values returned from the campaign route and use here in the stats table
    # campaign_return_data: bundled campaign data from campaign route
    page, campaign_return_data = getCampaignById(id)

    return render_template('campaign/campaign_stats.html', title=gettext('Campaign - ') + campaign.campaign_name,
                           campaign=campaign,
                           session_language=session_language,
                           campaign_editors=campaign_return_data['campaign_editors'],
                           campaign_contributions=campaign_return_data['campaign_contributions'],
                           user_pref_lang=get_user_language_preferences(username),
                           current_user=current_user,
                           all_contributors_data=campaign_return_data['all_contributors_data'],
                           all_campaign_country_statistics_data=campaign_return_data['all_campaign_country_statistics_data'],
                           username=username,
                           campaign_all_stats_csv_file=campaign_return_data['campaign_all_stats_csv_file'])


@campaigns.route('/campaigns/create', methods=['GET', 'POST'])
def CreateCampaign():
    # We get the current user's user_name
    username = session.get('username', None)
    session_language = session.get('lang', None)
    if not session_language:
        session_language = 'en'
    form = CampaignForm()
    if not username:
        session['next_url'] = request.url
        flash(gettext('You need to Login to create a campaign'), 'info')
        return redirect(url_for('campaigns.getCampaigns'))
    else:
        if form.is_submitted():
            form_categories = ",".join(request.form.getlist('categories'))
            # here we create a campaign
            # We add the campaign information to the database
            campaign = Campaign(
                campaign_name=form.campaign_name.data,
                categories=form_categories,
                start_date=datetime.strptime(form.start_date.data, '%Y-%m-%d'),
                campaign_manager=username,
                end_date=datetime.strptime(form.end_date.data, '%Y-%m-%d'),
                status=compute_campaign_status(form.end_date.data),
                short_description=form.short_description.data,
                long_description=form.long_description.data,
                creation_date=datetime.now().date(),
                depicts_metadata=form.depicts_metadata.data,
                campaign_image=form.campaign_image.data,
                captions_metadata=form.captions_metadata.data,
                campaign_type=form.campaign_type.data)
            db.session.add(campaign)
            # commit failed
            if testDbCommitSuccess():
                flash(gettext('Sorry %(campaign_name)s Could not be created, End Date required',
                              campaign_name=form.campaign_name.data), 'info')
            else:
                campaign_stats_path = str(campaign.id)
                stats_path = os.getcwd() + '/campaign_stats_files/' + campaign_stats_path
                if not os.path.exists(stats_path):
                    os.makedirs(stats_path)
                flash(gettext('%(campaign_name)s Campaign created!',
                              campaign_name=form.campaign_name.data), 'success')
                return redirect(url_for('campaigns.getCampaignById', id=campaign.id))
        return render_template('campaign/create_campaign.html', title=gettext('Create a campaign'),
                               form=form, datetime=datetime,
                               username=username,
                               session_language=session_language,
                               user_pref_lang=get_user_language_preferences(username),
                               current_user=current_user)


@campaigns.route('/campaigns/<int:id>/participate', methods=['GET', 'POST'])
def contributeToCampaign(id):
    
    # We get current user in sessions's username
    username = session.get('username', None)
    caption_languages = get_user_language_preferences(username)
    session_language = session.get('lang', None)
    if not session_language:
        session_language = 'en'
    # We select the campign whose id comes into the route
    campaign = Campaign.query.filter_by(id=id).first()
    return render_template('campaign/campaign_entry.html',
                           title=gettext('%(campaign_name)s - Contribute',
                                         campaign_name=campaign.campaign_name),
                           id=id,
                           session_language=session_language,
                           campaign=campaign,
                           username=username,
                           caption_languages=caption_languages,
                           user_pref_lang=get_user_language_preferences(username),
                           current_user=current_user)


@campaigns.route('/campaigns/<int:id>/update', methods=['GET', 'POST'])
def updateCampaign(id):
    # We get the current user's user_name
    username = session.get('username', None)
    session_language = session.get('lang', None)
    if not session_language:
        session_language = 'en'
    form = UpdateCampaignForm()
    if not username:
        flash(gettext('You need to Login to update a campaign'), 'info')
        return redirect(url_for('campaigns.getCampaigns'))
    else:
        # when the form is submitted, we update the campaign
        # TODO: Check if campaign is closed so that it cannot be edited again
        # This is a potential issue/Managerial
        if form.is_submitted():
            campaign = Campaign.query.filter_by(id=id).first()
            campaign.campaign_name = form.campaign_name.data
            campaign.campaign_manager = username
            campaign.short_description = form.short_description.data
            campaign.long_description = form.long_description.data
            campaign.depicts_metadata = form.depicts_metadata.data
            campaign.captions_metadata = form.captions_metadata.data
            campaign.categories = form.categories.data
            campaign.start_date = datetime.strptime(form.start_date.data, '%Y-%m-%d')
            campaign.campaign_image = form.campaign_image.data
            campaign.campaign_type = form.campaign_type.data
            campaign.end_date = datetime.strptime(form.end_date.data, '%Y-%m-%d')
            if testDbCommitSuccess():
                flash(gettext('Please enter an End Date for this Campaign!'), 'danger')
            else:
                flash(gettext('Update Succesfull !'), 'success')
                return redirect(url_for('campaigns.getCampaignById', id=id))
        # User requests to edit so we update the form with Campaign details
        elif request.method == 'GET':
            # we get the campaign data to place in form fields
            campaign = Campaign.query.filter_by(id=id).first()

            if campaign.campaign_manager != username:
                flash(gettext('You cannot update this campaign, Contact Manager User:%(campaign_manager)s ',
                              campaign_manager=campaign.campaign_manager), 'info')
                return redirect(url_for('campaigns.getCampaignById', id=id))
            form.campaign_name.data = campaign.campaign_name
            form.short_description.data = campaign.short_description
            form.long_description.data = campaign.long_description
            form.categories.data = campaign.categories
            form.start_date.data = campaign.start_date
            form.depicts_metadata.data = campaign.depicts_metadata
            form.campaign_image.data = campaign.campaign_image
            form.captions_metadata.data = campaign.captions_metadata
            form.campaign_type.data = campaign.campaign_type
            form.end_date.data = campaign.end_date
        else:
            flash(gettext('Booo! %(campaign_name)s Could not be updated!',
                          campaign_name=form.campaign_name.data), 'danger')
        return render_template('campaign/update_campaign.html',
                               title=gettext('%(campaign_name)s - Update',
                                             campaign_name=campaign.campaign_name),
                               campaign=campaign,
                               form=form,
                               session_language=session_language,
                               user_pref_lang=get_user_language_preferences(username),
                               current_user=current_user,
                               username=username)


@campaigns.route('/api/get-campaign-categories', methods=['GET', 'POST'])
def getCampaignCategories():
    # we get the campaign_id from the route request
    campaign_id = request.args.get('campaign')

    # We get the campaign categories
    campaign = Campaign.query.filter_by(id=campaign_id).first()
    return campaign.categories


@campaigns.route('/api/post-contribution', methods=['POST', 'GET'])
def postContribution():
    contrib_data = request.data.decode('utf8')
    contrib_data_list = []
    contrib_data_list = json.loads(contrib_data)
    username = session.get('username', None)
    campaign_id = contrib_data_list[0]['campaign_id']
    if not username:
        flash(gettext('You need to login to participate'), 'info')
        # User is not logged in so we set the next url to redirect them after login
        session['next_url'] = request.url
        return redirect(url_for('campaigns.contributeToCampaign', id=campaign_id))
    else:
        contrib_list = []
        for data in contrib_data_list:
            contribution = Contribution(username=username,
                                        campaign_id=int(campaign_id),
                                        file=data['image'],
                                        edit_action=data['edit_action'],
                                        edit_type=data['edit_type'],
                                        country=data['country'],
                                        depict_item=data.get('depict_item'),
                                        depict_prominent=data.get('depict_prominent'),
                                        caption_language=data.get('caption_language'),
                                        caption_text=data.get('caption_text'))
            contrib_list.append(contribution)
        for contrib in contrib_list:
            db.session.add(contrib)
        if testDbCommitSuccess():
            return("Failure")
        else:
            return("Success!")
    return("Failure")


@campaigns.route('/api/update-campaign-images/<int:id>', methods=['POST', 'GET'])
def UpdateCampaignImagesCount(id):

    # We get the data from request and convert it to json
    images_data = json.loads(request.data.decode('utf8'))
    campaign = Campaign.query.filter_by(id=1).first()
    # We get the campaign images count and cast before including that into db
    campaign_images = int(images_data['campaign_images'])
    campaign.campaign_images = campaign_images
    if testDbCommitSuccess():
        return("Failure")
    else:
        return("Success!")
    return("Failure")


@campaigns.route('/campaigns/<int:id>/contrib_stats_download/<string:filename>', methods=['GET', 'POST'])
def downloadContributionStats(id, filename):
    if filename:
        return send_file(os.getcwd() + '/campaign_stats_files/' + str(id) + '/' + filename,
                         as_attachment=True, cache_timeout=0, last_modified=True)
    else:
        flash('Download may be unavailable now', 'info')


@campaigns.route('/campaigns/<int:id>/country_stats_download/<string:filename>', methods=['GET', 'POST'])
def downloadCountryStats(id, filename):
    if filename:
        return send_file(os.getcwd() + '/campaign_stats_files/' + str(id) + '/' + filename,
                         as_attachment=True, cache_timeout=0, last_modified=True)
    else:
        flash('Download may be unavailable now', 'info')


@campaigns.route('/campaigns/<int:id>/all_stats_download/<string:filename>', methods=['GET', 'POST'])
def downloadAllCampaignStats(id, filename):
    if filename:
        return send_file(os.getcwd() + '/campaign_stats_files/' + str(id) + '/' + filename,
                         as_attachment=True, cache_timeout=0, last_modified=True)
    else:
        flash('Download may be unavailable now', 'info')
