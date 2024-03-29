"""Migrate database to use id instead of username for reference

Applies a migration script generated by Flask-Migrate. Adds the user
ids to all campaigns and contributions.

"""

from isa import db
from isa.models import Campaign
from isa.models import Contribution
from isa.models import User


def execute_db(statement):
    print("\033[1;34mmysql> {}\033[00m".format(statement))
    return connection.execute(statement)


connection = db.session.connection()

# Add user id to campaign and contribution tables and make username
# nullable.
execute_db("ALTER TABLE campaign ADD COLUMN manager_id INTEGER NOT NULL")
database_name = db.session.bind.url.database
# Get the type for the column and use it in the alter statement to not
# change it.
campaign_expression = (
    "SELECT column_type FROM information_schema.columns WHERE "
    "table_name = 'campaign' AND column_name = 'campaign_manager' AND "
    "table_schema = '{}'"
).format(database_name)
campaign_type = execute_db(campaign_expression).first()[0]
execute_db("ALTER TABLE campaign MODIFY campaign_manager {} NULL".format(campaign_type))
execute_db("ALTER TABLE contribution ADD COLUMN user_id INTEGER NOT NULL")
contributon_expression = (
    "SELECT column_type FROM information_schema.columns where "
    "table_name = 'contribution' AND column_name = 'username' AND "
    "table_schema = '{}'"
).format(database_name)
contribution_type = execute_db(contributon_expression).first()[0]
execute_db("ALTER TABLE contribution MODIFY username {} NULL".format(contribution_type))

# Remove unused column for campaign id in the country table.
execute_db("ALTER TABLE country DROP FOREIGN KEY country_ibfk_1")
execute_db("ALTER TABLE country DROP COLUMN campaign_id")

# Add users referenced by campaigns or contribution that don't exist
# in the user table.
usernames = {u.username for u in User.query.all()}
campaigns = {c.campaign_manager for c in Campaign.query.all()}
contributions = {c.username for c in Contribution.query.all()}
# All usernames that are managers of campaigns or have made contributions.
missing_users = (campaigns | contributions) - usernames

# Progress bar max width.
w = 70
# Elements of process per progress bar increase.
m = len(missing_users) / w
# Current progress bar width.
p = m
# Number of elements processed.
i = 0

print("Adding missing users.")
for username in missing_users:
    if not User.query.filter_by(username=username).count():
        user = User(username=username, caption_languages='en,fr,,,,')
        db.session.add(user)

    # Print progress
    i += 1
    if i >= p:
        print(".", end="", flush=True)
        p += m
print()

print("Added {} users.".format(i))

users = User.query.all()
p = len(users) / w
i = 0
# Replace references to username with user id.
print("Add user ids to campaigns and contributions.")
for user in users:
    for contribution in Contribution.query.filter_by(username=user.username):
        # print(contribution, user)
        contribution.user_id = user.id
        # contribution.user = user
    for campaign in Campaign.query.filter_by(campaign_manager=user.username):
        campaign.manager_id = user.id

    # Print progress
    i += 1
    if i >= p:
        print(".", end="", flush=True)
        p += len(users) / w
print()

# Add foreign keys.
execute_db("ALTER TABLE campaign ADD FOREIGN KEY(manager_id) REFERENCES user (id)")
execute_db("ALTER TABLE contribution ADD FOREIGN KEY(user_id) REFERENCES user (id)")

db.session.commit()
