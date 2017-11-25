# Sample Python code for user authorization

import os
import pickle

import google.oauth2.credentials

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"  #token: 4/ckQk81aljuVOy-x3EvPxUjP1bvlXwnUMJSCXiYB8G4s
CLIENT_CREDENTIALS_FILE = 'client_credentials.pcl'

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

def get_authenticated_service():
    try:
        with open(CLIENT_CREDENTIALS_FILE) as fobj:
            credentials = pickle.load(fobj)
    except IOError:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        credentials = flow.run_console()
        with open(CLIENT_CREDENTIALS_FILE, 'w') as fobj:
            pickle.dump(credentials, fobj)
    #import pdb; pdb.set_trace()

    print credentials.expiry
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


def channels_list_by_username(service, **kwargs):
    results = service.channels().list(**kwargs).execute()

    print('This channel\'s ID is %s. Its title is %s, and it has %s views.' %
       (results['items'][0]['id'],
        results['items'][0]['snippet']['title'],
        results['items'][0]['statistics']['viewCount']))



if __name__ == '__main__':
  # When running locally, disable OAuthlib's HTTPs verification. When
  # running in production *do not* leave this option enabled.
  os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
  service = get_authenticated_service()
  channels_list_by_username(service,
      part='snippet,contentDetails,statistics',
      forUsername='GoogleDevelopers')