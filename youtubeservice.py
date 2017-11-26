from __future__ import print_function

import os
import pickle
import stat

import google.auth.transport.requests

from googleapiclient import discovery
from google_auth_oauthlib import flow

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = os.path.join('private', 'client_secret.json')
CLIENT_CREDENTIALS_FILE = os.path.join('private', 'client_credentials.pcl')

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'


class YouTubeService(object):

    def __init__(self, credentials_filename='', verbose=False):
        self.credentials_filename = (
            credentials_filename or CLIENT_CREDENTIALS_FILE)
        self.flow = flow.InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES)
        self.verbose = verbose

    @property
    def service(self):
        return discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=self.credentials)

    @property
    def credentials(self):
        credentials = self.read_credentials()
        if credentials is not None:
            credentials = self.refresh_token(credentials)
        if (credentials is None or
            not credentials.valid or
            credentials.expired):
            # Ask the user to authenticate using a browser
            credentials = self.flow.run_console()
            self.write_credentials(credentials)
            if self.verbose:
                print('Token will expire at %s' % credentials.expiry)
        return credentials

    def refresh_token(self, credentials):
        request = google.auth.transport.requests.Request()
        try:
            credentials.refresh(request)
        except Exception as error:
            if self.verbose:
                print('Refresh generated an error: %r' % error)
            credentials = None
        else:
            self.write_credentials(credentials)
            if self.verbose:
                print('Token will expire at %s' % credentials.expiry)
        return credentials

    def write_credentials(self, credentials):
        with open(self.credentials_filename, 'wb') as fobj:
            pickle.dump(credentials, fobj)
        os.chmod(self.credentials_filename, stat.S_IRUSR | stat.S_IWUSR)

    @staticmethod
    def read_credentials():
        try:
            with open(CLIENT_CREDENTIALS_FILE, 'rb') as fobj:
                credentials = pickle.load(fobj)
        except (IOError, EOFError):
            credentials = None
        return credentials


def channels_list_by_username(service, **kwargs):
    results = service.channels().list(**kwargs).execute()

    print('This channel\'s ID is %s. Its title is %s, and it has %s views.' %
       (results['items'][0]['id'],
        results['items'][0]['snippet']['title'],
        results['items'][0]['statistics']['viewCount']))


def test_access():
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    yts = YouTubeService()
    service = yts.service
    channels_list_by_username(service,
        part='snippet,contentDetails,statistics',
        forUsername='GoogleDevelopers')


if __name__ == '__main__':
    test_access()
