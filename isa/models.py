from datetime import datetime

from flask_login import UserMixin

from isa import db, login_manager


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, index=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    caption_languages = db.Column(db.String(25), nullable=False)
    contrib = db.Column(db.Integer, default=0)

    def __repr__(self):
        # This is what is shown when object is printed
        return "User({}, {})".format(
               self.username,
               self.caption_languages)


class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    file = db.Column(db.String(210), nullable=False)
    edit_type = db.Column(db.String(10), nullable=False)
    edit_action = db.Column(db.String(7), nullable=False)
    country = db.Column(db.String(50), nullable=False, default='')
    depict_item = db.Column(db.String(15), nullable=True)
    depict_prominent = db.Column(db.Boolean, nullable=True)
    caption_language = db.Column(db.String(5), nullable=True)
    caption_text = db.Column(db.String(200), nullable=True)
    date = db.Column(db.Date, nullable=False,
                     default=datetime.now().strftime('%Y-%m-%d'))

    def __repr__(self):
        # This is what is shown when object is printed
        return "Contribution( {}, {}, {},{},{},{})".format(
               self.username,
               self.campaign_id,
               self.file,
               self.edit_type,
               self.edit_action,
               self.country)

    def __getitem__(self, index):
        return self[index]


class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_name = db.Column(db.String(200), nullable=False)
    campaign_images = db.Column(db.Integer, default=0)
    campaign_contributions = db.Column(db.Integer, default=0)
    campaign_participants = db.Column(db.Integer, default=0)
    campaign_image = db.Column(db.String(200), nullable=True, default='')
    categories = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False,
                           default=datetime.now().strftime('%Y-%m-%d'))
    campaign_manager = db.Column(db.String(15), nullable=False)
    end_date = db.Column(db.Date, nullable=True,
                         default=None)
    status = db.Column(db.Boolean, nullable=False, default=bool('False'))
    short_description = db.Column(db.Text, nullable=False)
    long_description = db.Column(db.Text, nullable=False)
    categories = db.Column(db.Text, nullable=False)
    creation_date = db.Column(db.Date, nullable=True,
                              default=datetime.now().strftime('%Y-%m-%d'))
    campaign_type = db.Column(db.Boolean)
    depicts_metadata = db.Column(db.Boolean)
    captions_metadata = db.Column(db.Boolean)
    contribution = db.relationship('Contribution', backref='made_on', lazy=True)

    def __repr__(self):
        # This is what is shown when object is printed
        return "Campaign( {}, {}, {}, {}, {}, {}, {}, {}, {})".format(
               self.campaign_name,
               self.campaign_image,
               self.campaign_manager,
               self.categories,
               self.depicts_metadata,
               self.captions_metadata,
               self.creation_date,
               self.start_date,
               self.end_date,
               self.start_date,
               self.end_date)
