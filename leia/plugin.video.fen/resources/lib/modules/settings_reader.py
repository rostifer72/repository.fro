# -*- coding: utf-8 -*-
import xbmcgui
import json
# from modules.utils import logger

window = xbmcgui.Window(10000)

def get_setting(setting_id, fallback=None):
	try: settings_dict = json.loads(window.getProperty('fen_settings'))
	except: settings_dict = make_settings_dict()
	if settings_dict is None: settings_dict = get_settings_fallback(setting_id)
	value = settings_dict.get(setting_id, '')
	if fallback is None: return value
	if value == '': return fallback
	return value

def get_settings_fallback(setting_id):
	from xbmcaddon import Addon
	return {setting_id: Addon().getSetting(setting_id)}

def set_setting(setting_id, value):
	from xbmcaddon import Addon
	Addon().setSetting(setting_id, value)

def make_settings_dict():
	import xbmcvfs
	import os
	import xml.etree.ElementTree as ET
	from modules.nav_utils import get_kodi_version, translate_path
	settings_dict = None
	try:
		kodi_version = get_kodi_version()
		profile_dir = translate_path('special://profile/addon_data/plugin.video.fen/')
		if not xbmcvfs.exists(profile_dir): xbmcvfs.mkdirs(profile_dir)
		settings_xml = os.path.join(profile_dir, 'settings.xml')
		root = ET.parse(settings_xml).getroot()
		settings_dict = {}
		for item in root:
			setting_id = item.get('id')
			if kodi_version >= 18: setting_value = item.text
			else: setting_value = item.get('value')
			if setting_value is None: setting_value = ''
			dict_item = {setting_id: setting_value}
			settings_dict.update(dict_item)
		window.setProperty('fen_settings', json.dumps(settings_dict))
	except: pass
	return settings_dict
