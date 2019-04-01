from flask_wtf import FlaskForm
from datetime import datetime
from wtforms import StringField, TextField, SubmitField, RadioField, SelectField, widgets
from wtforms.validators import DataRequired, Length, InputRequired
from wtforms.fields.html5 import  DateField
import pycountry
from isa.models import Campaign

class CampaignForm( FlaskForm ):
    campaign_name = StringField('Campaign Name',
                    validators=[ DataRequired(), Length( min=2, max=20 ) ] )
    description = StringField( 'Description', widget=widgets.TextArea() )
    categories = StringField( 'Categories', widget=widgets.TextArea() )
    campaign_country = SelectField( 'Country',
            choices = [(country.alpha_2, country.name) for country in pycountry.countries] )
    start_date = DateField( 'Start Date', id='datepick1',format="%Y-%m-%d", validators=[InputRequired()] )
    end_date = DateField( 'End Date', id='datepick2',format="%Y-%m-%d", validators=[InputRequired()] )
    submit = SubmitField('Create Campaign')

    def validate_camapain_name( self, campaign_name ):
        campaign_name = Campaign.query.filter_by( campaign_name = campaign_name.data )
        if campaign_name:
                raise ValidationError( 'Campaign Name already exists, Please choose another one' )

class UpdateCampaignForm( FlaskForm ):
    campaign_name = StringField('Campaign Name',
                    validators=[ DataRequired(), Length( min=2, max=20 ) ] )
    description = StringField( 'Description', widget=widgets.TextArea() )
    categories = StringField( 'Categories', widget=widgets.TextArea() )
    campaign_country = SelectField( 'Country',
            choices = [ (country.alpha_2, country.name ) for country in pycountry.countries] )
    start_date = DateField( 'Start Date', id='datepick1', validators=[InputRequired()] )
    end_date = DateField( 'End Date', id='datepick2', validators=[InputRequired()] )
    submit = SubmitField( 'Update' )

    def validate_camapain_name( self, campaign_name ):
        campaign_name = Campaign.query.filter_by( campaign_name = campaign_name.data )
        if campaign_name:
                raise ValidationError( 'Campaign Name already exists, Please choose another one' )