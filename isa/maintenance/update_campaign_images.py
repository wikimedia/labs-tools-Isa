"""Updates images for campaigns

This updates the campaigns, from loading images in the frontend to
storing them in the database (see
https://phabricator.wikimedia.org/T226303).

"""

import argparse

from isa.models import Campaign
from isa.campaigns import image_updater
from isa.campaigns.image_updater import ImageUpdater
from isa.main.utils import commit_changes_to_db


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Update campaigns even if it is processing."
    )
    parser.add_argument(
        "--campaign-ids",
        "-i",
        type=int,
        nargs="*",
        help="Update only the campaign with these ids.",
        metavar="ID"
    )
    parser.add_argument(
        "--exclude-campaigns",
        "-e",
        type=int,
        nargs="*",
        help="Do not update campaigns with these ids.",
        metavar="ID"
    )
    args = parser.parse_args()

    query = Campaign.query
    if args.campaign_ids:
        query = Campaign.query.filter(Campaign.id.in_(args.campaign_ids))
    if args.exclude_campaigns:
        query = query.filter(Campaign.id.notin_(args.exclude_campaigns))
    if not args.force:
        query = query.filter(Campaign.update_status != image_updater.PROCESSING)
    campaigns = query.all()

    for campaign in campaigns:
        image_updater.update(campaign.id)
