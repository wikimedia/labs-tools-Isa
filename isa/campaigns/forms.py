from flask_wtf import FlaskForm

from wtforms import BooleanField, SelectField, StringField, SubmitField, widgets, Label, DecimalField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange


class CampaignForm(FlaskForm):
    campaign_name = StringField('Campaign Name * ', validators=[DataRequired(),
                                Length(min=2, max=20)])
    short_description = StringField('Short description of Campaign', widget=widgets.TextArea())
    manager_name = StringField('Campaign Manager Name', validators=[Length(min=2, max=12)])
    start_date = DateField('Start Date *', id='datepick1',
                           format='%Y-%m-%d', validators=[InputRequired()])
    end_date = DateField('Close Date *', id='datepick2', format='%Y-%m-%d')
    categories = SelectField(validators=[DataRequired()], choices=[])
    categories_depth = DecimalField('Specify a category depth',
                                    validators=[NumberRange(min=0, max=5, message='Max depth is 5')])
    depicts_metadata = BooleanField('Depicts')
    captions_metadata = BooleanField('Captions')
    campaign_type = BooleanField('This is a Wiki Loves Campaign')
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
    end_date = DateField('Close Date *', id='datepick2', format='%Y-%m-%d')
    categories = SelectField(validators=[DataRequired()], choices=[])
    categories_depth = DecimalField('Modify a category depth',
                                    validators=[NumberRange(min=0.0, max=5.0, message='Max depth is 5')])
    depicts_metadata = BooleanField('Depicts')
    captions_metadata = BooleanField('Captions')
    campaign_type = BooleanField('This is a Wiki Loves Campaign')
    long_description = StringField('Long description of Campaign(full about info)',
                                   widget=widgets.TextArea())
    submit = SubmitField('Update Campaign')


class CampaignDepictsSearchForm(FlaskForm):
    depicts = SelectField(validators=[DataRequired()], choices=[])
    lang = SelectField(validators=[DataRequired()], choices=[('fr', 'fr'), ('en', 'en'), ('de', 'de')])
    submit = SubmitField('Save')


class CampaignCaptionsForm(FlaskForm):
    image_label = StringField('image here')
    caption = StringField(widget=widgets.TextArea())
    submit = SubmitField('Save')
