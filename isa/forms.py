from flask_wtf import FlaskForm
from datetime import datetime
from wtforms import StringField, TextField, SubmitField, RadioField, SelectField
from wtforms.validators import DataRequired, Length
from wtforms.widgets import TextArea
from wtforms.fields.html5 import DateField
import pycountry

class CampaignForm( FlaskForm ):
    campaign_name = StringField('Campaign Name',
                    validators=[ DataRequired(), Length( min=2, max=20 ) ] )
    description = StringField( 'Description', widget=TextArea() )
    categories = StringField( 'Categories', widget=TextArea() )
    campaign_country = SelectField( 'Country',
            choices = [(country.alpha_2, country.name) for country in pycountry.countries] )
    start_date = DateField( 'Start Date', format='%Y-%m-%d', default=datetime.now() )
    end_date = DateField( 'End Date', format='%Y-%m-%d', default=datetime.now() )
    status = example = RadioField('Status', choices=[('True','Closed'),('Flase','Open')])
    submit = SubmitField('Create Campaign')
