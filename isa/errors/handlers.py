from flask import Blueprint, render_template, session

errors = Blueprint('errors', __name__)


@errors.app_errorhandler(404)
def error_404(error):
    session_language = session.get('lang', None)
    if not session_language:
        session_language = 'en'
    return render_template('errors/404.html',
                           title='ISA-404',
                           session_language=session_language), 404


@errors.app_errorhandler(403)
def error_403(error):
    session_language = session.get('lang', None)
    if not session_language:
        session_language = 'en'
    return render_template('errors/403.html',
                           title='ISA-403',
                           session_language=session_language), 403


@errors.app_errorhandler(500)
def error_500(error):
    session_language = session.get('lang', None)
    if not session_language:
        session_language = 'en'
    return render_template('errors/500.html',
                           title='ISA-500',
                           session_language=session_language), 500
