from flask import render_template
from isa import app

@app.route( "/" )
def home():
    return render_template( 'home.html', title = 'Home' )

@app.route( "/campaigns" )
def getCampaigns():
    return render_template( 'campaigns.html', title = 'Home' )

@app.route( "/campaigns/<string:campaign_name>" )
def getCampaignById( campaign_name ):
    return render_template( 'campaign.html', title = 'Campaigns' )

@app.route( "/campaigns/create" )
def CreateCampaign():
    return render_template( 'create_campaign.html', title = 'Create a campaign' )

@app.route( "/campaigns/<string:campaign_name>/edit" )
def editCampaign( campaign_name ):
    return render_template( 'edit_campaign.html', title = 'Modify campaigns' )

@app.route( "/campaigns/<string:campaign_name>/entry" )
def contributeToCampaign( campaign_name ):
    return render_template( 'campaign_entry.html', title = 'Contribute' )

@app.route( "/login" )
def login():
    return 'login'