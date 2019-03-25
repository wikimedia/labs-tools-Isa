from flask import render_template
from isa import app

@app.route( "/" )
def home():
    return render_template( 'home.html' )

@app.route( "/campaigns" )
def getCampaigns():
    return render_template( 'campaigns.html' )

@app.route( "/campaigns/<string:campaign_name>" )
def getCampaignById( campaign_name ):
    return render_template( 'campaign.html' )

@app.route( "/campaigns/create" )
def CreateCampaign():
    return render_template( 'create_campaign.html' )

@app.route( "/campaigns/<string:campaign_name>/edit" )
def editCampaign( campaign_name ):
    return render_template( 'edit_campaign.html' )

@app.route( "/campaigns/<string:campaign_name>/entry" )
def contributeToCampaign( campaign_name ):
    return render_template( 'campaign_entry.html' )