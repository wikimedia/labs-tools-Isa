from flask import session
from flask_babel import Locale


def rtl_context_processor():
    """
    Context processor to inject 'is_rtl' variable into templates.

    This processor checks the 'session_language' from the session and determines
    if the current language is right-to-left (RTL). It then injects the 'is_rtl'
    variable into the template context, which can be used to conditionally apply
    RTL styles or logic in templates.
    
    """
    session_language = session.get('lang', 'en')
    is_rtl = Locale(session_language).text_direction == "rtl"
    return dict(is_rtl=is_rtl)
