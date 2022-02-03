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
        help="Update campaigns even if it has images or is processing."
    )
    parser.add_argument(
        "--campaign-id",
        "-i",
        type=int,
        help="Update only the campaign with this id.",
        metavar="ID"
    )
    parser.add_argument(
        "--exclude-campaigns",
        "-e",
        type=int,
        nargs="*",
        help="Ignore campaigns with these ids.",
        metavar="ID"
    )
    args = parser.parse_args()

    if args.campaign_id:
        campaigns = [Campaign.query.get(args.campaign_id)]
    else:
        campaigns = Campaign.query.all()

    for campaign in campaigns:
        if campaign.id in args.exclude_campaigns:
            continue

        if args.force or not campaign.images:
            # Make sure the image count is not stuck on processing.
            campaign.campaign_images = image_updater.FAILED
            commit_changes_to_db()
            ImageUpdater(campaign.id).update_images()
