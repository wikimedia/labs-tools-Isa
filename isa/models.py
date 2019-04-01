
from isa import db
from datetime import datetime

class User( db.Model ):
    id = db.Column( db.Integer, primary_key=True, index=True )
    username = db.Column( db.String( 20 ), unique=True, nullable=False )
    pref_lang = db.Column( db.String( 15 ), nullable=False )
    contrib = db.Column( db.Integer, default=0 )
    campaigns = db.relationship('Campaign', backref='works_on', lazy=True)
    contributions = db.relationship('Contribution', backref='made', lazy=True)    
    def __repr__( self ):
        # This is what is shown when object is printed
        return f"User( { self.username }, { self.pref_lang }, { self.contributions } )"

class Contribution( db.Model ):
    id = db.Column( db.Integer, primary_key=True )
    user_id = db.Column( db.Integer, db.ForeignKey( 'user.id'), nullable=False )
    campaign_id = db.Column( db.Integer, db.ForeignKey( 'campaign.id'), nullable=False )
    def __repr__( self ):
        # This is what is shown when object is printed
        return f"Contribution(  {self.user_id}, {self.campaign_id} )"
    def __getitem__(self, index):
        return self[index]

class Campaign( db.Model ):
    id = db.Column( db.Integer, primary_key=True )
    campaign_country = db.Column( db.String( 15 ), unique=True, nullable=False )
    campaign_name = db.Column( db.String( 15 ), unique=True, nullable=False )
    categories = db.Column( db.Text, nullable=False )
    start_date = db.Column( db.Date, nullable=False, default=datetime.now().strftime( "%Y-%m-%d" ) )
    end_date = db.Column( db.Date, nullable=False, default=datetime.now().strftime( "%Y-%m-%d" ) )
    status = db.Column ( db.Boolean, nullable=False, default=bool( 'False' ) )
    description = db.Column( db.Text, nullable=False )
    categories = db.Column( db.Text, nullable=False )
    user_id = db.Column( db.Integer, db.ForeignKey( 'user.id' ), nullable=False )
    contribution = db.relationship('Contribution', backref='made_on', lazy=True) 
    def __repr__( self ):
        # This is what is shown when object is printed
        return f"Campaign(  {self.campaign_name}, {self.campaign_country}, {self.status}, {self.start_date}, {self.end_date} )"