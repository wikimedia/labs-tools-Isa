import time
import json
import logging
from threading import Thread
import re

from celery import shared_task
import requests
from requests.exceptions import Timeout

from isa import db
from isa.main.utils import commit_changes_to_db
from isa.models import Campaign
from isa.models import Image
from isa.models import Country
from isa.campaigns.utils import API_URL

# Statuses used when processing. Set as Campaign.campaign_images.
DONE = 0
PROCESSING = 1
FAILED = 2

# Add files with these extensions as images.
ALLOWED_FILE_EXTENISONS = ["jpg", "jpeg", "png", "svg", "gif", "tif", "tiff"]
# Wait this long (in seconds) before timing out API request.
API_TIMEOUT = 5
# Retry sending API request at most this many times before giving up.
MAX_RETRIES = 5
# Wait this long (in seconds) before retrying to send an API request.
RETRY_DELAY = 1
# Commit this many images at a time to database.
IMAGES_PER_COMMIT = 1000


class UpdateImageException(Exception):
    pass


def update_in_task(campaign_id):
    """
    Update campaign images in a task

    Keyword arguments:
    campaign_id -- Id of the campaign to update.
    """
    update_task.delay(campaign_id)


@shared_task
def update_task(campaign_id):
    """
    Celery task for updating campaign images

    Keyword arguments:
    campaign_id -- Id of the campaign to update.
    """
    update(campaign_id)


def update(campaign_id):
    """
    Updated images for a campaign

    Keyword arguments:
    campaign_id -- Id of the campaign to update.
    """
    try:
        updater = ImageUpdater(campaign_id)
        updater.update_images()
    except Exception:
        logging.exception("Failed to update images for campaign {}.".format(
            campaign_id
        ))
        campaign = Campaign.query.filter_by(id=campaign_id).first()
        campaign.update_status = FAILED
        commit_changes_to_db()


class ImageUpdater:
    def __init__(self, campaign_id):
        """
        Keyword arguments:
        campaign_id -- Id of the campaign to update.
        """
        self._campaign = Campaign.query.get(campaign_id)
        self._images = {}
        self._processed_categories = set()
        self._image_commits = 0
        self._uncommited_images = 0

    def update_images(self):
        """
        Update images and countries for a campaign

        Exceptions:
        UpdateImageException -- When committing to the database fails.
        """
        logging.info("Updating images for campaign {}.".format(self._campaign.id))
        start_time = time.time()
        self._campaign.update_status = PROCESSING
        if not commit_changes_to_db():
            raise UpdateImageException("Committing to database failed.")

        # Clear images for the campaign to ensure that images that have
        # been removed from categories do not remain.
        Image.query.filter_by(campaign_id=self._campaign.id).delete()
        self._campaign.images.clear()
        self._campaign.campaign_images = 0
        if not commit_changes_to_db():
            raise UpdateImageException("Committing to database failed.")

        categories = json.loads(self._campaign.categories)
        for category in categories:
            if self._campaign.campaign_type:
                depth = 1
            else:
                depth = int(category["depth"])
            self._fetch_images(category["name"], depth)

        self._commit_images()
        logging.info(
            "{} images committed for campaign {} in {} seconds "
            "and {} commits."
            .format(
                self._campaign.campaign_images,
                self._campaign.id,
                int(time.time() - start_time),
                self._image_commits
            )
        )
        self._campaign.update_status = DONE
        if not commit_changes_to_db():
            raise UpdateImageException("Committing to database failed.")

    def _fetch_images(self, category, depth, continue_string=None):
        """
        Add images for a category to the campaign

        Fetches all images in the given category and if, `depth` is
        more than 0, its subcategories. Filters out pages that do not
        match file extensions for images.

        Keyword arguments:
        category -- Id of the campaign to fetch images for. Accepts both
          with and without "Category:" prefix.
        depth -- The number of subcategories down to go. 0 means no
          subcategories.
        continue_string -- Used for API requests. Defaults to None.
        """
        if not category.startswith("Category:"):
            category = "Category:" + category
        if category in self._processed_categories and not continue_string:
            # Skip the category if it has already been processed, except
            # if we are continuing on the same category.
            logging.debug('Skipping already processed category "{}".'.format(category))
            return

        if not continue_string:
            logging.debug('Fetching page ids for category "{}".'.format(category))
        self._processed_categories.add(category)
        parameters = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmlimit": "max",
            "cmprop": "title|type|ids",
            "cmtype": "subcat|file"
        }
        if continue_string:
            parameters["cmcontinue"] = continue_string
        response = self._api_get(parameters)

        for member in response["query"]["categorymembers"]:
            if member["type"] == "file" and self._is_allowed(member["title"]):
                image = Image(
                    page_id=member["pageid"],
                    campaign_id=self._campaign.id
                )
                if self._campaign.campaign_type:
                    country_name = self._get_country(category)
                    if not country_name:
                        # Skip categories without countries.
                        continue

                    if Country.query.filter_by(name=country_name).count() == 0:
                        # Make sure that the country is in the
                        # database.
                        country = Country(name=country_name)
                        logging.debug('Adding new country "{}".'.format(country_name))
                        db.session.add(country)
                    country_id = Country.query.filter_by(name=country_name)[0].id
                    image.country_id = country_id

                db.session.add(image)
                self._uncommited_images += 1
                if self._uncommited_images % IMAGES_PER_COMMIT == 0:
                    self._commit_images()
                    self._uncommited_images = 0
                    logging.debug("A total of {} images have been committed so far.".format(self._campaign.campaign_images))
            elif depth and member["type"] == "subcat":
                self._fetch_images(member["title"], depth - 1)
        if "continue" in response:
            new_continue_string = response["continue"]["cmcontinue"]
            self._fetch_images(category, depth, new_continue_string)

    def _commit_images(self):
        """
        Commit images to database
        """
        self._campaign.campaign_images = len(self._campaign.images)
        if not commit_changes_to_db():
            raise UpdateImageException("Committing to database failed.")

        self._image_commits += 1

    def _get_country(self, category):
        """
        Get country from a Wiki Loves images category

        Returns:
        The country if there is a match, else None.
        """
        re_country = r"Category:Images from Wiki Loves ([\w\s]+) (\d{4}) in (.+)"
        match = re.match(re_country, category)
        if match:
            return match.group(3)

    def _is_allowed(self, filename):
        """
        Check if a filename has an extension that is allowed

        Returns:
        True if the extension is allowed, else False.
        """
        extension = filename.lower().split(".")[-1]
        return extension in ALLOWED_FILE_EXTENISONS

    def _api_get(self, parameters, retries=0):
        """Make a GET request to the Commons API

        If the request times out or if an exception is raised in another
        way, the same request will be sent again, up to a certain amount
        of retries.

        Keyword arguments:
        parameters -- API parameters. General parameters are set for all
          requests.
        retries -- How many retries there have been, including this
          one. Defaults to 0.

        Returns:
        API response.

        Exceptions:
        UpdateImageException -- When all request retries fail.
        """
        base_parameters = {
            "format": "json",
            "formatversion": 2,
            "origin": "*"
        }
        parameters.update(base_parameters)
        try:
            logging.debug("Sending request, retry number {}.".format(retries))
            response = requests.get(
                API_URL,
                params=parameters,
                timeout=API_TIMEOUT
            ).json()
        except Timeout:
            if retries > MAX_RETRIES:
                raise UpdateImageException(
                    "Maximum retries exceeded for API requests."
                )

            time.sleep(RETRY_DELAY)
            return self._api_get(parameters, retries + 1)
        return response
