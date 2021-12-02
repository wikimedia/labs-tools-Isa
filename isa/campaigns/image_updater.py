import time
import json
import logging
from threading import Thread
import re

import requests
from requests.exceptions import Timeout

from isa import db
from isa.main.utils import commit_changes_to_db
from isa.models import Campaign
from isa.models import Image
from isa.models import Country
from isa.campaigns.utils import API_URL

# Statuses used when processing. Set as Campaign.campaign_images.
PROCESSING = -1
FAILED = -2

# Add files with these extensions as images.
ALLOWED_FILE_EXTENISONS = ["jpg", "jpeg", "png", "svg", "gif"]
# Wait this long (in seconds) before timing out API request.
API_TIMEOUT = 5
# Retry sending API request at most this many times before giving up.
MAX_RETRIES = 5
# Wait this long (in seconds) before retrying to send an API request.
RETRY_DELAY = 1


class UpdateImageException(Exception):
    pass


def update_images(campaign_id):
    """
    Update campaign images in a separate thread

    Keyword arguments:
    campaign_id -- Id of the campaign to update.
    """
    thread = Thread(target=_update, args=(campaign_id,))
    thread.start()


def _update(campaign_id):
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
        campaign.campaign_images = FAILED
        commit_changes_to_db()


class ImageUpdater:
    def __init__(self, campaign_id):
        """
        Keyword arguments:
        campaign_id -- Id of the campaign to update.
        """
        self._campaign_id = campaign_id
        self._images = {}
        self._wiki_loves_categories = []
        self._processed_categories = set()

    def update_images(self):
        """
        Update images and countries for a campaign

        Exceptions:
        UpdateImageException -- When committing to the database fails.
        """
        logging.info("Updating images for campaign {}.".format(self._campaign_id))
        start_time = time.time()
        campaign = Campaign.query.filter_by(id=self._campaign_id).first()
        if campaign.campaign_images == PROCESSING:
            logging.info("Image update for Campaign {} already in progress.".format(
                self._campaign_id
            ))
            return

        campaign.campaign_images = PROCESSING
        if commit_changes_to_db():
            raise UpdateImageException("Committing to database failed.")

        # Clear images for the campaign to ensure that images that have
        # been removed from categories do not remain.
        deleted = Image.query.filter_by(campaign_id=self._campaign_id).delete()
        campaign.images.clear()
        number_of_images = 0
        if campaign.campaign_type:
            # If this is a Wiki Loves campaign get the subcategories that contain the images for the contest.
            self._fetch_wiki_loves_categories(campaign)
            categories = self._wiki_loves_categories
        else:
            categories = json.loads(campaign.categories)

        # Fetch all page ids.
        for category in categories:
            depth = int(category["depth"])
            self._fetch_page_ids(category["name"], depth)

        # Fetch info for pages and add them to the database.
        for page_id, country in self._images.items():
            number_of_images += 1
            image = Image(page_id=page_id, campaign_id=self._campaign_id)
            if country:
                country_id = Country.query.filter_by(name=country)[0].id
                image.country_id = country_id
            db.session.add(image)
            logging.debug("Adding image with page id {} to campaign {}.".format(
                page_id,
                self._campaign_id
            ))
        campaign.campaign_images = number_of_images
        if commit_changes_to_db():
            campaign.campaign_images = FAILED
            raise UpdateImageException("Committing to database failed.")

        logging.info("Deleted {} images from campaign {}.".format(
            deleted,
            self._campaign_id
        ))
        logging.info("{} images committed for campaign {} in {} seconds.".format(
            number_of_images,
            self._campaign_id,
            int(time.time() - start_time)
        ))

    def _fetch_wiki_loves_categories(self, campaign):
        """
        Fetch the subcategories for a wiki loves categories that contain images
        """
        Country.query.filter_by(campaign_id=self._campaign_id).delete()
        campaign.countries.clear()
        for category in json.loads(campaign.categories):
            self._fetch_page_ids(category["name"], 0, True)

    def _fetch_page_ids(self, category, depth, wiki_loves_categories=False, continue_string=None):
        """
        Fetch the page ids for a category and its subcategories

        Filters out pages that do not match file extensions for images.

        Keyword arguments:
        category -- Id of the campaign to fetch images for. Accepts both
          with and without "Category:" prefix.
        depth -- The number of subcategories down to go. 0 means no
          subcategories.
        wiki_loves_categories -- Only get subcategories for Wiki Loves images. Defaults to False.
        continue_string -- Used for API requests. Defaults to None.
        """
        if not category.startswith("Category:"):
            category = "Category:" + category
        if category in self._processed_categories and not continue_string:
            # Skip the category if it has already been processed, except
            # if we are continuing on the same category.
            logging.debug("Skipping already processed category {}.".format(category))
            return

        logging.debug("Fetching page ids for category {}.".format(category))
        self._processed_categories.add(category)
        cmtype = "subcat"
        if not wiki_loves_categories:
            cmtype += "|file"
        parameters = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmlimit": "max",
            "cmprop": "title|type|ids",
            "cmtype": cmtype
        }
        if continue_string:
            parameters["cmcontinue"] = continue_string
        response = self._api_get(parameters)

        for member in response["query"]["categorymembers"]:
            if member["type"] == "file" and self._is_allowed(member["title"]):
                country_name = self._get_country(category)
                self._images[member["pageid"]] = country_name
            elif depth and member["type"] == "subcat":
                self._fetch_page_ids(member["title"], depth - 1)
            elif wiki_loves_categories and member["type"] == "subcat":
                wiki_loves_category = member["title"]
                country_name = self._get_country(wiki_loves_category)
                if country_name:
                    self._wiki_loves_categories.append({"name": wiki_loves_category, "depth": 0})
                    if Country.query.filter_by(name=country_name, campaign_id=self._campaign_id).count() == 0:
                        country = Country(name=country_name, campaign_id=self._campaign_id)
                        db.session.add(country)
        if "continue" in response:
            new_continue_string = response["continue"]["cmcontinue"]
            self._fetch_page_ids(category, depth, wiki_loves_categories, new_continue_string)

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
