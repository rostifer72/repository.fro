# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcvfs
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from threading import Thread
import _strptime  # fix bug in python import
from modules.source_utils import cleanProviderDatabase, checkDatabase
from modules.settings_reader import get_setting, set_setting, make_settings_dict
from modules.nav_utils import get_kodi_version, sync_MyAccounts, translate_path, execute_builtin
from services import listitem_actions
from modules.utils import gen_file_hash, local_string
from modules import settings
from modules.utils import logger

window = xbmcgui.Window(10000)

monitor = xbmc.Monitor()

class CheckSettingsFile:
	def run(self):
		logger('FEN', 'CheckSettingsFile Service Starting')
		window.clearProperty('fen_settings')
		profile_dir = translate_path('special://profile/addon_data/plugin.video.fen/')
		if not xbmcvfs.exists(profile_dir):
			xbmcvfs.mkdirs(profile_dir)
		settings_xml = os.path.join(profile_dir, 'settings.xml')
		if not xbmcvfs.exists(settings_xml):
			__addon__ = settings.addon()
			addon_version = __addon__.getAddonInfo('version')
			__addon__.setSetting('version_number', addon_version)
			monitor.waitForAbort(0.5)
		make_settings_dict()
		return logger('FEN', 'CheckSettingsFile Service Finished')

class SyncMyAccounts:
	def run(self):
		logger('FEN', 'SyncMyAccounts Service Starting')
		sync_MyAccounts(silent=True)
		return logger('FEN', 'SyncMyAccounts Service Finished')

class ReuseLanguageInvokerCheck:
	def run(self):
		logger('FEN', 'ReuseLanguageInvokerCheck Service Starting')
		if get_kodi_version() < 18: return
		addon_dir = translate_path('special://home/addons/plugin.video.fen')
		addon_xml = os.path.join(addon_dir, 'addon.xml')
		tree = ET.parse(addon_xml)
		root = tree.getroot()
		current_addon_setting = get_setting('reuse_language_invoker', 'true')
		try: current_xml_setting = [str(i.text) for i in root.iter('reuselanguageinvoker')][0]
		except: return logger('FEN', 'ReuseLanguageInvokerCheck Service Finished')
		if current_xml_setting == current_addon_setting:
			return logger('FEN', 'ReuseLanguageInvokerCheck Service Finished')
		for item in root.iter('reuselanguageinvoker'):
			item.text = current_addon_setting
			hash_start = gen_file_hash(addon_xml)
			tree.write(addon_xml)
			hash_end = gen_file_hash(addon_xml)
			logger('FEN', 'ReuseLanguageInvokerCheck Service Finished')
			if hash_start != hash_end:
				if not xbmcgui.Dialog().yesno('Fen', '%s\n%s' % (local_string(33021), local_string(33020))): return
				current_profile = xbmc.getInfoLabel('system.profilename')
				execute_builtin('LoadProfile(%s)' % current_profile)
			else: xbmcgui.Dialog().ok('Fen', local_string(32574))

class AutoRun:
	def run(self):
		try:
			logger('FEN', 'AutoRun Service Starting')
			if settings.auto_start_fen(): execute_builtin('RunAddon(plugin.video.fen)')
			logger('FEN', 'AutoRun Service Finished')
			return
		except: return

class ClearSubs:
	def run(self):
		logger('FEN', 'Clear Subtitles Service Starting')
		if get_setting('subtitles.clear_on_start') == 'true':
			subtitle_path = translate_path('special://temp/')
			files = xbmcvfs.listdir(subtitle_path)[1]
			for i in files:
				try:
					if i.startswith('FENSubs_'): xbmcvfs.delete(os.path.join(subtitle_path, i))
				except: pass
		logger('FEN', 'Clear Subtitles Service Finished')

class ClearTraktServices:
	def run(self):
		logger('FEN', 'Trakt Service Starting')
		if settings.refresh_trakt_on_startup():
			try:
				from caches.trakt_cache import clear_cache_on_startup
				clear_cache_on_startup()
			except: pass
		if settings.sync_fen_watchstatus():
			try:
				from apis.trakt_api import sync_watched_trakt_to_fen
				sync_watched_trakt_to_fen(dialog=False)
			except: pass
		logger('FEN', 'Trakt Service Finished')

class CleanExternalSourcesDatabase:
	def run(self):
		logger('FEN', 'Clean External Sources Service Starting')
		checkDatabase()
		cleanProviderDatabase()
		logger('FEN', 'Clean External Sources Service Finished')

class ListItemNotifications():
	db_types = ['movie', 'tvshow', 'season', 'episode']
	def run(self):
		logger('FEN', 'Listitem Monitor Service Starting')
		previous_label, current_label, highlight_time = '', '', 0
		while not monitor.abortRequested():
			if get_setting('notification.enabled', 'false') == 'true':
				try:
					threads = []
					settings.list_actions_global()
					previous_label, highlight_time, activate_function, current_dbtype, current_label = self.getInfo(previous_label, highlight_time)
					if activate_function:
						if get_setting('notification.nextep') == 'true' and current_dbtype == 'tvshow':
							threads.append(Thread(target=listitem_actions.nextep_notification, args=(0,)))
						if get_setting('notification.watched_status') == 'true':
							threads.append(Thread(target=listitem_actions.watched_status_notification, args=(current_dbtype,1)))
						if get_setting('notification.progress') == 'true':
							threads.append(Thread(target=listitem_actions.progress_notification, args=(current_dbtype,2)))
						if get_setting('notification.duration_finish') == 'true' and current_dbtype in ('movie', 'episode'):
							threads.append(Thread(target=listitem_actions.duration_finish_notification, args=(current_dbtype, 3)))
						if get_setting('notification.last_aired') == 'true' and current_dbtype == 'tvshow':
							threads.append(Thread(target=listitem_actions.last_aired_notification, args=(4,)))
						if get_setting('notification.next_aired') == 'true' and current_dbtype == 'tvshow':
							threads.append(Thread(target=listitem_actions.next_aired_notification, args=(5,)))
						if get_setting('notification.production_status') == 'true' and current_dbtype in ('movie', 'tvshow'):
							threads.append(Thread(target=listitem_actions.production_status_notification, args=(6,)))
						if get_setting('notification.budget_revenue') == 'true' and current_dbtype == 'movie':
							threads.append(Thread(target=listitem_actions.budget_revenue_notification, args=(7,)))
						[i.start() for i in threads]
						[i.join() for i in threads]
						try: self.processNotifications(current_dbtype, current_label)
						except: pass
				except: pass
				monitor.waitForAbort(self.delay)
			else:
				monitor.waitForAbort(5.0)
		logger('FEN', 'Listitem Monitor Service Finished')
		return

	def getInfo(self, previous_label, highlight_time):
		activate_function = False
		in_fen = xbmc.getInfoLabel('Container.PluginName') == 'plugin.video.fen'
		widget = xbmc.getInfoLabel('ListItem.Property(fen_widget)') == 'true'
		current_dbtype = xbmc.getInfoLabel('ListItem.dbtype')
		current_label = xbmc.getInfoLabel('ListItem.label')
		proceed = (in_fen or widget) and current_dbtype in self.db_types
		if proceed:
			self.delay = 0.1
			if current_label != previous_label:
				highlight_time = time.time()
			pause = time.time() - highlight_time
			previous_label = current_label
			try: delay = float(int(get_setting('notification.delay')))/1000
			except: delay = float(2000)/1000
			if highlight_time and pause >= delay:
				activate_function = True
				highlight_time = 0
		else:
			self.delay = 2.0
			previous_label = ''
		return previous_label, highlight_time, activate_function, current_dbtype, current_label

	def processNotifications(self, current_dbtype, current_label):
		try: duration = int(get_setting('notification.duration'))
		except: duration = 2500
		wait = float(duration)/1000
		notifications = sorted([i for i in settings.list_actions if i is not None], key=lambda x: x[3])
		length = len(notifications)
		for count, item in enumerate(notifications, 1):
			try:
				if self.visibilityCheck(current_dbtype, current_label):
					xbmcgui.Dialog().notification(item[0], item[1], item[2], duration, False)
					if count != length: monitor.waitForAbort(wait)
				else: break
			except: pass

	def visibilityCheck(self, current_dbtype, current_label):
		if not xbmc.getInfoLabel('ListItem.dbtype') == current_dbtype: return False
		if not xbmc.getInfoLabel('ListItem.label') == current_label: return False
		current_id = xbmcgui.getCurrentWindowId()
		if not current_id in (10000, 10025): return False
		if not xbmc.getCondVisibility('Control.HasFocus(%s)' % str(xbmcgui.Window(current_id).getFocusId())): return False
		if monitor.abortRequested(): return False
		if xbmc.Player().isPlaying(): return False
		return True


