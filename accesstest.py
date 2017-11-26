
from pprint import pprint
from youtubeservice import YouTubeService


def test():
    print('\n\n=== OUTPUT START ===\n')
    ys = YouTubeService()
    service = ys.service
    results = service.search().list(
        part='id, snippet', #,contentDetails,statistics',
        type='channel',
        q='EuroPython Conference',
    ).execute()
    pprint(results)
    data = results['items']
    for entry in range(len(results['items'])):
        data = results['items'][entry]
        snippet = data['snippet']
        pprint(data['id'])
        pprint(snippet['title'])
#
#         pprint(results['items'][entry]['snippet']['title'])
#         pprint(results['items'][entry]['snippet']['channelTitle'])
#     pprint(elements)
#    elements = results['items'][0]['id']
#     pprint(channelID)
    print('\n\n=== FINISH ===\n')

if __name__ == '__main__':
    test()
