#
# Implementation of the Wordpress API for adding / updating / deleting
# events as custom post types. 
#

import requests, warnings
import jinja2.filters

from zoneinfo import ZoneInfo
from flask_pluginengine import current_plugin
from requests.auth import HTTPBasicAuth

from indico.modules.events.models.events import EventType

def make_request(method, endpoint, data = {}):
    wp_url = current_plugin.settings.get('wp_url')
    wp_username = current_plugin.settings.get('wp_username')
    wp_password = current_plugin.settings.get('wp_application_password')

    if wp_url[-1] == '/':
        wp_url = wp_url[:-1]
    if endpoint[0] != '/':
        endpoint = '/' + endpoint

    auth = HTTPBasicAuth(wp_username, wp_password)

    if method == 'post':
        response = requests.post(wp_url + endpoint,
            data = data, auth = auth)
    elif method == 'get':
        response = requests.get(wp_url + endpoint,  auth = auth)
    elif method == 'delete':
        response = requests.delete(wp_url + endpoint,  auth = auth)
    else:
        raise RuntimeError('Method not supported: ' % method)
    
    if response.status_code >= 300:
        warnings.warn(response.text)
        raise RuntimeError('Invalid response from the Wordpress API')

    return response

def delete_event(event_id):
    wp_event = get_event(event_id)
    if wp_event is not None:
        make_request('delete', '/wp-json/wp/v2/unipievents/%d' % wp_event['id'])

def get_event(event_id):
    """Retrieve an event data from Wordpress, if available."""
    response = make_request('get', 'wp-json/wp/v2/unipievents/?externalid=%d' % event_id)
    data = response.json()

    if len(data) > 0:
        return data[0]
    else:
        return None

def get_categories(event):
    """Construct the vector of taxonomies to use in Wordpress"""
    taxonomies = []
    maps = current_plugin.settings.get('wp_category_maps')
    for pair in maps.split(','):
        key, value = map(int, pair.split(":"))
        if key == event.category_id:
            taxonomies.append(value)
    return taxonomies

def get_speakers(event):
    speakers = []
    for sp in event.person_links:
        speaker_description = ""
        speaker_description = speaker_description + sp.full_name
        if sp.affiliation:
            speaker_description = speaker_description + " (%s)" % sp.affiliation
        speakers.append(speaker_description)

    return speakers

def get_venue(event):
    venue = event.venue_name
    if event.venue_name != "" and event.room_name != "":
        venue = venue + ", "
    venue = venue + event.room_name

    return venue


def update_event(event):
    wp_event = get_event(event.id)

    post_title = event.title
    venue = get_venue(event)

    event_description = str(event.description)
    if event_description == "":
        event_description = "<p>TBA</p>"

    description = ""
    excerpt = ""
    if event.type == 'lecture':
        speakers = get_speakers(event)
        if len(speakers) > 0:
            speaker_names = ",".join(speakers)
            post_title = post_title + " - %s" % speaker_names
        if venue != "":
            if venue[-1] != ".":
                venue = venue + "."
            description = description + "<h4>Venue</h4><p>" + venue + "</p>"
        excerpt = excerpt + event_description
        description = description + "<h4 class='mt-4'>Abstract</h4>" + event_description

    description += "<p class='mt-4'>Further information is available on the <a href=\"%s\">event page</a> on the Indico platform.</p>"  % event.external_url

    taxonomies = get_categories(event)

    if wp_event:
        # In this case we merge the arrays to make sure 
        # we do not overwrite categories that are set in
        # the wordpress event
        taxonomies = set(taxonomies + wp_event['unipievents_taxonomy'])

    zone = ZoneInfo(current_plugin.settings.get('wp_timezone'))

    # Indico stores times as UTC, whereas the Unipi events plugin expects
    # them in a local time zone. 
    start_timestamp = (event.start_dt + zone.utcoffset(event.start_dt)).timestamp()
    end_timestamp = (event.end_dt + zone.utcoffset(event.start_dt)).timestamp()

    # We make sure that the excerpt is pure text, and truncate it to $250$ characters. 
    excerpt = jinja2.filters.do_striptags(excerpt)
    excerpt = jinja2.filters.do_truncate({}, excerpt, length = 250, end = '', leeway = 10)

    event_data = {
        'status': 'publish',
        'title': post_title,
        'content': description,
        'excerpt': excerpt,
        'unipievents_taxonomy': ",".join(map(str, taxonomies)),
        'unipievents_startdate': int(start_timestamp),
        'unipievents_enddate': int(end_timestamp),
        'unipievents_place': venue,
        'unipievents_externalid': event.id
    }

    endpoint = '/wp-json/wp/v2/unipievents'

    if wp_event is not None:
        endpoint = endpoint + '/%d' % wp_event['id']

    make_request('post', endpoint, event_data)
