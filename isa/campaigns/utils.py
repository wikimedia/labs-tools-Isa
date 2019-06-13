import json
import csv
import pycountry

from datetime import datetime


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
