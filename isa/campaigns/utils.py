import json
import sys
import csv
import pycountry

from datetime import datetime

from isa.models import Contribution


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
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    if end_date:
        if (end_date.strftime('%Y-%m-%d %H:%M') < datetime.now().strftime('%Y-%m-%d %H:%M')):
            status = bool('True')
    else:
        return False
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
