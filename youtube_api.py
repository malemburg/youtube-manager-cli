""" YouTube API Tools

"""
import os
import pickle
from googleapiclient import discovery
#from googleapiclient.errors import HttpError
from google_auth_oauthlib import flow 
from oauth2client import file
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

###

if __name__ == '__main__':
    service = youtube_service()
    channel_name = raw_input('Channel name: ')
    print ('Channel ID: %s' % find_channel_id(service, channel_name))
