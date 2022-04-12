from flask_wtf import FlaskForm

from isa import gettext
from isa.utils.languages import getLanguages
from wtforms import SelectField, SubmitField


class LanguageForm(FlaskForm):
    # Prefix labels with code to allow them to be picked up when
    # searching.
    languages = [
        (code, "{} - {}".format(code, name))
        for code, name in getLanguages()
    ]

    caption_languages = languages[:]
    caption_languages.insert(0, ("", ""))
    caption_language_select_1 = SelectField(choices=caption_languages)
    caption_language_select_2 = SelectField(choices=caption_languages)
    caption_language_select_3 = SelectField(choices=caption_languages)
    caption_language_select_4 = SelectField(choices=caption_languages)
    caption_language_select_5 = SelectField(choices=caption_languages)
    caption_language_select_6 = SelectField(choices=caption_languages)

    depicts_languages = languages[:]
    depicts_languages.insert(0, ("", gettext("Same as interface")))
    depicts_language_select = SelectField(choices=depicts_languages)
    submit = SubmitField()
