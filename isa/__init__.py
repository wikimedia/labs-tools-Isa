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
from celery import Celery
from celery import Task
from flask_migrate import Migrate


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
app.config['SQLALCHEMY_PRE_PING'] = True
app.config['SQLALCHEMY_TRACK_OPTIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600
app.config['SQLALCHEMY_POOL_SIZE'] = 1
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20
# We hook babel to our app


def get_locale():
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    return session.get('lang', 'en')


babel = Babel(app)
babel.init_app(app, locale_selector=get_locale)


@app.before_request
def before_request():
    try:
        db.session.execute("SELECT 1;")
        db.session.commit()
    except Exception:
        db.session.rollback()
    # Update session language
    get_locale()

    if "ISA_DEV" in app.config and app.config["ISA_DEV"]:
        session['username'] = "Dev"


db = SQLAlchemy(app)
migrate = Migrate()

migrate.init_app(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'main.home'
login_manager.login_message = 'You Need to Login to Access This Page!'
login_manager.login_message_category = 'danger'

CSRFProtect(app)


def celery_init_app(app):
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


celery_app = celery_init_app(app)

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

    return dict(languages=sorted(languages))
