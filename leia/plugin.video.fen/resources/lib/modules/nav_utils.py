# -*- coding: utf-8 -*-
import xbmc, xbmcvfs
import os
from sys import argv
from modules.utils import local_string as ls
from modules.utils import to_utf8
from modules.settings_reader import get_setting, set_setting
try: from urllib import urlencode
except ImportError: from urllib.parse import urlencode
# from modules.utils import logger

def build_navigate_to_page(params):
	import xbmcgui
	import json
	from modules.settings import get_theme, nav_jump_use_alphabet
	use_alphabet = nav_jump_use_alphabet()
	invoker_on = get_setting('reuse_language_invoker') == 'true'
	icon = os.path.join(get_theme(), 'item_jump.png')
	fanart = os.path.join(translate_path('special://home/addons/plugin.video.fen'), "fanart.png")
	db_type = params.get('db_type')
	def _make_list(use_alphabet):
		for i in start_list:
			if use_alphabet: display1, display2 = i.upper(), ls(32821) % (db_type, i.upper())
			else: display1, display2 = '%s %s' % (ls(32022), i), ls(32822) % i
			listitem = xbmcgui.ListItem(display1, display2)
			listitem.setArt({'icon': icon, 'fanart': fanart})
			yield listitem
	if use_alphabet:
		start_list = [chr(i) for i in range(97,123)]
	else:
		start_list = [str(i) for i in range(1, int(params.get('total_pages'))+1)]
		start_list.remove(params.get('current_page'))
	choice_list = list(_make_list(use_alphabet))
	chosen_start = xbmcgui.Dialog().select('Fen', choice_list, useDetails=True)
	sleep(100)
	if chosen_start < 0: return
	new_start = start_list[chosen_start]
	if use_alphabet: new_page, new_letter = '', new_start
	else: new_page, new_letter = new_start, None
	url_params = {'mode': params.get('transfer_mode', ''),
					'action': params.get('transfer_action', ''),
					'new_page': new_page,
					'new_letter': new_letter,
					'media_type': params.get('media_type', ''),
					'query': params.get('query', ''),
					'actor_id': params.get('actor_id', ''),
					'user': params.get('user', ''),
					'slug': params.get('slug', ''),
					'final_params': params.get('final_params', '')}
	if not invoker_on:
		sleep(1500)
		url_params = {'mode': 'container_update', 'final_params': json.dumps(url_params)}
	execute_builtin('RunPlugin(%s)' % build_url(url_params))

def paginate_list(item_list, page, letter, limit=20):
	from modules.utils import chunks
	def _get_start_index(letter):
		if letter == 't':
			try:
				beginswith_tuple = ('s', 'the s', 'a s', 'an s')
				indexes = [i for i,v in enumerate(title_list) if v.startswith(beginswith_tuple)]
				start_index = indexes[-1:][0] + 1
			except: start_index = None
		else:
			beginswith_tuple = (letter, 'the %s' % letter, 'a %s' % letter, 'an %s' % letter)
			try: start_index = next(i for i,v in enumerate(title_list) if v.startswith(beginswith_tuple))
			except: start_index = None
		return start_index
	if letter != 'None':
		from itertools import chain
		try: from itertools import zip_longest
		except ImportError: from itertools import izip_longest as zip_longest
		title_list = [i['title'].lower() for i in item_list]
		start_list = [chr(i) for i in range(97,123)]
		letter_index = start_list.index(letter)
		base_list = [element for element in list(chain.from_iterable([val for val in zip_longest(start_list[letter_index:], start_list[:letter_index][::-1])])) if element != None]
		for i in base_list:
			start_index = _get_start_index(i)
			if start_index: break
		item_list = item_list[start_index:]
	pages = list(chunks(item_list, limit))
	total_pages = len(pages)
	return pages[page - 1], total_pages

def toggle_jump_to():
	from modules.settings import nav_jump_use_alphabet
	(setting, new_action) = ('0', ls(32022)) if nav_jump_use_alphabet() else ('1', ls(32023))
	toggle_setting(setting_id='nav_jump', setting_value=setting, refresh=True)
	notification(ls(32851) % new_action)

def container_update(params):
	import json
	try: final_params = json.loads(params['final_params'])
	except: final_params = params['final_params']
	execute_builtin('Container.Update(%s)' % build_url(final_params))

def container_refresh(params):
	import json
	try: final_params = json.loads(params['final_params'])
	except: final_params = params['final_params']
	execute_builtin('Container.Refresh(%s)' % build_url(final_params))

def translate_path(path):
	try: translate = xbmcvfs.translatePath(path)
	except: translate = xbmc.translatePath(path)
	return translate

def sleep(time):
	return xbmc.sleep(time)

def execute_builtin(command):
	return xbmc.executebuiltin(command)

def extended_info_open(db_type, tmdb_id):
	if db_type in ('movie', 'movies'): function = 'extendedinfo'
	else: function = 'extendedtvinfo'
	return execute_builtin('RunScript(script.extendedinfo,info=%s,id=%s)' % (function, tmdb_id))

def volume_checker():
	"""
	0% == -60db, 100% == 0db
	"""
	try:
		if get_setting('volumecheck.enabled', 'false') == 'false': return
		if xbmc.getCondVisibility('Player.Muted'): return
		from modules.utils import string_alphanum_to_num
		max_volume = int(min(int(get_setting('volumecheck.percent', '100')), 100))
		current_volume_db = int(string_alphanum_to_num(xbmc.getInfoLabel('Player.Volume').split('.')[0]))
		current_volume_percent = int(100 - ((float(current_volume_db)/60)*100))
		if current_volume_percent > max_volume: execute_builtin('SetVolume(%d)' % int(max_volume))
	except: pass

def get_search_term(db_type, query=None):
	import xbmcgui
	if not query:
		try: from urllib import unquote
		except ImportError: from urllib.parse import unquote
		query = xbmcgui.Dialog().input("Fen", type=xbmcgui.INPUT_ALPHANUM)
		if not query: return
		query = unquote(query)
	(mode, action) = ('build_movie_list', 'tmdb_movies_search') if db_type == 'movie' else ('build_tvshow_list', 'tmdb_tv_search')
	return execute_builtin('Container.Update(%s)' % build_url({'mode': mode, 'action': action, 'query': query}))

def get_kodi_version():
	return int(xbmc.getInfoLabel("System.BuildVersion")[0:2])

def get_skin():
	return xbmc.getSkinDir()

def show_busy_dialog():
	if get_kodi_version() >= 18: return execute_builtin('ActivateWindow(busydialognocancel)')
	else: return execute_builtin('ActivateWindow(busydialog)')

def hide_busy_dialog():
	if get_kodi_version() >= 18: return execute_builtin('Dialog.Close(busydialognocancel)')
	else: return execute_builtin('Dialog.Close(busydialog)')

def close_all_dialog():
	execute_builtin('Dialog.Close(all,true)')

def focus_index(index):
	import xbmcgui
	sleep(100)
	current_window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
	focus_id = current_window.getFocusId()
	try: current_window.getControl(focus_id).selectItem(index)
	except: pass

def play_trailer(url, all_trailers=[]):
	if all_trailers:
		import xbmcgui
		import json
		from modules.utils import clean_file_name, to_utf8
		all_trailers = to_utf8(json.loads(all_trailers))
		if len(all_trailers) == 1:
			video_id = all_trailers[0].get('key')
		else:
			video_choice = xbmcgui.Dialog().select('Fen', [clean_file_name(i['name']) for i in all_trailers])
			if video_choice < 0: return
			video_id = all_trailers[video_choice].get('key')
		url = 'plugin://plugin.video.youtube/play/?video_id=%s' % video_id
	try: execute_builtin('RunPlugin(%s)' % url)
	except: notification(ls(32574))

def show_text(heading, text=None, file=None):
	from modules.settings import skin_location
	from windows.textviewer import TextViewerXML
	if file:
		try:
			with open(file, encoding="utf-8") as r: text = r.read()
		except:
			with open(file) as r: text = r.read()
	window = TextViewerXML('textviewer.xml', skin_location(), heading=heading, text=text)
	window.run()
	del window

def open_settings(query, addon='plugin.video.fen'):
	sleep(250)
	if query:
		try:
			kodi_version = get_kodi_version()
			button = -100 if kodi_version <= 17 else 100
			control = -200 if kodi_version <= 17 else 80
			hide_busy_dialog()
			menu, function = query.split('.')
			execute_builtin('Addon.OpenSettings(%s)' % addon)
			execute_builtin('SetFocus(%i)' % (int(menu) - button))
			execute_builtin('SetFocus(%i)' % (int(function) - control))
		except: execute_builtin('Addon.OpenSettings(%s)' % addon)
	else:
		execute_builtin('Addon.OpenSettings(%s)' % addon)

def toggle_setting(setting_id, setting_value, refresh=False):
	set_setting(setting_id, setting_value)
	if refresh: execute_builtin('Container.Refresh')

def build_url(url_params):
	try: url = 'plugin://plugin.video.fen/?' + urlencode(url_params)
	except: url = 'plugin://plugin.video.fen/?' + urlencode(to_utf8(url_params))
	return url

def notification(line1, time=5000, icon=None, sound=False):
	import xbmcgui
	if not icon: icon = os.path.join(translate_path('special://home/addons/plugin.video.fen'), "icon.png")
	xbmcgui.Dialog().notification('Fen', line1, icon, time, sound)

def add_dir(url_params, list_name, iconImage='DefaultFolder.png', fanartImage=None, isFolder=True):
	import xbmcgui, xbmcplugin
	from modules.settings import get_theme
	if not fanartImage: fanartImage = os.path.join(translate_path('special://home/addons/plugin.video.fen'), "fanart.png")
	icon = os.path.join(get_theme(), iconImage)
	url = build_url(url_params)
	listitem = xbmcgui.ListItem(list_name)
	listitem.setArt({'icon': icon, 'poster': icon, 'thumb': icon, 'fanart': fanartImage, 'banner': icon})
	xbmcplugin.addDirectoryItem(handle=int(argv[1]), url=url, listitem=listitem, isFolder=isFolder)

def external_browse():
	return 'fen' not in xbmc.getInfoLabel('Container.PluginName')

def setView(view_type, content='files'):
	if external_browse(): return
	from modules.settings import check_database
	try: from sqlite3 import dbapi2 as database
	except: from pysqlite2 import dbapi2 as database
	views_db = translate_path('special://profile/addon_data/plugin.video.fen/views.db')
	check_database(views_db)
	if not content == 'addons': sleep(500)
	t = 0
	try:
		dbcon = database.connect(views_db)
		dbcur = dbcon.cursor()
		while not xbmc.getInfoLabel('Container.Content') == content:
			if external_browse(): return
			t += 1
			if t >= 20: return
			sleep(100)
		dbcur.execute("SELECT view_id FROM views WHERE view_type = ?", (str(view_type),))
		view_id = dbcur.fetchone()[0]
		execute_builtin("Container.SetViewMode(%s)" % str(view_id))
		dbcon.close()
	except: return

def link_folders(service, folder_name, action):
	import xbmcgui
	from caches import fen_cache
	def _get_media_type():
		from modules.settings import get_theme
		for item in [('movie', ls(32028), 'movies.png'), ('tvshow', ls(32029), 'tv.png')]:
			line1 = '[B]%s[/B]' % item[1]
			line2 = ls(32693) % item[1]
			icon = os.path.join(get_theme(), item[2])
			listitem = xbmcgui.ListItem(line1, line2)
			listitem.setArt({'icon': icon})
			listitem.setProperty('media_type', item[0])
			media_type_list.append(listitem)
		chosen_media_type = dialog.select('Fen', media_type_list, useDetails=True)
		return chosen_media_type
	dialog = xbmcgui.Dialog()
	_cache = fen_cache.FenCache()
	string = 'FEN_%s_%s' % (service, folder_name)
	current_link = _cache.get(string)
	media_type_list = []
	if action == 'remove':
		if not current_link: return
		if not dialog.yesno('Fen', ls(32694) % current_link): return
		from modules.settings import check_database
		try: from sqlite3 import dbapi2 as database
		except ImportError: from pysqlite2 import dbapi2 as database
		cache_file = translate_path('special://profile/addon_data/plugin.video.fen/fen_cache2.db')
		check_database(cache_file)
		dbcon = database.connect(cache_file)
		dbcur = dbcon.cursor()
		dbcur.execute("DELETE FROM fencache WHERE id=?", (string,))
		dbcon.commit()
		dbcon.close()
		xbmcgui.Window(10000).clearProperty(string)
		if service == 'FOLDER':
			clear_cache('folder_scraper', silent=True)
		execute_builtin("Container.Refresh")
		return dialog.ok('Fen', ls(32576))
	if current_link:
		line = '%s[CR]%s[CR]%s'
		if not dialog.yesno('Fen', line % (ls(32695), '[B]%s[/B]' % current_link, ls(32696))): return
	media_type = _get_media_type()
	if media_type < 0: return
	media_type = media_type_list[media_type].getProperty('media_type')
	title = dialog.input(ls(32228)).lower()
	if not title: return
	from apis.tmdb_api import tmdb_movies_title_year, tmdb_tv_title_year
	year = dialog.input('%s (%s)' % (ls(32543), ls(32669)), type=xbmcgui.INPUT_NUMERIC)
	function = tmdb_movies_title_year if media_type == 'movie' else tmdb_tv_title_year
	results = function(title, year)['results']
	if len(results) == 0: return dialog.ok('Fen', ls(32490))
	name_key = 'title' if media_type == 'movie' else 'name'
	released_key = 'release_date' if media_type == 'movie' else 'first_air_date'
	choice_list = []
	for item in results:
		title = item[name_key]
		try: year = item[released_key].split('-')[0]
		except: year = ''
		if year: rootname = '%s (%s)' % (title, year)
		else: rootname = title
		line1 = rootname
		line2 = '[I]%s[/I]' % item['overview']
		icon = 'https://image.tmdb.org/t/p/w92%s' % item['poster_path'] if item.get('poster_path') else os.path.join(translate_path('special://home/addons/plugin.video.fen'), "fanart.png")
		listitem = xbmcgui.ListItem(line1, line2)
		listitem.setArt({'icon': icon})
		listitem.setProperty('rootname', rootname)
		choice_list.append(listitem)
	chosen_title = dialog.select("Fen", choice_list, useDetails=True)
	if chosen_title < 0: return
	from datetime import timedelta
	rootname = choice_list[chosen_title].getProperty('rootname')
	_cache.set(string, rootname, expiration=timedelta(days=365))
	if service == 'FOLDER':
		clear_cache('folder_scraper', silent=True)
	execute_builtin("Container.Refresh")
	return dialog.ok('Fen', ls(32576))

def clean_settings():
	import xbmcgui, xbmcaddon
	import xml.etree.ElementTree as ET
	from modules import py_tools
	def _make_content(dict_object):
		if kodi_version >= 18:
			content = '<settings version="2">'
			for item in dict_object:
				if item['id'] in active_settings:
					if 'default' in item and 'value' in item: content += '\n    <setting id="%s" default="%s">%s</setting>' % (item['id'], item['default'], item['value'])
					elif 'default' in item: content += '\n    <setting id="%s" default="%s"></setting>' % (item['id'], item['default'])
					elif 'value' in item: content += '\n    <setting id="%s">%s</setting>' % (item['id'], item['value'])
					else: content += '\n    <setting id="%s"></setting>'
				else: removed_settings.append(item)
		else:
			content = '<settings>'
			for item in dict_object:
				if item['id'] in active_settings:
					if 'value' in item: content += '\n    <setting id="%s" value="%s" />' % (item['id'], item['value'])
					else: content += '\n    <setting id="%s" value="" />' % item['id']
				else: removed_settings.append(item)
		content += '\n</settings>'
		return content
	close_all_dialog()
	sleep(200)
	line = '%s[CR]%s[CR]%s'
	progressDialog = xbmcgui.DialogProgress()
	progressDialog.create(ls(32577), line % ('', '', ''))
	progressDialog.update(0, line % ('  ', '', ''))
	kodi_version = get_kodi_version()
	addon_ids = ['plugin.video.fen', 'script.module.fenomscrapers', 'script.module.myaccounts']
	addon_names = [xbmcaddon.Addon(id=i).getAddonInfo('name') for i in addon_ids]
	addon_dirs = [translate_path(xbmcaddon.Addon(id=i).getAddonInfo('path')) for i in addon_ids]
	profile_dirs = [translate_path(xbmcaddon.Addon(id=i).getAddonInfo('profile')) for i in addon_ids]
	active_settings_xmls = [os.path.join(translate_path(xbmcaddon.Addon(id=i).getAddonInfo('path')), 'resources', 'settings.xml') for i in addon_ids]
	if py_tools.isPY3: params = list(zip(addon_names, profile_dirs, active_settings_xmls))
	else: params = zip(addon_names, profile_dirs, active_settings_xmls)
	for addon in params:
		try:
			try:
				if progressDialog.iscanceled(): break
			except Exception: pass
			current_progress = params.index(addon)+1
			removed_settings = []
			active_settings = []
			current_user_settings = []
			root = ET.parse(addon[2]).getroot()
			for item in root.findall('./category/setting'):
				setting_id = item.get('id')
				if setting_id:
					active_settings.append(setting_id)
			settings_xml = os.path.join(addon[1], 'settings.xml')
			root = ET.parse(settings_xml).getroot()
			for item in root:
				dict_item = {}
				setting_id = item.get('id')
				setting_default = item.get('default')
				if kodi_version >= 18: setting_value = item.text
				else: setting_value = item.get('value')
				dict_item['id'] = setting_id
				if setting_value: dict_item['value'] = setting_value
				if setting_default: dict_item['default'] = setting_default
				current_user_settings.append(dict_item)
			new_content = _make_content(current_user_settings)
			xml_file = xbmcvfs.File(settings_xml, 'w')
			xml_file.write(new_content)
			xml_file.close()
			percent = int((current_progress/float(len(params)))*100)
			line2 = ls(32812) % addon[0]
			line3 = ls(32813) % len(removed_settings)
			progressDialog.update(percent, line % ('', line2, line3))
		except:
			notification(ls(32574), 2000)
		sleep(800)
	try:
		progressDialog.close()
	except Exception:
		pass
	xbmcgui.Dialog().ok('Fen', ls(32576))

def backup_settings():
	import xbmcgui
	import os
	from modules import py_tools
	from modules.utils import multiselect_dialog
	if py_tools.isPY2: from modules.zfile_py2 import ZipFile
	else: from modules.zfile import ZipFile
	try:
		user_data = [(ls(32817), '.xml'), (ls(32818), '.db')]
		preselect = [0,1]
		dialog_list = [i[0] for i in user_data]
		function_list = [i[1] for i in user_data]
		backup_exts = multiselect_dialog(ls(32820), dialog_list, function_list, preselect=preselect)
		if not backup_exts: return
		dialog = xbmcgui.Dialog()
		profile_dir = translate_path('special://profile/addon_data/plugin.video.fen/')
		backup_path = translate_path(get_setting('backup_directory'))
		if backup_path in ('', None): return dialog.ok('Fen', ls(32490))
		temp_zip = translate_path(os.path.join(profile_dir, 'fen_settings.zip'))
		backup_zip = translate_path(os.path.join(backup_path, 'fen_settings.zip'))
		root_len = len(profile_dir)
		line1 = ls(32576)
		show_busy_dialog()
		try:
			with ZipFile(temp_zip, 'w') as zippy:
				for folder_name, subfolders, filenames in os.walk(profile_dir):
					for item in filenames:
						if any(item.endswith(i) for i in backup_exts):
							file_path = os.path.join(folder_name, item)
							zippy.write(file_path, file_path[root_len:])
			xbmcvfs.copy(temp_zip, backup_zip)
			xbmcvfs.delete(temp_zip)
		except Exception:
			line1 = ls(32490)
	except Exception:
		line1 = ls(32490)
	hide_busy_dialog()
	dialog.ok('FEN', line1)

def restore_settings():
	import xbmcgui
	import os
	from modules import py_tools
	if py_tools.isPY2: from modules.zfile_py2 import ZipFile
	else: from modules.zfile import ZipFile
	try:
		dialog = xbmcgui.Dialog()
		profile_dir = translate_path('special://profile/addon_data/plugin.video.fen/')
		backup_path = translate_path(get_setting('backup_directory'))
		if backup_path in ('', None): return dialog.ok('Fen', ls(32490))
		temp_zip = translate_path(os.path.join(profile_dir, 'fen_settings.zip'))
		backup_zip = translate_path(os.path.join(backup_path, 'fen_settings.zip'))
		if not xbmcvfs.exists(backup_zip): return dialog.ok('Fen', ls(32490))
		line1 = ls(32576)
		show_busy_dialog()
		try:
			xbmcvfs.copy(backup_zip, temp_zip)
			with ZipFile(temp_zip, "r") as zip_file:
				zip_file.extractall(profile_dir)
			xbmcvfs.delete(temp_zip)
		except Exception:
			line1 = ls(32490)
	except Exception:
		line1 = ls(32490)
	hide_busy_dialog()
	dialog.ok('Fen', line1)

def clear_settings_window_properties():
	import xbmcgui
	from modules.utils import local_string as ls
	xbmcgui.Window(10000).clearProperty('fen_settings')
	notification(ls(32576), 2500)

def open_MyAccounts(params):
	import xbmcgui
	from myaccounts import openMASettings
	query = params.get('query', None)
	openMASettings(query)
	sleep(100)
	while xbmc.getCondVisibility('Window.IsVisible(addonsettings)') or xbmcgui.Window(10000).getProperty('myaccounts.active') == 'true':
		sleep(250)
	sleep(100)
	sync_MyAccounts()
	sleep(100)
	open_settings('1.0')

def sync_MyAccounts(silent=False):
	import myaccounts
	from modules.settings_reader import get_setting, set_setting
	all_acct = myaccounts.getAll()
	try:
		trakt_acct = all_acct.get('trakt')
		trakt_user = get_setting('trakt_user')
		set_setting('trakt_access_token', trakt_acct.get('token'))
		if trakt_user != trakt_acct.get('username'):
			set_setting('trakt_expires_at', trakt_acct.get('expires'))
			set_setting('trakt_refresh_token', trakt_acct.get('refresh'))
			set_setting('trakt_user', trakt_acct.get('username'))
			trakt_user = trakt_acct.get('username')
			if trakt_user not in ('', None):
				set_setting('trakt_indicators_active', 'true')
				set_setting('watched_indicators', '1')
		if trakt_user not in ('', None):
			set_setting('trakt_indicators_active', 'true')
	except: pass
	try:
		fu_acct = all_acct.get('furk')
		if get_setting('furk_login') != fu_acct.get('username') or get_setting('furk_password') != fu_acct.get('password'):
			set_setting('furk_login', fu_acct.get('username'))
			set_setting('furk_password', fu_acct.get('password'))
		if fu_acct.get('api_key', None):
			if get_setting('furk_api_key') != fu_acct.get('api_key'):
				set_setting('furk_api_key', fu_acct.get('api_key'))
	except: pass
	try:
		en_acct = all_acct.get('easyNews')
		if get_setting('easynews_user') != en_acct.get('username') or get_setting('easynews_password') != en_acct.get('password'):
			set_setting('easynews_user', en_acct.get('username'))
			set_setting('easynews_password', en_acct.get('password'))
	except: pass
	try:
		ad_acct = all_acct.get('alldebrid')
		set_setting('ad.token', ad_acct.get('token'))
		if get_setting('ad.account_id') != ad_acct.get('username'):
			set_setting('ad.account_id', ad_acct.get('username'))
	except: pass
	try:
		pm_acct = all_acct.get('premiumize')
		set_setting('pm.token', pm_acct.get('token'))
		if get_setting('pm.account_id') != pm_acct.get('username'):
			set_setting('pm.account_id', pm_acct.get('username'))
	except: pass
	try:
		rd_acct = all_acct.get('realdebrid')
		set_setting('rd.token', rd_acct.get('token'))
		set_setting('rd.auth', rd_acct.get('token'))
		if get_setting('rd.username') != rd_acct.get('username'):
			set_setting('rd.username', rd_acct.get('username'))
			set_setting('rd.client_id', rd_acct.get('client_id'))
			set_setting('rd.refresh', rd_acct.get('refresh'))
			set_setting('rd.secret', rd_acct.get('secret'))
	except: pass
	try:
		tmdb_acct = all_acct.get('tmdb')
		if get_setting('tmdb_api') != tmdb_acct.get('api_key'):
			set_setting('tmdb_api', tmdb_acct.get('api_key'))
	except: pass
	try:
		fanart_acct = all_acct.get('fanart_tv')
		if get_setting('fanart_client_key') != fanart_acct.get('api_key'):
			set_setting('fanart_client_key', fanart_acct.get('api_key'))
	except: pass
	try:
		imdb_acct = all_acct.get('imdb')
		if get_setting('imdb_user') != imdb_acct.get('user'):
			set_setting('imdb_user', imdb_acct.get('user'))
	except: pass
	if not silent: notification(ls(33030), time=1500)

def toggle_language_invoker():
	import xbmcgui, xbmcaddon
	import xml.etree.ElementTree as ET
	from modules.utils import gen_file_hash
	close_all_dialog()
	sleep(100)
	dialog = xbmcgui.Dialog()
	addon_dir = translate_path('special://home/addons/plugin.video.fen')
	addon_xml = os.path.join(addon_dir, 'addon.xml')
	tree = ET.parse(addon_xml)
	root = tree.getroot()
	try: current_value = [str(i.text) for i in root.iter('reuselanguageinvoker')][0]
	except: return
	current_setting = get_setting('reuse_language_invoker')
	new_value = 'false' if current_value == 'true' else 'true'
	if not dialog.yesno('Fen', ls(33018) % (current_value.upper(), new_value.upper())) > 0: return
	if new_value == 'true':
		if not dialog.yesno('Fen', ls(33019)): return
	for item in root.iter('reuselanguageinvoker'):
		item.text = new_value
		hash_start = gen_file_hash(addon_xml)
		tree.write(addon_xml)
		hash_end = gen_file_hash(addon_xml)
		if hash_start != hash_end:
			toggle_setting('reuse_language_invoker', new_value)
		else: return dialog.ok('Fen', ls(32574))
	if not dialog.yesno('Fen', ls(33020)): return
	execute_builtin('LoadProfile(%s)' % xbmc.getInfoLabel('system.profilename'))

def remove_meta_keys(dict_item, db_type):
	if db_type == 'movie':
		remove = ('fanart_added', 'cast', 'poster', 'rootname', 'imdb_id', 'tmdb_id', 'tvdb_id', 'all_trailers',
				'fanart', 'banner', 'clearlogo', 'clearart', 'landscape', 'discart', 'original_title', 'search_title',
				'extra_info', 'alternative_titles', 'country_codes', 'fanarttv_fanart', 'fanarttv_poster')
	elif db_type == 'tvshow':
		remove = ('fanart_added', 'cast', 'poster', 'rootname', 'imdb_id', 'tmdb_id', 'tvdb_id', 'all_trailers', 'discart',
				'total_episodes', 'total_seasons', 'total_watched', 'total_unwatched', 'fanart', 'banner', 'clearlogo',
				'clearart', 'landscape', 'season_data', 'original_title', 'search_title', 'extra_info', 'alternative_titles',
				'season_summary', 'country_codes', 'fanarttv_fanart', 'fanarttv_poster')
	else:# episode
		remove = ('thumb',)
	for k in remove: dict_item.pop(k, None)
	return dict_item

def refresh_cached_data(db_type, id_type, media_id, from_list=False):
	import metadata
	try:
		metadata.delete_cache_item(db_type, id_type, media_id)
		if db_type == 'tvshow':
			metadata.delete_all_seasons_memory_cache(media_id)
		if from_list: return True
		notification(ls(32576))
		execute_builtin('Container.Refresh')
	except:
		if from_list: return False
		notification(ls(32574), 4500)

def clear_cache(cache_type, silent=False):
	import xbmcgui
	from modules.utils import confirm_dialog
	profile_dir = translate_path('special://profile/addon_data/plugin.video.fen/')
	if cache_type == 'meta':
		from metadata import delete_meta_cache
		if not delete_meta_cache(silent=silent): return
	elif cache_type == 'internal_scrapers':
		if not silent:
			if not confirm_dialog(): return
		from apis import furk_api
		from apis import easynews_api
		furk_api.clear_media_results_database()
		easynews_api.clear_media_results_database()
		for item in ('pm_cloud', 'rd_cloud', 'ad_cloud', 'folder_scraper'): clear_cache(item, silent=True)
	elif cache_type == 'external_scrapers':
		from modules.source_utils import deleteProviderCache
		from caches.debrid_cache import DebridCache
		data = deleteProviderCache(silent=silent)
		debrid_cache = DebridCache().clear_database()
		if not (data, debrid_cache) == ('success', 'success'): return
	elif cache_type == 'trakt':
		from caches.trakt_cache import clear_all_trakt_cache_data
		if not clear_all_trakt_cache_data(silent=silent): return
	elif cache_type == 'imdb':
		if not silent:
			if not confirm_dialog(): return
		from apis.imdb_api import clear_imdb_cache
		if not clear_imdb_cache(): return
	elif cache_type == 'pm_cloud':
		if not silent:
			if not confirm_dialog(): return
		from apis.premiumize_api import PremiumizeAPI
		if not PremiumizeAPI().clear_cache(): return
	elif cache_type == 'rd_cloud':
		if not silent:
			if not confirm_dialog(): return
		from apis.real_debrid_api import RealDebridAPI
		if not RealDebridAPI().clear_cache(): return
	elif cache_type == 'ad_cloud':
		if not silent:
			if not confirm_dialog(): return
		from apis.alldebrid_api import AllDebridAPI
		if not AllDebridAPI().clear_cache(): return
	elif cache_type == 'folder_scraper':
		from caches.fen_cache import FenCache
		FenCache().delete_all_folderscrapers()
	else: # 'list'
		if not silent:
			if not confirm_dialog(): return
		from caches.fen_cache import FenCache
		FenCache().delete_all_lists()
	if not silent: notification(ls(32576))

def clear_all_cache():
	import xbmcgui
	from modules.utils import confirm_dialog
	dialog = xbmcgui.Dialog()
	if not confirm_dialog(): return
	line = '%s[CR]%s[CR]%s'
	progress_dialog = xbmcgui.DialogProgress()
	progress_dialog.create('Fen', '')
	caches = [('meta', '%s %s' % (ls(32527), ls(32524))), ('internal_scrapers', '%s %s' % (ls(32096), ls(32524))), ('external_scrapers', '%s %s' % (ls(32118), ls(32524))),
			('trakt', ls(32087)), ('imdb', '%s %s' % (ls(32064), ls(32524))), ('list', '%s %s' % (ls(32815), ls(32524))),
			('pm_cloud', '%s %s' % (ls(32061), ls(32524))), ('rd_cloud', '%s %s' % (ls(32054), ls(32524))), ('ad_cloud', '%s %s' % (ls(32063), ls(32524)))]
	for count, cache_type in enumerate(caches, 1):
		progress_dialog.update(int(float(count) / float(len(caches)) * 100), line % ('', '%s....' % ls(32816), cache_type[1]))
		clear_cache(cache_type[0], silent=True)
		sleep(400)
	progress_dialog.close()
	sleep(250)
	dialog.ok('Fen', ls(32576))

def clear_scrapers_cache(silent=False):
	for item in ('internal_scrapers', 'external_scrapers'): clear_cache(item, silent=True)
	if not silent: notification(ls(32576))

def clear_and_rescrape(content, query, meta):
	import json
	show_busy_dialog()
	clear_scrapers_cache(silent=True)
	meta_json = json.dumps(meta)
	if content in ('movie', 'movies'):
		play_params = {'mode': 'play_media', 'vid_type': 'movie', 'query': query, 'tmdb_id': meta['tmdb_id'], 'meta': meta_json, 'autoplay': False}
	else:
		play_params = {'mode': 'play_media', 'vid_type': 'episode', 'tmdb_id': meta['tmdb_id'],
					'query': query, 'tvshowtitle': meta['rootname'], 'season': meta['season'],
					'episode': meta['episode'], 'meta': meta_json, 'autoplay': False}
	hide_busy_dialog()
	sleep(100)
	return execute_builtin('RunPlugin(%s)' % build_url(play_params))

def refresh_icon():
	import xbmcgui
	try: from sqlite3 import dbapi2 as database
	except ImportError: from pysqlite2 import dbapi2 as database
	from modules.utils import confirm_dialog
	try:
		icon_path = os.path.join(translate_path('special://home/addons/plugin.video.fen'), "icon.png")
		thumbs_folder = translate_path('special://thumbnails')
		TEXTURE_DB = translate_path(os.path.join('special://database', 'Textures13.db'))
		dbcon = database.connect(TEXTURE_DB)
		dbcur = dbcon.cursor()
		dbcur.execute("""SELECT cachedurl FROM texture WHERE url = ?""", (icon_path,))
		image = dbcur.fetchone()[0]
		dbcon.close()
		removal_path = os.path.join(thumbs_folder, image)
		if confirm_dialog:
			xbmcvfs.delete(removal_path)
			sleep(200)
			execute_builtin('ReloadSkin()')
			sleep(500)
			notice = ls(32576)
		else: return
	except:
		notice = ls(32574)
	notification(notice)
