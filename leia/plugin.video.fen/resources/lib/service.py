# -*- coding: utf-8 -*-
import xbmc, xbmcgui
from threading import Thread
from services import service_functions
from modules.settings_reader import make_settings_dict
from modules.utils import logger

window = xbmcgui.Window(10000)

class Main(xbmc.Monitor):
	def __init__ (self):
		xbmc.Monitor.__init__(self)
		logger('FEN', 'Main Monitor Service Starting')
		logger('FEN', 'Settings Monitor Service Starting')
		self.startUpServices()
	
	def startUpServices(self):
		threads = []
		functions = [service_functions.ListItemNotifications().run,]
		for item in functions: threads.append(Thread(target=item))
		while not self.abortRequested():
			try: service_functions.CheckSettingsFile().run()
			except: pass
			try: service_functions.SyncMyAccounts().run()
			except: pass
			try: service_functions.ReuseLanguageInvokerCheck().run()
			except: pass
			try: service_functions.AutoRun().run()
			except: pass
			try: service_functions.ClearSubs().run()
			except: pass
			try: service_functions.ClearTraktServices().run()
			except: pass
			try: service_functions.CleanExternalSourcesDatabase().run()
			except: pass
			[i.start() for i in threads]
			break

	def onSettingsChanged(self):
		window.clearProperty('fen_settings')
		xbmc.sleep(50)
		refreshed = make_settings_dict()

Main().waitForAbort()

logger('FEN', 'Settings Monitor Service Finished')
logger('FEN', 'Main Monitor Service Finished')
