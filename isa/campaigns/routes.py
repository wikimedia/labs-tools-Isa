import os
import csv
import sys
import json
import shutil
import glob
import mwoauth

from io import StringIO
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, session, Blueprint, send_file
from flask_login import current_user

from isa import app, db, gettext
from isa.campaigns.forms import CampaignForm
from isa.campaigns.utils import (convert_latin_to_english, get_table_stats, get_campaign_category_list,
                                 get_country_from_code, compute_campaign_status,
                                 create_campaign_country_stats_csv, create_campaign_contributor_stats_csv,
                                 create_campaign_all_stats_csv, get_all_camapign_stats_data,
                                 get_campaign_country_data, make_edit_api_call, generate_csrf_token)
from isa.main.utils import commit_changes_to_db
from isa.models import Campaign, Contribution, User
from isa.users.utils import (get_user_language_preferences, get_all_users_contribution_data_per_campaign,
                             get_user_ranking, get_current_user_images_improved)
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
    
    # We now get the contributor count for this campaign
    for contrib in all_contributions:
        if (contrib.campaign_id == campaign.id):
            campaign_contributions += 1

    campaign_table_stats = get_table_stats(id, username)
    
    # Delete the files in the campaign directory
    stats_path = os.getcwd() + '/campaign_stats_files/' + str(campaign.id)
    files = glob.glob(stats_path + '/*')
    if len(files) > 0:
        for f in files:
            os.remove(f)

    # We create the campaign stats directory if it does not exist
    if not os.path.exists(stats_path):
        os.makedirs(stats_path)

    # We build the campaign statistucs file here with the contributor stats
    # 1 - country contribution file

    campaign_name = campaign.campaign_name
    stats_file_directory = stats_path
    country_fields = ['rank', 'country', 'images_improved']
    country_stats_data = campaign_table_stats['all_campaign_country_statistics_data']

    country_csv_file = create_campaign_country_stats_csv(stats_file_directory, campaign_name,
                                                         country_fields, country_stats_data)

    # 2 - contributors file
    contributor_fields = ['rank', 'username', 'images_improved']
    contributor_stats_data = campaign_table_stats['all_contributors_data']
    
    current_user_images_improved = get_current_user_images_improved(contributor_stats_data, username)

    contributor_csv_file = create_campaign_contributor_stats_csv(stats_file_directory,
                                                                 campaign_name,
                                                                 contributor_fields,
                                                                 contributor_stats_data)
    campaign.campaign_participants = campaign_table_stats['campaign_editors']
    campaign.campaign_contributions = campaign_contributions
    if commit_changes_to_db():
        print('Campaign info updated successfully!')
    return (render_template('campaign/campaign.html', title=gettext('Campaign - ') + campaign.campaign_name,
                            campaign=campaign,
                            campaign_manager=campaign.campaign_manager,
                            username=username,
                            campaign_image="https://commons.wikimedia.org/wiki/Special:FilePath/" + campaign.campaign_image,
                            session_language=session_language,
                            campaign_editors=campaign_editors,
                            campaign_contributions=campaign_contributions,
                            current_user=current_user,
                            is_wiki_loves_campaign=campaign.campaign_type,
                            all_contributors_data=campaign_table_stats['all_contributors_data'],
                            current_user_rank=campaign_table_stats['current_user_rank'],
                            all_campaign_country_statistics_data=campaign_table_stats['all_campaign_country_statistics_data'],
                            current_user_images_improved=current_user_images_improved,
                            contributor_csv_file=contributor_csv_file,
                            country_csv_file=country_csv_file))


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

    stats_file_directory = os.getcwd() + '/campaign_stats_files/' + str(campaign.id)
    
    # We create the all_stats download file
    # The field in the stats file will be as thus
    all_stats_fields = ['username', 'file', 'edit_type', 'edit_action', 'country', 'depict_item',
                        'depict_prominent', 'caption_text', 'caption_language', 'date']
    campaign_all_stats_data = get_all_camapign_stats_data(id)
    campaign_all_stats_csv_file = create_campaign_all_stats_csv(stats_file_directory,
                                                                convert_latin_to_english(campaign.campaign_name),
                                                                all_stats_fields, campaign_all_stats_data)
    
    # We get the table stats from the campaign itself
    campaign_table_stats = get_table_stats(id, username)
    
    # We prepare the campaign stats data to be sent to the next page (stats route)
    all_campaign_stats_data = {}
    all_campaign_stats_data['campaign_editors'] = campaign.campaign_participants
    all_campaign_stats_data['campaign_contributions'] = campaign.campaign_contributions
    all_campaign_stats_data['all_contributors_data'] = campaign_table_stats['all_contributors_data']
    all_campaign_stats_data['all_campaign_country_statistics_data'] = campaign_table_stats['all_campaign_country_statistics_data']
    all_campaign_stats_data['campaign_all_stats_csv_file'] = campaign_all_stats_csv_file

    return render_template('campaign/campaign_stats.html', title=gettext('Campaign - ') + campaign.campaign_name,
                           campaign=campaign,
                           session_language=session_language,
                           campaign_editors=all_campaign_stats_data['campaign_editors'],
                           campaign_contributions=all_campaign_stats_data['campaign_contributions'],
                           current_user=current_user,
                           is_wiki_loves_campaign=campaign.campaign_type,
                           all_contributors_data=all_campaign_stats_data['all_contributors_data'],
                           all_campaign_country_statistics_data=all_campaign_stats_data['all_campaign_country_statistics_data'],
                           username=username,
                           campaign_all_stats_csv_file=all_campaign_stats_data['campaign_all_stats_csv_file'])


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
            campaign_end_date = None
            if form.end_date.data == '':
                campaign_end_date = None
            else:
                campaign_end_date = datetime.strptime(form.end_date.data, '%Y-%m-%d')
            campaign = Campaign(
                campaign_name=form.campaign_name.data,
                categories=form_categories,
                campaign_images=form.campaign_images.data,
                start_date=datetime.strptime(form.start_date.data, '%Y-%m-%d'),
                campaign_manager=username,
                end_date=campaign_end_date,
                status=compute_campaign_status(campaign_end_date),
                short_description=form.short_description.data,
                long_description=form.long_description.data,
                creation_date=datetime.now().date(),
                depicts_metadata=form.depicts_metadata.data,
                campaign_image=form.campaign_image.data,
                captions_metadata=form.captions_metadata.data,
                campaign_type=form.campaign_type.data)
            db.session.add(campaign)
            # commit failed
            if commit_changes_to_db():
                flash(gettext('Sorry %(campaign_name)s Could not be created',
                              campaign_name=form.campaign_name.data), 'info')
            else:
                campaign_stats_path = str(campaign.id)
                stats_path = os.getcwd() + '/campaign_stats_files/' + campaign_stats_path
                if not os.path.exists(stats_path):
                    os.makedirs(stats_path)
                flash(gettext('%(campaign_name)s Campaign created!',
                              campaign_name=form.campaign_name.data), 'success')
                return redirect(url_for('campaigns.getCampaignById', id=campaign.id))
        return render_template('campaign/campaign-form.html', title=gettext('Create a campaign'),
                               form=form, datetime=datetime,
                               username=username,
                               session_language=session_language,
                               current_user=current_user)


@campaigns.route('/campaigns/<int:id>/participate', methods=['GET', 'POST'])
def contributeToCampaign(id):
    
    # We get current user in sessions's username
    username = session.get('username', None)
    session_language = session.get('lang', None)
    if not session_language:
        session_language = 'en'
    # We select the campign whose id comes into the route
    campaign = Campaign.query.filter_by(id=id).first()
    return render_template('campaign/campaign_entry.html',
                           is_update=False,
                           title=gettext('%(campaign_name)s - Contribute',
                                         campaign_name=campaign.campaign_name),
                           id=id,
                           session_language=session_language,
                           caption_languages=get_user_language_preferences(username),
                           campaign=campaign,
                           username=username,
                           current_user=current_user)


@campaigns.route('/campaigns/<int:id>/update', methods=['GET', 'POST'])
def updateCampaign(id):
    # We get the current user's user_name
    username = session.get('username', None)
    session_language = session.get('lang', None)
    if not session_language:
        session_language = 'en'
    form = CampaignForm()
    if not username:
        flash(gettext('You need to Login to update a campaign'), 'info')
        return redirect(url_for('campaigns.getCampaigns'))
    else:
        # when the form is submitted, we update the campaign
        # TODO: Check if campaign is closed so that it cannot be edited again
        # This is a potential issue/Managerial
        if form.is_submitted():
            campaign_end_date = None
            if form.end_date.data == '':
                campaign_end_date = None
            else:
                campaign_end_date = datetime.strptime(form.end_date.data, '%Y-%m-%d')
            campaign = Campaign.query.filter_by(id=id).first()
            campaign.campaign_name = form.campaign_name.data
            campaign.campaign_manager = username
            campaign.short_description = form.short_description.data
            campaign.long_description = form.long_description.data
            campaign.depicts_metadata = form.depicts_metadata.data
            campaign.captions_metadata = form.captions_metadata.data
            campaign.categories = form.categories.data
            campaign.campaign_images = form.campaign_images.data
            campaign.start_date = datetime.strptime(form.start_date.data, '%Y-%m-%d')
            campaign.campaign_image = form.campaign_image.data
            campaign.campaign_type = form.campaign_type.data
            campaign.end_date = campaign_end_date
            if commit_changes_to_db():
                flash(gettext('Campaign update failed please try later!'), 'danger')
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
            form.campaign_images.data = campaign.campaign_images
            form.start_date.data = campaign.start_date
            form.depicts_metadata.data = campaign.depicts_metadata
            form.campaign_image.data = campaign.campaign_image
            form.captions_metadata.data = campaign.captions_metadata
            form.campaign_type.data = campaign.campaign_type
            form.end_date.data = campaign.end_date
        else:
            flash(gettext('Booo! %(campaign_name)s Could not be updated!',
                          campaign_name=form.campaign_name.data), 'danger')
        return render_template('campaign/campaign-form.html',
                               is_update=True,
                               title=gettext('%(campaign_name)s - Update',
                                             campaign_name=campaign.campaign_name),
                               campaign=campaign,
                               form=form,
                               session_language=session_language,
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
    contrib_options_list = []
    contrib_data_list = []
    contrib_data_list = json.loads(contrib_data)
    username = session.get('username', None)
    
    # The most recent rev_id will be stored in latest_base_rev_id
    # Default is 0 meaning there is none and the edit failed
    latest_base_rev_id = 0
    # We get the session and app credetials for edits on Commons

    csrf_token, api_auth_token = generate_csrf_token(app.config['CONSUMER_KEY'], app.config['CONSUMER_SECRET'],
                                                     session.get('access_token')['key'],
                                                     session.get('access_token')['secret'])
    
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
                                        caption_text=data.get('caption_text'),
                                        date=datetime.date(datetime.utcnow()))
            contrib_list.append(contribution)

        # We write the api_options for the contributions into a list
        for contrib_data in contrib_data_list:
            contrib_options_list.append(contrib_data['api_options'])

        for i in range(len(contrib_options_list)):
            # We make an api call with the current contribution data and get baserevid
            lastrevid = make_edit_api_call(csrf_token,
                                           api_auth_token,
                                           contrib_data_list[i])
            
            if lastrevid is not None:
                # We check if the previous edit was successfull
                # We then add the contribution to the db session
                db.session.add(contrib_list[i])
                
                # Check that there are still elements in the list in order to pop
                if len(contrib_options_list) > 1:
                    # We take out the first element of the data list
                    contrib_options_list.pop(0)

                    # We assign the baserevid of the next data list of api_options
                    # If there is a next element in the data list
                    next_api_options = contrib_options_list[0]
                    next_api_options['baserevid'] = lastrevid
            else:
                return("Failure")
            # We store the latest revision id to be sent to client
            latest_base_rev_id = lastrevid

        # We attempt to save the changes to db
        if commit_changes_to_db():
            return("Failure")
        else:
            return (str(latest_base_rev_id))
    return("Failure")


@campaigns.route('/api/update-campaign-images/<int:id>', methods=['POST', 'GET'])
def UpdateCampaignImagesCount(id):

    # We get the data from request and convert it to json
    images_data = json.loads(request.data.decode('utf8'))
    campaign = Campaign.query.filter_by(id=id).first()
    # We get the campaign images count and cast before including that into db
    campaign_images = int(images_data['campaign_images'])
    campaign.campaign_images = campaign_images
    if commit_changes_to_db():
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
