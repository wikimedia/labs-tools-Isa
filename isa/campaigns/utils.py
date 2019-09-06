import json
import sys
import csv
import pycountry
import requests
import mwoauth
import unicodedata

from datetime import datetime
from flask import request, session
from mwoauth import ConsumerToken, Handshaker
from operator import itemgetter
from requests_oauthlib import OAuth1

from isa import app
from isa.models import Contribution, User
from isa.users.utils import (get_all_users_contribution_data_per_campaign, get_user_ranking)


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
    """
    Add campaign campaign content to a list

    Keyword arguments:
    content_list -- The list of the campaign content
    """
    campaign_content = []
    campaign_content.append(content_list)
    return campaign_content


def get_all_camapign_stats_data(campaign_id):
    """
    provides all contributions related to a campaign

    Keyword arguments:
    campaign_id -- The id of the campaign in question
    """
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
    """
    Create CSV file with country statistics for a campaign

    Keyword arguments:
    stats_file_directory -- The directory to save the csv file
    campaign_name -- The campaign name
    country_fields -- Fields to add to the csv header
    country_stats_data -- Country data for csv file
    """
    file_directory = stats_file_directory + '/' + campaign_name.replace(' ', '_') + '_country_stats.csv'
    # We build the campaign statistucs file here with the country stats stats
    with open(file_directory, 'w', encoding='UTF-8') as csv_file:
        writer = csv.writer(csv_file)
        fields = country_fields
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(country_stats_data)
    csv_file.close()
    return campaign_name.replace(' ', '_') + '_country_stats.csv'


def create_campaign_contributor_stats_csv(stats_file_directory, campaign_name,
                                          contributor_fields, contributor_stats_data):
    """
    Create CSV file with contributor statistics for a campaign

    Keyword arguments:
    stats_file_directory -- The directory to save the csv file
    campaign_name -- The campaign name
    country_fields -- Fields to add to the csv header
    country_stats_data -- Contributor data for csv file
    """
    # We build the campaign statistucs file here with the country stats stats
    file_directory = stats_file_directory + '/' + campaign_name.replace(' ', '_') + '_stats.csv'
    with open(file_directory, 'w', encoding='UTF-8') as contrib_csv_file:
        writer = csv.writer(contrib_csv_file)
        fields = contributor_fields
        writer = csv.DictWriter(contrib_csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(contributor_stats_data)
    contrib_csv_file.close()
    return campaign_name.replace(' ', '_') + '_stats.csv'


def create_campaign_all_stats_csv(stats_file_directory, campaign_name, all_stats_fields,
                                  campaign_all_stats_data):
    """
    Create CSV file with contributor statistics for a campaign

    Keyword arguments:
    stats_file_directory -- The directory to save the csv file
    campaign_name -- The campaign name
    country_fields -- Fields to add to the csv header
    country_stats_data -- All campaign stats data for csv file
    """
    # We build the campaign statistucs file here with the country stats stats
    file_directory = stats_file_directory + '/' + campaign_name.replace(' ', '_') + '_all_stats.csv'
    with open(file_directory, 'w', encoding='UTF-8') as all_stats_csv_file:
        writer = csv.writer(all_stats_csv_file)
        fields = all_stats_fields
        writer = csv.DictWriter(all_stats_csv_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(campaign_all_stats_data)
    all_stats_csv_file.close()
    return campaign_name.replace(' ', '_') + '_all_stats.csv'


def generate_csrf_token(app_key, app_secret, user_key, user_secret):
    """
    Generate CSRF token for edit request

    Keyword arguments:
    app_key -- The application api auth key
    app_secret -- The application api auth secret
    user_key -- User auth key generated at login
    user_secret -- User secret generated at login
    """
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
    Make edit API call to make changes to an image on Commons.

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


def get_country_ranking(all_contrystats_data, country):
    """
    Get a particular Country's ranking

    Keyword arguments:
    all_contry_stats_data -- sorted list of all country by their contributions
    country -- the country whic's ranking is to be obtained
    """

    index = next((i for i, item in enumerate(all_contrystats_data) if item['country'] == country), -1)
    return index + 1  # we shift from 0


def get_country_improved_file_count(campaign_contributions, country):
    """
    Count improved files per country in ca campaign

    Keyword arguments:
    campaign_contributions -- Contributions in said campaign
    country -- The country whose images are counted
    """
    country_improved_files = []
    for contribution in campaign_contributions:
        if contribution.country == country:
            country_improved_files.append(contribution.file)
    return len(country_improved_files)


# TODO: Transfer all these methods to the campaign blueprint
def get_campaign_country_data(campaign_id):
    """
    Fetch campaign country data

    Keyword arguments:
    campaign_id -- Campaign country for said campaign
    """
    # Holds contribution countries for campaign with id: campaign_id
    contribution_countries = []

    # Holds all countries and images imaproved per country
    all_country_statistics_data = []

    # We get all the campaign contributions
    campaign_contributions = Contribution.query.filter_by(campaign_id=campaign_id).all()
    # We then iterate to get the countries
    for contribution in campaign_contributions:
        if contribution.country != "":
            contribution_countries.append(contribution.country)
    contribution_countries = set(contribution_countries)

    for country in contribution_countries:
        country_stats_data = {
            'country': country,
            'images_improved': get_country_improved_file_count(campaign_contributions, country)
        }
        all_country_statistics_data.append(country_stats_data)
    all_country_statistics_data = sorted(all_country_statistics_data,
                                         key=itemgetter('images_improved'), reverse=True)

    for country_stats_data in all_country_statistics_data:
        country_stats_data['rank'] = get_country_ranking(all_country_statistics_data, country_stats_data['country'])
    return all_country_statistics_data


def get_table_stats(campaign_id, username):
    """
    Fetch campaign table stats

    Keyword arguments:
    campaign_id -- Campaign id for said campaign
    username -- username of the current user who's stats will be shown
    """
    # participantids for this campaign
    campaign_user_names = []
    # We are querrying all the users who participate in the campaign
    contribs_for_campaign = Contribution.query.filter_by(campaign_id=campaign_id).all()
    for campaign_contribution in contribs_for_campaign:
        campaign_user_names.append(campaign_contribution.username)
    # we get the unique ids so as not to count an id twice
    campaign_user_names_set = set(campaign_user_names)
    # We then re-initialize the ids array
    campaign_user_names = []
    # We now obtain the ranking for all the users in the system and their files improved
    all_camapign_users_list = []
    #  We iterate the individual participants id in a campaign and get the user info
    for user_name in campaign_user_names_set:
        user = User.query.filter_by(username=user_name).first()
        all_camapign_users_list.append(user)
        
    # We get the users and their contribution data
    all_contributors_data = get_all_users_contribution_data_per_campaign(all_camapign_users_list, campaign_id)
    current_user_rank = get_user_ranking(all_contributors_data, username)

    # We add rank to all contributor's data
    for user_data in all_contributors_data:
        user_data['rank'] = get_user_ranking(all_contributors_data, user_data['username'])

    # We get all the campaign coountry sorted data
    all_campaign_country_statistics_data = get_campaign_country_data(campaign_id)
    
    campaign_table_stats = {}
    campaign_table_stats['all_contributors_data'] = all_contributors_data
    campaign_table_stats['all_campaign_country_statistics_data'] = all_campaign_country_statistics_data
    campaign_table_stats['current_user_rank'] = current_user_rank
    campaign_table_stats['campaign_editors'] = len(campaign_user_names_set)
    return campaign_table_stats


def convert_latin_to_english(text):
    """
    Convert campaign names from Latin to English

    Keyword arguments:
    text -- Text to be converted to english
    """
    try:
        text = text.decode('UTF-8')
    except (UnicodeDecodeError, AttributeError):
        pass
    return "".join(char for char in
                   unicodedata.normalize('NFKD', text)
                   if unicodedata.category(char) != 'Mn')
