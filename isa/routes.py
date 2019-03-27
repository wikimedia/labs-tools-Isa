from flask import render_template, redirect, url_for, flash
from isa import app
from datetime import datetime
from isa import db
from isa.models import User, Campaign
from isa.forms import CampaignForm

@app.route( "/" )
def home():
    return render_template( 'home.html', title = 'Home' )

@app.route( "/campaigns" )
def getCampaigns():
    campaigns = Campaign.query.all()
    return render_template( 'campaigns.html', title = 'Campaigns', campaigns=campaigns, today_date=datetime.utcnow )

@app.route( "/campaigns/<string:campaign_name>" )
def getCampaignById( campaign_name ):

    #  Here we will select campain with campaign_name and render its info
    return render_template( 'campaign.html', title = 'Campaigns' )

@app.route( "/campaigns/create", methods=['GET','POST'] )
def CreateCampaign():
    form = CampaignForm()
    if form.is_submitted():
        # We add the campaign information to the database
        # TODO: Add current userid for user who created campaign
        campaign = Campaign(
            campaign_country = form.campaign_country.data,
            campaign_name = form.campaign_name.data,
            start_date = form.start_date.data,
            end_date = form.end_date.data,
            status = bool( form.status.data ),
            description = form.description.data,
            user_id = 1
        )
        db.session.add( campaign )
        db.session.commit()
        flash( f'{ form.campaign_name.data } Campaign created!', 'success' )
        return redirect( url_for( 'getCampaigns' ) )
    return render_template( 'create_campaign.html', title = 'Create a campaign', form=form)

@app.route( "/campaigns/<string:campaign_name>/edit" )
def editCampaign( campaign_name ):
    return render_template( 'edit_campaign.html', title = 'Modify campaigns' )

@app.route( "/campaigns/<string:campaign_name>/entry" )
def contributeToCampaign( campaign_name ):
    return render_template( 'campaign_entry.html', title = 'Contribute' )

@app.route( "/login" )
def login():
    return 'login'