
from isa import db
from datetime import datetime

class User( db.Model ):
    id = db.Column( db.Integer, primary_key=True )
    username = db.Column( db.String( 20 ), unique=True, nullable=False )
    pref_lang = db.Column( db.String( 15 ), unique=True, nullable=False )
    contributions = db.Column( db.Integer, default=0 )
    campaigns = db.relationship('Campaign', backref='works_on', lazy=True)
    def __repr__( self ):
        # This is what is shown when object is printed
        return f"User( { self.username }, { self.pref_lang }, { self.contributions } )"

class Campaign( db.Model ):
    id = db.Column( db.Integer, primary_key=True )
    campaign_country = db.Column( db.String( 15 ), unique=True, nullable=False )
    campaign_name = db.Column( db.String( 15 ), unique=True, nullable=False )
    start_date = db.Column( db.String( 15 ), nullable=False, default=datetime.utcnow )
    end_date = db.Column( db.String( 15 ), nullable=False, default=datetime.utcnow )
    status = db.Column ( db.Boolean, nullable=False, default=True )
    description = db.Column( db.Text, nullable=False )
    user_id = db.Column( db.Integer, db.ForeignKey( 'user.id'), nullable=False )
    def __repr__( self ):
        # This is what is shown when object is printed
        return f"Campaign(  {self.campaign_name}, {self.campaign_country}, {self.status}, {self.start_date}, {self.end_date} )"
