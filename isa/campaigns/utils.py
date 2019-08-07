import json
import sys
import csv
import pycountry
import requests
import mwoauth

from datetime import datetime

from mwoauth import ConsumerToken, Handshaker

from flask import request, session
from isa import app
from isa.models import Contribution
from requests_oauthlib import OAuth1


def get_country_from_code(country_code):
    """
    Get country label from country code.

    Keyword arguments:
    country_code -- the code of the country (e.g 'FR' for France)
    """
    country = []
    countries = [(country.alpha_2, country.name) for country in pycountry.countries]
    for country_index in range(len(countries)):
        # index 0 is the country code selected from the form
        if(countries[country_index][0] == country_code):
            country.append(countries[country_index])
    return country[0][1]


def compute_campaign_status(end_date):
    """
    Computes the campaign status (Open or closed).

    Keyword arguments:
    end_date -- the end date of the campaign
    """
    status = bool('False')
    if end_date is not None and end_date.strftime('%Y-%m-%d %H:%M') < datetime.now().strftime('%Y-%m-%d %H:%M'):
        status = bool('True')
    return status


def get_campaign_category_list(categories):
    """
    Extract categoriues for a given campaign

    Keyword arguments:
    campaign_id -- The id of the campaign
    """
    categories_list = []
    # We convert the json string to json
    categories = json.loads(categories)
    if categories is None:
        return []
    else:
        for category in categories:
            categories_list.append(category['name'])
        return categories_list


def combine_campign_content(content_list):
    campaign_content = []
    campaign_content.append(content_list)
    return campaign_content


def get_all_campaign_images(query_data):
    campaign_image_list = []
    for data in query_data:
        for category_member in data['query']['categorymembers']:
            campaign_image_list.append(category_member['title'])
    return campaign_image_list


def get_actual_image_file_names(image_list):
    image_names = []
    for image in image_list:
        image_name_without_file = image.split(':')[1]
        # we now replaces spaces with underscore in image name
        image_names.append(image_name_without_file.replace(" ", "_"))
    return image_names


def constructEditContent(formdata):
    """
    Arranges edit content into objects

    Keyword arguments:
    formdata -- Request data with depict q values
    """
    depicts_content = []
    if formdata:
        for depict_data in formdata:
            depicts_content.append(depict_data.split('|'))
        return depicts_content
    else:
        return []


def buildCategoryObject(category):
    cat_object_body = {}
    cat_object_body['name'] = category
    cat_object_body['depth'] = 0
    return cat_object_body


def get_all_camapign_stats_data(campaign_id):
    all_campaign_stats_data = []
    all_campaign_stats = Contribution.query.filter_by(campaign_id=campaign_id).all()
    for campaign_stat in all_campaign_stats:
        campaign_stat_data = {}
        campaign_stat_data['username'] = campaign_stat.username
        campaign_stat_data['file'] = campaign_stat.file
        campaign_stat_data['edit_type'] = campaign_stat.edit_type
        campaign_stat_data['edit_action'] = campaign_stat.edit_action
        campaign_stat_data['country'] = campaign_stat.country
        campaign_stat_data['depict_item'] = campaign_stat.depict_item
        campaign_stat_data['depict_prominent'] = campaign_stat.depict_prominent
        campaign_stat_data['caption_text'] = campaign_stat.caption_text
        campaign_stat_data['caption_language'] = campaign_stat.caption_language
        campaign_stat_data['date'] = campaign_stat.date
        all_campaign_stats_data.append(campaign_stat_data)
    return all_campaign_stats_data


def create_campaign_country_stats_csv(stats_file_directory, campaign_name,
                                      country_fields, country_stats_data):
    file_directory = stats_file_directory + '/' + campaign_name.replace(' ', '_') + '_country_stats.csv'
    # We build the campaign statistucs file here with the country stats stats
    with open(file_directory, 'w') as csv_file:
        writer = csv.writer(csv_file)
        fields = country_fields
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(country_stats_data)
    csv_file.close()
    return campaign_name.replace(' ', '_') + '_country_stats.csv'


def create_campaign_contributor_stats_csv(stats_file_directory, campaign_name,
                                          contributor_fields, contributor_stats_data):
    # We build the campaign statistucs file here with the country stats stats
    file_directory = stats_file_directory + '/' + campaign_name.replace(' ', '_') + '_stats.csv'
    with open(file_directory, 'w') as contrib_csv_file:
        writer = csv.writer(contrib_csv_file)
        fields = contributor_fields
        writer = csv.DictWriter(contrib_csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(contributor_stats_data)
    contrib_csv_file.close()
    return campaign_name.replace(' ', '_') + '_stats.csv'


def create_campaign_all_stats_csv(stats_file_directory, campaign_name, all_stats_fields,
                                  campaign_all_stats_data):
    # We build the campaign statistucs file here with the country stats stats
    file_directory = stats_file_directory + '/' + campaign_name.replace(' ', '_') + '_all_stats.csv'
    with open(file_directory, 'w') as all_stats_csv_file:
        writer = csv.writer(all_stats_csv_file)
        fields = all_stats_fields
        writer = csv.DictWriter(all_stats_csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(campaign_all_stats_data)
    all_stats_csv_file.close()
    return campaign_name.replace(' ', '_') + '_all_stats.csv'


def generate_csrf_token(app_key, app_secret, user_key, user_secret):
    # We authenticate the user using the keys
    auth = OAuth1(app_key, app_secret, user_key, user_secret)

    # Get token
    token_request = requests.get('https://commons.wikimedia.org/w/api.php', params={
        'action': 'query',
        'meta': 'tokens',
        'format': 'json',
    }, auth=auth)
    token_request.raise_for_status()

    # We get the CSRF token from the result to be used in editing
    CSRF_TOKEN = token_request.json()['query']['tokens']['csrftoken']
    return CSRF_TOKEN, auth


def make_edit_api_call(csrf_token, api_auth_token, username, contribution_data):
    """
    Makes an edit API call to make changes to an image.

    Keyword arguments:
    app_key -- The application configuration key
    app_secret -- The application configuration secret
    user_key -- User key generated for user at login
    user_secret -- User secret generated in token at login
    username -- username in session
    params -- APi configuration data from front end
    """
    params = contribution_data['api_options']
    edit_type = contribution_data['edit_type']
    edit_action = contribution_data['edit_action']
    
    # Serialise JSON data in 'claim' for depicts edits
    # but NOT for 'remove' action, as claim is a string in this case
    if edit_type == 'depicts' and edit_action != "remove":
        params['claim'] = json.dumps(params['claim'])
    
    params['format'] = 'json'
    params['token'] = csrf_token
    params['formatversion'] = 1
    params['summary'] = username + '@ISA'

    # This is the actual edit post request
    # We sign that with the authentication
    response = requests.post('https://commons.wikimedia.org/w/api.php', data=params, auth=api_auth_token)
    if response.status_code == 200:
        result = response.json()
        revision_id = None
        if edit_type == 'depicts':
            page_info = result.get('pageinfo')
            if page_info is not None:
                revision_id = page_info.get('lastrevid')
        else:
            entity = result.get('entity')
            if entity is not None:
                revision_id = entity.get('lastrevid')
        return revision_id
