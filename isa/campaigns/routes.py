from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, session, Blueprint
from flask_login import current_user
import pycountry

from isa import db
from isa.campaigns.forms import CampaignForm, CampaignDepictsSearchForm, CampaignCaptionsForm, UpdateCampaignForm
from isa.get_category_items import get_category_items
from isa.models import Campaign, Contribution, User
from isa.campaigns.utils import (get_actual_image_file_names, get_all_campaign_images, constructEditContent,
                                 get_campaign_category_list, get_country_from_code, compute_campaign_status)
from isa.main.utils import testDbCommitSuccess
from isa.users.utils import get_user_language_preferences

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
    countries = [(country.alpha_2, country.name) for country in pycountry.countries]
    return render_template('campaign/campaign.html', title='Campaign - ' + campaign.campaign_name,
                           campaign=campaign,
                           campaign_manager=campaign_manager.username,
                           username=username,
                           campaign_editors=campaign_editors,
                           campaign_contributions=campaign_contributions,
                           user_pref_lang=get_user_language_preferences(username),
                           current_user=current_user,
                           countries=countries)


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
            # here we create a campaign
            # We add the campaign information to the database
            campaign = Campaign(
                campaign_name=form.campaign_name.data,
                categories=form.categories.data,
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
                flash('Sorry {} already exists'.format(
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
    # We get the current user's user_name
    username = session.get('username', None)
    # if not username:
    #     flash('You need to Login to participate', 'info')
    #     return redirect(url_for('campaigns.getCampaigns'))
    if False:
        pass
    else:
        campaign = Campaign.query.filter_by(id=id).first()
        current_user_id = User.query.filter_by(username='Eugene233').first().id
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
        all_campaign_image_names = get_actual_image_file_names(all_campaign_images)

        # When a form with depict statments is submitted, we process each and
        # register a contribution for each of the depicts
        if depicts_form.is_submitted() and depicts_form.submit.data:
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
        if captions_form.is_submitted() and captions_form.submit.data:
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
        return render_template('campaign/campaign_entry.html', title=campaign.campaign_name + ' - Contribute',
                               id=id,
                               captions_form=captions_form,
                               depicts_form=depicts_form,
                               all_campaign_image_names=all_campaign_image_names,
                               campaign=campaign,
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
            campaign = Campaign.query.filter_by(id=id).first()
            campaign.campaign_name = form.campaign_name.data
            campaign.short_description = form.short_description.data
            campaign.long_description = form.long_description.data
            campaign.manager_name = form.manager_name.data
            campaign.depicts_metadata = form.depicts_metadata.data
            campaign.captions_metadata = form.captions_metadata.data
            campaign.categories = form.categories.data
            campaign.start_date = form.start_date.data
            campaign.campaign_type = form.campaign_type.data
            campaign.end_date = form.end_date.data
            if testDbCommitSuccess():
                flash('Please check the country for this Campaign!', 'danger')
            else:
                flash('Updated Succesfull!', 'success')
                return redirect(url_for('campaigns.getCampaigns'))
        # User requests to edit so we update the form with Campaign details
        elif request.method == 'GET':
            # we get the campaign data to place in form fields
            campaign = Campaign.query.filter_by(id=id).first()
            form.campaign_name.data = campaign.campaign_name
            form.short_description.data = campaign.short_description
            form.long_description.data = campaign.long_description
            form.categories.data = campaign.categories
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
