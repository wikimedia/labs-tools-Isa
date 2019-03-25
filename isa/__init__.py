from flask import Flask

app = Flask(__name__)
# Another secret key will be generated later
app.config['SECRET_KEY'] = '92db213479becba241a5531916b4f857'

# avoiding import errors with import name app
from isa import routes