import xbmcplugin, xbmcgui
import os
from sys import argv
try: from urllib import unquote, urlencode, quote
except ImportError: from urllib.parse import unquote, urlencode, quote
from apis.easynews_api import import_easynews
from modules.nav_utils import build_url, setView, translate_path
from modules.utils import clean_file_name, to_utf8
from modules.utils import local_string as ls
from modules.settings import get_theme
# from modules.utils import logger

addon_dir = translate_path('special://home/addons/plugin.video.fen')
dialog = xbmcgui.Dialog()
icon_directory = get_theme()
default_easynews_icon = os.path.join(icon_directory, 'easynews.png')
fanart = os.path.join(addon_dir, 'fanart.png')

EasyNews = import_easynews()

def search_easynews(params):
	from modules.history import add_to_search_history
	__handle__ = int(argv[1])
	default = params.get('suggestion', '')
	search_title = clean_file_name(params.get('query')) if ('query' in params and params.get('query') != 'NA') else None
	if not search_title: search_title = dialog.input('Enter search Term', type=xbmcgui.INPUT_ALPHANUM, defaultt=default)
	if not search_title: return
	try:
		search_name = clean_file_name(unquote(search_title))
		add_to_search_history(search_name, 'easynews_video_queries')
		files = EasyNews.search(search_name)
		if not files: return dialog.ok('Fen', ls(32760))
		easynews_file_browser(files, __handle__)
	except: pass
	xbmcplugin.setContent(__handle__, 'files')
	xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
	setView('view.premium')

def easynews_file_browser(files, __handle__):
	down_str = ls(32747)
	files = sorted(files, key=lambda k: k['name'])
	for count, item in enumerate(files, 1):
		try:
			cm = []
			name = clean_file_name(item['name']).upper()
			url_dl = item['url_dl']
			size = str(round(float(int(item['rawSize']))/1048576000, 1))
			display = '%02d | [B]%s GB[/B] | [I]%s [/I]' % (count, size, name)
			url_params = {'mode': 'easynews.resolve_easynews', 'url_dl': url_dl, 'play': 'true'}
			url = build_url(url_params)
			down_file_params = {'mode': 'downloader', 'name': item['name'], 'url': url_dl, 'action': 'cloud.easynews', 'image': default_easynews_icon}
			cm.append((down_str,'RunPlugin(%s)' % build_url(down_file_params)))
			listitem = xbmcgui.ListItem(display)
			listitem.addContextMenuItems(cm)
			listitem.setArt({'icon': default_easynews_icon, 'poster': default_easynews_icon, 'thumb': default_easynews_icon, 'fanart': fanart, 'banner': default_easynews_icon})
			xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=False)
		except: pass

def resolve_easynews(params):
	try: url_dl = params['url_dl']
	except: url_dl = params['url']
	resolved_link = EasyNews.resolve_easynews(url_dl)
	if params.get('play', 'false') != 'true' : return resolved_link
	from modules.player import FenPlayer
	FenPlayer().play(resolved_link)

def account_info(params):
	from datetime import datetime
	from modules.utils import jsondate_to_datetime
	try:
		account_info, usage_info = EasyNews.account()
		if not account_info or not usage_info:
			return dialog.ok('Fen', ls(32574))
		expires = jsondate_to_datetime(to_utf8(account_info[2]), "%Y-%m-%d")
		days_remaining = (expires - datetime.today()).days
		body = []
		body.append(ls(32757) % to_utf8(account_info[1]))
		body.append(ls(32755) % to_utf8(account_info[0]))
		body.append('[B]%s:[/B] %s' % (ls(32630), to_utf8(account_info[3])))
		body.append(ls(32750) % expires)
		body.append(ls(32751) % days_remaining)
		body.append('%s %s' % (ls(32772), to_utf8(usage_info[2]).replace('years', ls(32472))))
		body.append(ls(32761) % to_utf8(usage_info[0]).replace('Gigs', 'GB'))
		body.append(ls(32762) % to_utf8(usage_info[1]).replace('Gigs', 'GB'))
		return dialog.select('EASYNEWS', body)
	except Exception as e:
		line = '%s[CR]%s[CR]%s'
		return dialog.ok('Fen', line % ('', ls(32574), str(e)))
