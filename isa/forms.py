
from flask_wtf import FlaskForm
import pycountry

from wtforms import BooleanField, SelectField, StringField, SubmitField, widgets
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, InputRequired, Length


class CampaignForm(FlaskForm):
    campaign_name = StringField('Campaign Name * ', validators=[DataRequired(),
                                Length(min=2, max=20)])
    short_description = StringField('Short description of Campaign', widget=widgets.TextArea())
    manager_name = StringField('Campaign Manager Name', validators=[DataRequired(),
                               Length(min=2, max=12)])
    start_date = DateField('Start Date *', id='datepick1',
                           format='%Y-%m-%d', validators=[InputRequired()])
    end_date = DateField('Close Date *', id='datepick2',
                         format='%Y-%m-%d', validators=[InputRequired()])
    categories = StringField('Categories to use in this campaign',
                             widget=widgets.TextArea())
    depicts_metadata = BooleanField('Depicts')
    captions_metadata = BooleanField('Captions')
    long_description = StringField('Long description of Campaign(full about info)',
                                   widget=widgets.TextArea())
    submit = SubmitField('Publish Campaign')


class UpdateCampaignForm(FlaskForm):
    campaign_name = StringField('Campaign Name * ', validators=[DataRequired(),
                                Length(min=2, max=20)])
    short_description = StringField('Short description of Campaign', widget=widgets.TextArea())
    manager_name = StringField('Campaign Manager Name', validators=[DataRequired(),
                               Length(min=2, max=12)])
    start_date = DateField('Start Date *', id='datepick1',
                           format='%Y-%m-%d', validators=[InputRequired()])
    end_date = DateField('Close Date *', id='datepick2',
                         format='%Y-%m-%d', validators=[InputRequired()])
    categories = StringField('Categories to use in this campaign', widget=widgets.TextArea())
    depicts_metadata = BooleanField('Depicts')
    captions_metadata = BooleanField('Captions')
    long_description = StringField('Long description of Campaign(full about info)',
                                   widget=widgets.TextArea())
    submit = SubmitField('Update Campaign')
