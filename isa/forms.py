from flask_wtf import FlaskForm
from datetime import datetime
from wtforms import StringField, TextField, SubmitField, RadioField, DateField, SelectField
from wtforms.validators import DataRequired, Length
from wtforms.widgets import TextArea
import pycountry

Countries = [ ('-1', '-----'),
            ('rw', 'Rwanda'),
            ('den', 'Denmark'),
            ('ben', 'Benin'),
            ('cm', 'Cameroon')  ]

class CampaignForm( FlaskForm ):
    campaign_name = StringField('Campaign Name',
                    validators=[DataRequired(), Length(min=2, max=20)])
    description = StringField('Description', widget=TextArea())
    categories = StringField('Categories', widget=TextArea())
    campaign_country = SelectField(
            'Country',
            choices = [(country.alpha_2, country.name) for country in pycountry.countries] )
    start_date = DateField('Start date', default=datetime.utcnow )
    end_date = DateField('End date', default=datetime.utcnow )
    status = example = RadioField('Status', choices=[('True','Closed'),('Flase','Open')])
    submit = SubmitField('Create Campaign')
