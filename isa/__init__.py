import os
from glob import glob
import json
import logging

import yaml
from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel, gettext
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
app = Flask(__name__)

# Load configuration from YAML file
__dir__ = os.path.dirname(__file__)
app.config.update(
    yaml.safe_load(open(os.path.join(__dir__, 'config.yaml'))))

# Another secret key will be generated later
app.config['SQLALCHEMY_DATABASE_URI']
app.config['SECRET_KEY']
app.config['TEMPLATES_AUTO_RELOAD']

# We hook babel to our app
babel = Babel(app)


@app.context_processor
def utility_processor():
    def translate(s):
        # Translate and JSON encode a string. Removes the leading and
        # trailing double quote that encoding adds.
        return(json.dumps(gettext(s))[1:-1])
    return {"_": translate}


@app.before_request
def before_request():
    # Update session language
    get_locale()

    if "ISA_DEV" in os.environ and os.environ["ISA_DEV"]:
        session['username'] = "Dev"


@babel.localeselector
def get_locale():
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    return session.get('lang', 'en')


db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.home'
login_manager.login_message = 'You Need to Login to Access This Page!'
login_manager.login_message_category = 'danger'

CSRFProtect(app)

# we import all our blueprint routes here
from isa.campaigns.routes import campaigns
from isa.main.routes import main
from isa.users.routes import users
from isa.errors.handlers import errors

# Here we register the various blue_prints of our app
app.register_blueprint(campaigns)
app.register_blueprint(main)
app.register_blueprint(users)
app.register_blueprint(errors)


@app.context_processor
def inject_language_choices():
    languages = ["en"]
    for language in os.scandir("isa/translations"):
        if language.name == "qqq":
            continue

        mo_file = glob("isa/translations/{}/LC_MESSAGES/*.mo".format(language.name))
        if mo_file:
            languages.append(language.name)

    return dict(languages=languages)
