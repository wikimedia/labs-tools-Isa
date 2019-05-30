from flask_wtf import FlaskForm

from wtforms import BooleanField, SelectField, StringField, SubmitField, widgets, Label, DecimalField, HiddenField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange


class CampaignForm(FlaskForm):
    campaign_name = StringField(validators=[DataRequired(),
                                Length(min=2, max=20)])
    short_description = StringField(widget=widgets.TextArea())
    start_date = DateField(id='datepick1',
                           format='%Y-%m-%d', validators=[InputRequired()])
    end_date = DateField(id='datepick2', format='%Y-%m-%d')
    categories = HiddenField(validators=[DataRequired()])
    depicts_metadata = BooleanField()
    captions_metadata = BooleanField()
    campaign_type = BooleanField()
    long_description = StringField(widget=widgets.TextArea())
    submit = SubmitField()


class UpdateCampaignForm(FlaskForm):
    campaign_name = StringField('Campaign Name', validators=[DataRequired(),
                                Length(min=2, max=20)])
    short_description = StringField('Short description of Campaign', widget=widgets.TextArea())
    start_date = DateField('Start Date ', id='datepick1',
                           format='%Y-%m-%d', validators=[InputRequired()])
    end_date = DateField('Close Date ', id='datepick2', format='%Y-%m-%d')
    categories = HiddenField(validators=[DataRequired()])
    depicts_metadata = BooleanField('Depicts')
    captions_metadata = BooleanField('Captions')
    campaign_type = BooleanField('This is a Wiki Loves Campaign')
    long_description = StringField('Long description of Campaign(full about info)',
                                   widget=widgets.TextArea())
    submit = SubmitField('Update Campaign')


class CampaignDepictsSearchForm(FlaskForm):
    depicts = SelectField(validators=[DataRequired()], choices=[])
    sub_categories = StringField()
    lang = SelectField(validators=[DataRequired()], choices=[('fr', 'fr'), ('en', 'en'), ('de', 'de')])
    submit = SubmitField('Save')


class CampaignCaptionsForm(FlaskForm):
    image_label = StringField()
    sub_categories = StringField()
    caption = StringField(widget=widgets.TextArea())
    submit = SubmitField('Save')
