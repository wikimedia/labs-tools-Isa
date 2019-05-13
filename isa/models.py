from datetime import datetime

from flask_login import UserMixin

from isa import db, login_manager


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, index=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    pref_lang = db.Column(db.String(15), nullable=False)
    contrib = db.Column(db.Integer, default=0)
    campaigns = db.relationship('Campaign', backref='works_on', lazy=True)
    contributions = db.relationship('Contribution', backref='made', lazy=True)

    def __repr__(self):
        # This is what is shown when object is printed
        return "User({}, {}, {})".format(
               self.username,
               self.pref_lang,
               self.contributions)


class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)

    def __repr__(self):
        # This is what is shown when object is printed
        return "Contribution( {}, {})".format(
               self.user_id,
               self.campaign_id)

    def __getitem__(self, index):
        return self[index]


class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_name = db.Column(db.String(15), nullable=False)
    categories = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False,
                           default=datetime.now().strftime('%Y-%m-%d'))
    end_date = db.Column(db.Date, nullable=False,
                         default=datetime.now().strftime('%Y-%m-%d'))
    status = db.Column(db.Boolean, nullable=False, default=bool('False'))
    short_description = db.Column(db.Text, nullable=False)
    long_description = db.Column(db.Text, nullable=False)
    categories = db.Column(db.Text, nullable=False)
    campaign_type = db.Column(db.Boolean)
    manager_name = db.Column(db.String(15), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    depicts_metadata = db.Column(db.Boolean)
    captions_metadata = db.Column(db.Boolean)
    contribution = db.relationship('Contribution', backref='made_on', lazy=True)

    def __repr__(self):
        # This is what is shown when object is printed
        return "Campaign( {}, {}".format(
               self.campaign_name,
               self.categories,
               self.depicts_metadata,
               self.captions_metadata,
               self.start_date,
               self.end_date)
