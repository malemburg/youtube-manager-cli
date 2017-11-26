
import sys
from pprint import pprint

from fuzzywuzzy import fuzz
from youtubeservice import YouTubeService


def get_channels(service, channel_name):
    results = service.search().list(
        part='id, snippet', #,contentDetails,statistics',
        type='channel',
        q=channel_name,
    ).execute()
    items = results['items']
    pprint(items)




def test():
    print('\n\n=== OUTPUT START ===\n')
    ys = YouTubeService()
    service = ys.service
    channels = get_channels(service, channel_name='PyDDF')
    pprint(channels)
    print('\n\n=== FINISH ===\n')


def x_test(channel_name='EuroPython Conference'):
    print('\n\n=== OUTPUT START ===\n')
    ys = YouTubeService()
    service = ys.service
    results = service.search().list(
        part='id, snippet', #,contentDetails,statistics',
        type='channel',
        q=channel_name,
    ).execute()
    #pprint(results)
    data = results['items']
    for entry in range(len(results['items'])):
        data = results['items'][entry]
        snippet = data['snippet']
        channelId = data['id']['channelId']
        title = snippet['title']

        print('title: {}, channelId: {}'.format(title, channelId))

        videos = service.search().list(
            part='id, snippet', #,contentDetails,statistics',
            type='video',
            q=channelId,
        ).execute()
        pprint(videos)


#
#         pprint(results['items'][entry]['snippet']['title'])
#         pprint(results['items'][entry]['snippet']['channelTitle'])
#     pprint(elements)
#    elements = results['items'][0]['id']
#     pprint(channelID)


    print('\n\n=== FINISH ===\n')


if __name__ == '__main__':
    test()  #sys.argv[1])
