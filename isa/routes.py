from flask import render_template
from isa import app

@app.route("/")
def home():
    return render_template( 'home.html' )