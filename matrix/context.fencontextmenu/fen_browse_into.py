import xbmc
import sys
import urllib
from urlparse import parse_qsl

def build_url(query):
    return 'plugin://plugin.video.fen/?' + urllib.urlencode(query)

listitem = sys.listitem
path = listitem.getPath()
widget_status = listitem.getProperty("fen_widget")

params = dict(parse_qsl(path.replace('plugin://plugin.video.fen/?','')))

if __name__ == '__main__':
    browse_into = {'mode': 'build_season_list', 'meta': params['meta']}
    xbmc.executebuiltin("ActivateWindow(Videos,%s)" % build_url(browse_into))