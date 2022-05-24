import xbmc, xbmcaddon, xbmcplugin, xbmcgui
import sys, os
import urllib
from urlparse import parse_qsl
from resources.lib.modules.easynews_api import EasyNewsAPI
from resources.lib.modules.settings import get_theme
from resources.lib.modules.nav_utils import build_url, setView
from resources.lib.modules.utils import clean_file_name
# from resources.lib.modules.utils import logger

__addon_id__ = 'plugin.video.furkit'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__handle__ = int(sys.argv[1])
addon_dir = xbmc.translatePath(__addon__.getAddonInfo('path'))
dialog = xbmcgui.Dialog()
icon_directory = get_theme()
default_easynews_icon = os.path.join(icon_directory, 'easynews.png')
fanart = os.path.join(addon_dir, 'fanart.jpg')

EasyNews = EasyNewsAPI()

def search_easynews():
    from resources.lib.modules.history import add_to_search_history
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    if params.get('query', None): search_title = clean_file_name(params.get('query'))
    else: search_title = dialog.input('Enter search Term', type=xbmcgui.INPUT_ALPHANUM)
    if not search_title: return
    try:
        search_name = clean_file_name(urllib.unquote(search_title))
        add_to_search_history(search_name, 'easynews_video_queries')
        files = EasyNews.search(search_name)
        if not files: return dialog.ok('No results', 'No results')
        easynews_file_browser(files)
    except: pass
    xbmcplugin.setContent(__handle__, 'files')
    xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
    setView('view.easynews_files')

def easynews_file_browser(files):
    for count, item in enumerate(files, 1):
        try:
            cm = []
            name = clean_file_name(item['name']).upper()
            url_dl = item['url_dl']
            size = str(round(float(int(item['rawSize']))/1048576000, 1))
            display = '%02d | [B]%s GB[/B] | [I]%s [/I]' % (count, size, name)
            url_params = {'mode': 'media_play', 'url': item['url_dl'], 'rootname': 'nill'}
            url = build_url(url_params)
            down_file_params = {'mode': 'download_file', 'name': item['name'], 'url': item['url_dl'], 'db_type': 'easynews_file', 'image': default_easynews_icon}
            cm.append(("[B]Download File[/B]",'XBMC.RunPlugin(%s)' % build_url(down_file_params)))
            listitem = xbmcgui.ListItem(display)
            listitem.addContextMenuItems(cm)
            listitem.setArt({'thumb': default_easynews_icon, 'fanart': fanart})
            listitem.setInfo(type='video', infoLabels={'title': display, 'size': int(item['rawSize'])})
            xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=True)
        except: pass