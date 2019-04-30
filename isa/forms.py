
from flask_wtf import FlaskForm
import pycountry

from wtforms import SelectField, StringField, SubmitField, widgets
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, InputRequired, Length


class CampaignForm(FlaskForm):
    campaign_name = StringField('Campaign Name', validators=[DataRequired(),
                                Length(min=2, max=20)])
    description = StringField('Description', widget=widgets.TextArea())
    categories = StringField('Categories', widget=widgets.TextArea())
    start_date = DateField('Start Date', id='datepick1',
                           format='%Y-%m-%d', validators=[InputRequired()])
    end_date = DateField('End Date', id='datepick2',
                         format='%Y-%m-%d', validators=[InputRequired()])
    submit = SubmitField('Create Campaign')


class UpdateCampaignForm(FlaskForm):
    campaign_name = StringField('Campaign Name',
                                validators=[DataRequired(), Length(min=2, max=20)])
    description = StringField('Description', widget=widgets.TextArea())
    categories = StringField('Categories', widget=widgets.TextArea())
    start_date = DateField('Start Date', id='datepick1', validators=[InputRequired()])
    end_date = DateField('End Date', id='datepick2', validators=[InputRequired()])
    submit = SubmitField('Update')
