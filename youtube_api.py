""" YouTube API Tools

"""
import os
import pickle
import pprint

# Google APIs
from googleapiclient import discovery
#from googleapiclient.errors import HttpError
from google_auth_oauthlib import flow 
from oauth2client import file

# Fuzzy matching
from fuzzywuzzy import fuzz

### Globals

# OAuth2 secrets file
#
# Needs to be kept private. See
# https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
# for details
CLIENT_SECRETS_FILE = 'private/client_secret.json'

# Oauth2 credentials files
#
# This needs to be kept private. It stores the temporary tokens generated
# during the OAuth2 authorization process.
OAUTH_CREDENTIALS_FILE = 'private/client-oauth.pickle'

# Force use of HTTPS for YouTube access, so we can use all available APIs
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

# API service details
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

### Helpers

class Namespace:

    """ Namespace container

    """
    @classmethod
    def from_dict(class_, d):
        o = class_()
        o.__dict__.update(d)
        for k, v in d.iteritems():
            if isinstance(v, dict):
                o[k] = Namespace.from_dict(v)
        return o

    def __str__(self):
        return pprint.pformat(self.__dict__)

    def __repr__(self):
        return '%s(keys=%s)' % (
            self.__class__.__name__,
            ','.join(self.__dict__.keys()),
            )


def read_credentials(filename=OAUTH_CREDENTIALS_FILE):

    """ Read a credentials file and return the object.

        The file needs to store the object as pickle.
    
    """
    try:
         with open(filename, 'rb') as cfile:
             credentials = pickle.load(cfile)
         os.chmod(filename, 0600)
    except (IOError, EOFError):
         credentials = None
    return credentials

def write_credentials(credentials, filename=OAUTH_CREDENTIALS_FILE):

    """ Write the credentials object to a file.
    
        The function uses pickle to store the object.
        
    """
    with open(filename, 'wb') as cfile:
        pickle.dump(credentials, cfile)
    os.chmod(filename, 0600)

def refresh_token(credentials):

    """ Refresh the token in the credentials.

        This extends the lifetime of the token and is useful when
        using the command line interface for an extended amount of
        time.

    """
    import google.auth.transport.requests
    request = google.auth.transport.requests.Request()
    try:
        credentials.refresh(request)
    except Exception as error:
        print ('Refresh generated an error: %r' % error)
        credentials = None
    else:
        write_credentials(credentials)
        print ('Token will expire at %s' % credentials.expiry)
    return credentials

def youtube_service():

    """ Create an authenticated YouTube service object

        The API will automatically ask for authentication in case the
        existing credential and OAuth2 files do not allow access.
    
    """
    # Initiate the installed flow for OAuth2
    oauth_flow = flow.InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        SCOPES)

    # Try to read credentials from file, otherwise ask user for
    # to grant access
    credentials = read_credentials()
    if credentials is not None:
        credentials = refresh_token(credentials)
    if (credentials is None or 
        not credentials.valid or
        credentials.expired):
        # Ask the user to authenticate using a browser
        credentials = oauth_flow.run_console()
        write_credentials(credentials)
        #print ('Credentials: %r' % credentials.__dict__)
        print ('Token will expire at %s' % credentials.expiry)

    # Build service object
    return discovery.build(API_SERVICE_NAME,
                           API_VERSION,
                           credentials=credentials)

def channels_list_by_username(service, **kwargs):

    results = service.channels().list(
         part='snippet,contentDetails,statistics',
         forUsername='GoogleDevelopers',
    ).execute()
    #print ('Results: %r' % results)
    print('This channel\'s ID is %s. Its title is %s, and it has %s views.' %
        (results['items'][0]['id'],
         results['items'][0]['snippet']['title'],
         results['items'][0]['statistics']['viewCount']))

def find_channel_id(service, channel_name, min_ratio=75):

    results = service.search().list(
        q=channel_name,
        part='snippet',
        type='channel',
        maxResults=5).execute()
    #pprint.pprint(results)
    items = results['items']
    if not items:
        raise KeyError('No channel found')
    first_item = items[0]
    details = first_item['snippet']
    channel_title = details['channelTitle']
    ratio = fuzz.partial_ratio(channel_title, channel_name)
    if ratio < min_ratio:
        raise KeyError('Channel found, but does not match (ratio=%s): %r' %
                       (ratio, channel_title))
    return details['channelId']

YT_SEARCH_MAX_RESULTS_LIMIT = 50

def get_channel_video_ids(service, channel_id, query=None, max_results=100):

    # Fetch results in pages
    all_items = []
    next_page = None
    while len(all_items) < max_results:
        get_results = min(max_results - len(all_items),
                          YT_SEARCH_MAX_RESULTS_LIMIT)
        results = service.search().list(
            q=query,
            channelId=channel_id,
            part='id',
            type='video',
            maxResults=get_results,
            pageToken=next_page).execute()
        #pprint.pprint(results)
        all_items.extend(results['items'])
        next_page = results.get('nextPageToken')
        if next_page is None:
            break

    # Extract IDs
    return [entry['id']['videoId'] for entry in all_items]

ALL_VIDEO_PARTS = (
    'contentDetails',
    'fileDetails',
    'id',
    'liveStreamingDetails',
    'localizations',
    'player',
    'processingDetails',
    'recordingDetails',
    'snippet',
    'statistics',
    'status',
    'suggestions',
    'topicDetails'
    )

DEFAULT_VIDEO_PARTS = 'snippet,statistics,status,contentDetails'

def get_video_details(service, video_id):

    results = service.videos().list(
        id=video_id,
        part=DEFAULT_VIDEO_PARTS,
        ).execute()
    #pprint.pprint(results)
    items = results['items']
    if not items:
        raise KeyError('Video with ID %r not found' % video_id)
    return items[0]

def get_video_details_namespace(service, video_id):
    details = get_video_details(service, video_id)
    return Namespace.from_dict(details)

def update_video_details(service, video_details):

    assert video_details['id']
    # Note: YT complains when passing in a body structure with parts
    # which are not listed in part.
    results = service.videos().update(
        part=DEFAULT_VIDEO_PARTS,
        body=video_details,
        ).execute()
    pprint.pprint(results)
    return results

def update_video_description(service, video_details):

    description = video_details['snippet']['description']
    description += '\n\nTest'
    video_details['snippet']['description'] = description

###

if __name__ == '__main__':
    pp = pprint.pprint
    service = youtube_service()
    if 0:
        channel_name = raw_input('Channel name: ')
        channel_id = find_channel_id(service, channel_name)
    elif 1:
        channel_name = 'malemburg'
        channel_id = 'UChBNxhX_IaRXKSp2GHsNhHw'
    else:
        channel_name = 'EuroPython Conference'
        channel_id = 'UC98CzaYuFNAA_gOINFB0e4Q'
    print ('Channel ID: %s' % channel_id)
    video_ids = get_channel_video_ids(service, channel_id,
                                      max_results=10)
    print ('Video IDs (%i videos): %r' % (len(video_ids), video_ids))

    print ('Example video:')
    video_details = get_video_details(service, 'PwbfHcnkmNs')
    pp(video_details)
    
    update_video_description(service, video_details)
    video_details['status']['privacyStatus'] = 'public'
    video_details['snippet']['tags'] += ['pyddf-test']
    print('With new description:')
    pp(video_details)

    update_video_details(service, video_details)

