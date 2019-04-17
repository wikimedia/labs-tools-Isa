from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
# Another secret key will be generated later
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = '92db213479becba241a5531916b4f857'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

from isa import routes
