import os

import yaml
from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel, gettext

from flask_login import LoginManager

app = Flask(__name__)

# Load configuration from YAML file
__dir__ = os.path.dirname(__file__)
app.config.update(
    yaml.safe_load(open(os.path.join(__dir__, 'config.yaml'))))

# Another secret key will be generated later
app.config['SQLALCHEMY_DATABASE_URI']
app.config['SECRET_KEY']

# We hook babel to our app
babel = Babel(app)


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
