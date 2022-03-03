from flask_wtf import FlaskForm

from isa.utils.languages import getLanguages
from wtforms import SelectField, SubmitField


class CaptionsLanguageForm(FlaskForm):
    # Prefix labels with code to allow them to be picked up when
    # searching.
    languages = [
        (code, "{} - {}".format(code, name))
        for code, name in getLanguages()
    ]
    languages.insert(0, ("", ""))
    language_select_1 = SelectField(choices=languages)
    language_select_2 = SelectField(choices=languages)
    language_select_3 = SelectField(choices=languages)
    language_select_4 = SelectField(choices=languages)
    language_select_5 = SelectField(choices=languages)
    language_select_6 = SelectField(choices=languages)
    submit = SubmitField()
