from flask_wtf import FlaskForm

from isa.utils.languages import getLanguages
from wtforms import SelectField, SubmitField

from wtforms.validators import DataRequired


class CaptionsLanguageForm(FlaskForm):
    language_select_1 = SelectField(choices=getLanguages())
    language_select_2 = SelectField(choices=getLanguages())
    language_select_3 = SelectField(choices=getLanguages())
    language_select_4 = SelectField(choices=getLanguages())
    language_select_5 = SelectField(choices=getLanguages())
    language_select_6 = SelectField(choices=getLanguages())
    submit = SubmitField()
