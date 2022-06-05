import xbmc
import sys
import urllib
import json
from urlparse import parse_qsl

def build_url(query):
    return 'plugin://plugin.video.fen/?' + urllib.urlencode(query)

listitem = sys.listitem
path = listitem.getPath()
widget_status = listitem.getProperty("fen_widget")

params = dict(parse_qsl(path.replace('plugin://plugin.video.fen/?','')))

if __name__ == '__main__':
    meta = json.loads(params['meta'])
    if params['vid_type'] == 'movie':
        watched_params = {"mode": "mark_movie_as_watched_unwatched", "action": 'mark_as_watched',
        "media_id": meta['tmdb_id'], "title": meta['title'], "year": meta['year']}
    else:
        watched_params = {"mode": "mark_episode_as_watched_unwatched", "action": 'mark_as_watched',
        "season": meta['season'], "episode": meta['episode'], "media_id": meta['tmdb_id'],
        "imdb_id": meta['imdb_id'], "title": meta['title'], "year": meta['year']}
    xbmc.executebuiltin("RunPlugin(%s)" % build_url(watched_params))
    xbmc.executebuiltin('UpdateLibrary(video,special://skin/foo)')
