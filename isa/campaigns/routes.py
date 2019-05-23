from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, session, Blueprint
from flask_login import current_user
import sys
import json

from isa import db
from isa.campaigns.forms import CampaignForm, CampaignDepictsSearchForm, CampaignCaptionsForm, UpdateCampaignForm
from isa.get_category_items import get_category_items
from isa.models import Campaign, Contribution, User
from isa.campaigns.utils import (get_actual_image_file_names, get_all_campaign_images, constructEditContent,
                                 get_campaign_category_list, get_country_from_code, compute_campaign_status,
                                 buildCategoryObject)
from isa.main.utils import testDbCommitSuccess
from isa.users.utils import (get_user_language_preferences,
                             getAllUsersContributionsPerCampaign, getUserRanking, getCurrentUserImagesImproved)

campaigns = Blueprint('campaigns', __name__)


@campaigns.route('/campaigns')
def getCampaigns():
    campaigns = Campaign.query.all()
    username = session.get('username', None)
    return render_template('campaign/campaigns.html',
                           title='Campaigns',
                           username=username,
                           campaigns=campaigns,
                           today_date=datetime.date(datetime.utcnow()),
                           datetime=datetime,
                           user_pref_lang=get_user_language_preferences(username),
                           current_user=current_user)


@campaigns.route('/campaigns/<int:id>')
def getCampaignById(id):
    # We get the current user's user_name
    username = session.get('username', None)
    campaign = Campaign.query.filter_by(id=id).first()
    if not campaign:
        flash('Campaign with id {} does not exist'.format(id), 'info')
        return redirect(url_for('campaigns.getCampaigns'))

    # We select the campaign and the manager here
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

    # We now obtain the ranking for all the users in the system and their files improved
    all_camapign_users_list = []
    #  We iterate the individual participants id in a campaign and get the user info
    for user_id in campaign_users_ids_set:
        user = User.query.filter_by(id=user_id).first()
        all_camapign_users_list.append(user)

    # We get the users and their contribution data
    all_contributors_data = getAllUsersContributionsPerCampaign(all_camapign_users_list, id)
    current_user_rank = getUserRanking(all_contributors_data, username)
    current_user_images_improved = getCurrentUserImagesImproved(all_contributors_data, username)

    # We add rank to all contributor's data
    for user_data in all_contributors_data:
        user_data['rank'] = getUserRanking(all_contributors_data, user_data['username'])
    return render_template('campaign/campaign.html', title='Campaign - ' + campaign.campaign_name,
                           campaign=campaign,
                           campaign_manager=campaign_manager.username,
                           username=username,
                           campaign_editors=campaign_editors,
                           campaign_contributions=campaign_contributions,
                           user_pref_lang=get_user_language_preferences(username),
                           current_user=current_user,
                           is_wiki_loves_campaign=campaign.campaign_type,
                           all_contributors_data=all_contributors_data,
                           current_user_rank=current_user_rank,
                           current_user_images_improved=current_user_images_improved)


@campaigns.route('/campaigns/create', methods=['GET', 'POST'])
def CreateCampaign():
    # We get the current user's user_name
    username = session.get('username', None)
    if not username:
        flash('You need to Login to create a campaign', 'info')
        return redirect(url_for('campaigns.getCampaigns'))
    else:
        if username:
            current_user_id = User.query.filter_by(username=username).first().id
        else:
            # TODO: We have to decide which user should own arbitrary campaigns
            current_user_id = User.query.filter_by(username='Eugene233').first().id
        form = CampaignForm()
        if form.is_submitted():
            form_categories = ",".join(request.form.getlist('categories'))
            # here we create a campaign
            # We add the campaign information to the database
            campaign = Campaign(
                campaign_name=form.campaign_name.data,
                categories=form_categories,
                categories_depth=int(form.categories_depth.data),
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                status=compute_campaign_status(form.end_date.data),
                short_description=form.short_description.data,
                long_description=form.long_description.data,
                depicts_metadata=form.depicts_metadata.data,
                captions_metadata=form.captions_metadata.data,
                campaign_type=form.campaign_type.data,
                manager_name=form.manager_name.data,
                user_id=current_user_id)
            db.session.add(campaign)
            # commit failed
            if testDbCommitSuccess():
                flash('Sorry {} Could not be created'.format(
                      form.campaign_name.data), 'danger')
            else:
                flash('{} Campaign created!'.format(form.campaign_name.data), 'success')
                return redirect(url_for('campaigns.getCampaigns'))
        return render_template('campaign/create_campaign.html', title='Create a campaign',
                               form=form, datetime=datetime,
                               username=username,
                               user_pref_lang=get_user_language_preferences(username),
                               current_user=current_user)


@campaigns.route('/campaigns/<int:id>/participate', methods=['GET', 'POST'])
def contributeToCampaign(id):
    
    # We get current user in sessions's username
    username = session.get('username', None)

    # We select the campign whose id comes into the route
    campaign = Campaign.query.filter_by(id=id).first()
    
    # contribution = Contribution(
    captions_form = CampaignCaptionsForm(prefix="captions_form")
    depicts_form = CampaignDepictsSearchForm(prefix="depicts_form")

    campaign_categories = get_campaign_category_list(campaign.categories)
    # will homd the data about the categores
    campaign_partcicipate_data = []
    # we now get content through api call for the images
    for category in campaign_categories:
        category_data = get_category_items(category)
        campaign_partcicipate_data.append(category_data)
    all_campaign_images = get_all_campaign_images(campaign_partcicipate_data)

    # We take only the images which have the following extensions
    #  .png .jpeg .jpg .svg
    all_campaign_desired_images = []
    for image in all_campaign_images:
        image_lower = image.lower()
        if image_lower.endswith('.png') or image_lower.endswith('.jpeg') \
           or image_lower.endswith('.jpg') or image_lower.endswith('.svg'):
            all_campaign_desired_images.append(image)
    # When a form with depict statments is submitted, we process each and
    # register a contribution for each of the depicts
    if depicts_form.is_submitted():
        # We check if there is a user in session
        if not username:
            flash('You need to login to participate', 'info')
            # User is not logged in so we set the next url to redirect them after login
            session['next_url'] = request.url
            return redirect(url_for('campaigns.contributeToCampaign', id=id))
        else:
            current_user_id = User.query.filter_by(username=username).first().id
            depicts_data = constructEditContent(request.form.getlist('depicts_form-depicts'))
            if not depicts_data:
                flash('please add at least a depict statement', 'info')
            else:
                #  we iterate the depicsts data and create a contribution for each
                for depict in depicts_data:
                    contribution = Contribution(
                        user_id=current_user_id,
                        campaign_id=id,
                        edit_type='depicts',
                        file=depict[1],
                        edit_acton='Add',
                        edit_content=depict[0]
                    )
                    db.session.add(contribution)
                    # commit failed
                    if testDbCommitSuccess():
                        flash('Sorry edit could not be registered', 'danger')
                    else:
                        flash('Thanks for Your contribution', 'success')
                        # We make sure that the form data does not remain in browser
                        return redirect(url_for('campaigns.contributeToCampaign', id=id))
    if captions_form.is_submitted() and captions_form.submit.data:
        # We check if there is a user in session
        if not username:
            flash('You need to login to participate', 'info')
            # User is not logged in so we set the next url to redirect them after login
            session['next_url'] = request.url
            return redirect(url_for('campaigns.contributeToCampaign', id=id))
        else:
            captions_image_label = request.form.get('captions_form-image_label')
            caption_text = request.form.get('captions_form-caption')
            if captions_image_label and caption_text:
                contribution = Contribution(
                    user_id=current_user_id,
                    campaign_id=id,
                    edit_type='caption',
                    file=captions_image_label,
                    edit_acton='Add',
                    edit_content=caption_text
                )
                db.session.add(contribution)
                # commit failed
                if testDbCommitSuccess():
                    flash('Sorry edit could not be registered', 'danger')
                else:
                    flash('Thanks for Your contribution', 'success')
                    # We make sure that the form data does not remain in browser
                    return redirect(url_for('campaigns.contributeToCampaign', id=id))
    return render_template('campaign/campaign_entry.html', title=campaign.campaign_name + ' - Contribute',
                           id=id,
                           captions_form=captions_form,
                           depicts_form=depicts_form,
                           all_campaign_desired_images=all_campaign_desired_images,
                           campaign=campaign,
                           username=username,
                           campaign_partcicipate_data=campaign_partcicipate_data,
                           user_pref_lang=get_user_language_preferences(username),
                           current_user=current_user)


@campaigns.route('/campaigns/<int:id>/update', methods=['GET', 'POST'])
def updateCampaign(id):
    # We get the current user's user_name
    username = session.get('username', None)
    form = UpdateCampaignForm()
    if not username:
        flash('You need to Login to update a campaign', 'danger')
        return redirect(url_for('campaigns.getCampaigns'))
    else:
        # when the form is submitted, we update the campaign
        # TODO: Check if campaign is closed so that it cannot be edited again
        # This is a potential issue/Managerial
        if form.is_submitted():
            # we get the list of catefories from request
            form_categories = ",".join(request.form.getlist('categories'))

            campaign = Campaign.query.filter_by(id=id).first()
            campaign.campaign_name = form.campaign_name.data
            campaign.short_description = form.short_description.data
            campaign.long_description = form.long_description.data
            campaign.manager_name = form.manager_name.data
            campaign.depicts_metadata = form.depicts_metadata.data
            campaign.captions_metadata = form.captions_metadata.data
            campaign.categories = form_categories
            campaign.categories_depth = int(form.categories_depth.data)
            campaign.start_date = form.start_date.data
            campaign.campaign_type = form.campaign_type.data
            campaign.end_date = form.end_date.data
            if testDbCommitSuccess():
                flash('Please enter an End Date for this Campaign!', 'danger')
            else:
                flash('Update Succesfull !', 'success')
                return redirect(url_for('campaigns.getCampaignById', id=id))
        # User requests to edit so we update the form with Campaign details
        elif request.method == 'GET':
            # we get the campaign data to place in form fields
            campaign = Campaign.query.filter_by(id=id).first()
            form.campaign_name.data = campaign.campaign_name
            form.short_description.data = campaign.short_description
            form.long_description.data = campaign.long_description
            form.categories.data = campaign.categories
            form.categories_depth.data = int(campaign.categories_depth)
            form.manager_name.data = campaign.manager_name
            form.start_date.data = campaign.start_date
            form.depicts_metadata.data = campaign.depicts_metadata
            form.captions_metadata.data = campaign.captions_metadata
            form.campaign_type.data = campaign.campaign_type
            form.end_date.data = campaign.end_date
        else:
            flash('Booo! {} Could not be updated!'.format(
                form.campaign_name.data), 'danger')
        return render_template('campaign/update_campaign.html', title=campaign.campaign_name + ' - Update',
                               campaign=campaign,
                               form=form,
                               user_pref_lang=get_user_language_preferences(username),
                               current_user=current_user,
                               username=username)


@campaigns.route('/api/get-campaign-categories', methods=['GET', 'POST'])
def getCampaignCategories():
    # we get the campaign_id from the route request
    campaign_id = request.args.get('campaign')
    # We get the current user's user_name
    username = session.get('username', None)
    if not username:
        return '<stong> Sorry! This Data is available for logged in Users only</strong>'
    else:
        # We get the campaign categories
        campaign = Campaign.query.filter_by(id=campaign_id).first()
        campaign_object = {}
        campaign_object['name'] = campaign.campaign_name
        campaign_object['categories'] = {}  # We store each category here

        categories_objects_array = []
        for category in campaign.categories.split(','):
            categories_objects_array.append(buildCategoryObject(category))
        campaign_object['categories'] = categories_objects_array
        return json.dumps(campaign_object)
