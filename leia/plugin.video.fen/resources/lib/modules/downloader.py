# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcvfs
import os

try: from urllib import unquote
except: from urllib.parse import unquote
try: from urlparse import parse_qsl, urlparse
except ImportError: from urllib.parse import parse_qsl, urlparse
try: from urllib2 import Request, urlopen
except ImportError: from urllib.request import Request, urlopen
from threading import Thread

import json
from modules.sources import Sources
from modules.nav_utils import show_busy_dialog, hide_busy_dialog, notification, sleep
from modules.utils import clean_file_name, clean_title, to_utf8, safe_string, remove_accents
from modules.utils import local_string as ls
from modules.settings_reader import get_setting
from modules.settings import download_directory
from modules.utils import logger # leave on

# window = xbmcgui.Window(10000)

image_extensions = ['jpg', 'jpeg', 'jpe', 'jif', 'jfif', 'jfi', 'bmp', 'dib', 'png', 'gif', 'webp', 'tiff', 'tif',
					'psd', 'raw', 'arw', 'cr2', 'nrw', 'k25', 'jp2', 'j2k', 'jpf', 'jpx', 'jpm', 'mj2']

levels =['../../../..', '../../..', '../..', '..']

def runner(params):
	show_busy_dialog()
	threads = []
	action = params.get('action')
	if action == 'meta.single':
		Downloader(params).run()
	elif action == 'meta.pack':
		from modules.source_utils import find_season_in_release_title
		if params['provider'] == 'furk':
			try:
				t_files = Sources().furkPacks(params['file_name'], params['file_id'], download=True)
				pack_choices = [dict(params, **{'pack_files':{'link': item['url_dl'], 'filename': item['name'], 'size': item['size']}}) for item in t_files]
			except: return notification(ls(32692))
		else:
			try:
				debrid_files, debrid_function = Sources().debridPacks(params['provider'], params['name'], params['magnet_url'], params['info_hash'], download=True)
				pack_choices = [dict(params, **{'pack_files':item}) for item in debrid_files]
			except: return notification(ls(32692))
		chosen_list = selectDebridPackItem(pack_choices)
		if not chosen_list: return
		if params['provider'] == 'furk': show_package = True
		else: show_package = json.loads(params['source']).get('package') == 'show'
		for item in chosen_list:
			if show_package:
				meta  = json.loads(item.get('meta'))
				season = find_season_in_release_title(item['pack_files']['filename'])
				if season:
					meta['season'] = season
					item['meta'] = json.dumps(meta)
				else: pass
			threads.append(Thread(target=Downloader(item).run))
		[i.start() for i in threads]
	elif action == 'image':
		for item in ('thumb_url', 'image_url'):
			image_params = params
			image_params['url'] = params.pop(item)
			image_params['db_type'] = item
			Downloader(image_params).run()
	elif action.startswith('cloud'):
		Downloader(params).run()

def selectDebridPackItem(pack_choices):
	from modules.utils import multiselect_dialog
	display_list = ['%02d | [B]%.2f GB[/B] | [I]%s[/I]' % \
					(count,
					float(i['pack_files']['size'])/1073741824,
					clean_file_name(i['pack_files']['filename']).upper())
					for count, i in enumerate(pack_choices, 1)]
	return multiselect_dialog(ls(32031), display_list, pack_choices)

class Downloader:
	def __init__(self, params):
		self.params = params
		# self.downloads_string = 'fen.current_downloads'

	# @staticmethod
	# def addDownload(add_dict):
	# 	try: current_down_list = json.loads(window.getProperty(self.downloads_string))
	# 	except: current_down_list = []
	# 	current_down_list.append(add_dict)
	# 	current_down_list = json.dumps(current_down_list)
	# 	window.setProperty(self.downloads_string, current_down_list)

	# @staticmethod
	# def updateDownload(current_down_list, ):
	# 	window.setProperty(current_down_list)

	# @staticmethod
	# def removeDownload(remove_dict):
	# 	try: current_down_list = json.loads(window.getProperty(self.downloads_string))
	# 	except: return
	# 	current_down_list.remove(remove_dict)
	# 	current_down_list = json.dumps(current_down_list)
	# 	window.setProperty(self.downloads_string, current_down_list)

	def run(self):
		self.downPrep()
		self.getURLandHeaders()
		if self.url in (None, 'None', ''):
			hide_busy_dialog()
			return notification(ls(32692), 4000)
		self.getDownFolder()
		self.getFilename()
		self.getExtension()
		self.getDestinationFolder()
		self.download_runner(self.url, self.final_destination, self.extension)

	def downPrep(self):
		if 'meta' in self.params:
			meta = json.loads(self.params.get('meta'))
			title = meta.get('search_title')
			self.db_type = meta.get('vid_type')
			self.year = meta.get('year')
			self.image = meta.get('poster')
			self.season = meta.get('season')
			self.episode = meta.get('episode')
			self.name = self.params.get('name')
		else:
			title = self.params.get('name')
			self.db_type = self.params.get('db_type')
			self.image = self.params.get('image')
			self.name = None
		self.title = clean_file_name(title)
		self.provider = self.params.get('provider')
		self.action = self.params.get('action')
		self.source = self.params.get('source')
		self.final_name = None

	def download_runner(self, url, folder_dest, ext):
		dest = os.path.join(folder_dest, self.final_name + ext)
		# try: self.current_downloads = json.loads(window.getProperty(self.downloads_string))
		# except: self.current_downloads = []
		# self.current_downloads.append({'url': url, 'folder_dest': folder_dest, 'final_name': self.final_name})
		# window.setProperty(self.downloads_string, self.current_downloads)
		self.doDownload(url, folder_dest, dest)

	def getURLandHeaders(self):
		url = self.params.get('url')
		if url in (None, 'None', ''):
			if self.action == 'meta.single':
				source = json.loads(self.source)
				url = Sources().resolve_sources(source)
			elif self.action == 'meta.pack':
				if self.provider == 'Real-Debrid':
					from apis.real_debrid_api import RealDebridAPI as debrid_function
				elif self.provider == 'Premiumize.me':
					from apis.premiumize_api import PremiumizeAPI as debrid_function
				elif self.provider == 'AllDebrid':
					from apis.alldebrid_api import AllDebridAPI as debrid_function
				url = self.params['pack_files']['link']
				if self.provider in ('Real-Debrid', 'AllDebrid'):
					url = debrid_function().unrestrict_link(url)
				elif self.provider == 'Premiumize.me':
					url = debrid_function().add_headers_to_url(url)
		else:
			if self.action.startswith('cloud'):
				if '_direct' in self.action:
					url = self.params['url']
				elif 'realdebrid' in self.action:
					from indexers.real_debrid import resolve_rd
					url = resolve_rd(self.params)
				elif 'alldebrid' in self.action:
					from indexers.alldebrid import resolve_ad
					url = resolve_ad(self.params)
				elif 'premiumize' in self.action:
					from apis.premiumize_api import PremiumizeAPI
					url = PremiumizeAPI().add_headers_to_url(url)
				elif 'easynews' in self.action:
					from indexers.easynews import resolve_easynews
					url = resolve_easynews(self.params)
		try: headers = dict(parse_qsl(url.rsplit('|', 1)[1]))
		except: headers = dict('')
		try: url = url.split('|')[0]
		except: pass
		self.url = url
		self.headers = headers

	def getDownFolder(self):
		self.down_folder = download_directory(self.db_type)
		if self.db_type == 'thumb_url':
			self.down_folder = os.path.join(self.down_folder, '.thumbs')
		for level in levels:
			try: xbmcvfs.mkdir(os.path.abspath(os.path.join(self.down_folder, level)))
			except: pass
		xbmcvfs.mkdir(self.down_folder)

	def getDestinationFolder(self):
		if self.action == 'image':
			self.final_destination = self.down_folder
		elif self.action in ('meta.single', 'meta.pack'):
			folder_rootname = '%s (%s)' % (self.title, self.year)
			self.final_destination = os.path.join(self.down_folder, folder_rootname)
			if self.db_type == 'episode':
				self.final_destination = os.path.join(self.down_folder, folder_rootname, 'Season %02d' %  int(self.season))
		else:
			self.final_destination = self.down_folder

	def getFilename(self):
		if self.final_name: final_name = self.final_name
		elif self.action == 'meta.pack':
			name = self.params['pack_files']['filename']
			final_name = os.path.splitext(urlparse(name).path)[0].split('/')[-1]
		elif self.action == 'image':
			final_name = self.title
		else:
			name_url = unquote(self.url)
			file_name = clean_title(name_url.split('/')[-1])
			if clean_title(self.title).lower() in file_name.lower():
				final_name = os.path.splitext(urlparse(name_url).path)[0].split('/')[-1]
			else:
				try: final_name = self.name.translate(None, '\/:*?"<>|').strip('.')
				except: final_name = os.path.splitext(urlparse(name_url).path)[0].split('/')[-1]
		self.final_name = to_utf8(safe_string(remove_accents(final_name)))

	def getExtension(self):
		if self.action == 'archive':
			ext = '.zip'
		if self.action == 'audio':
			ext = os.path.splitext(urlparse(self.url).path)[1][1:]
			if not ext in ['wav', 'mp3', 'ogg', 'flac', 'wma', 'aac']: ext = 'mp3'
			ext = '.%s' % ext
		elif self.action == 'image':
			ext = os.path.splitext(urlparse(self.url).path)[1][1:]
			ext = '.%s' % ext
		else:
			ext = os.path.splitext(urlparse(self.url).path)[1][1:]
			if not ext in ['mp4', 'mkv', 'flv', 'avi', 'mpg']: ext = 'mp4'
			ext = '.%s' % ext
		self.extension = ext

	def confirmDownload(self, mb):
		line = '%s[CR]%s[CR]%s'
		if self.action not in ('image', 'meta.pack'):
			if not xbmcgui.Dialog().yesno('Fen', line % ('[B]%s[/B]' % self.final_name.upper(), ls(32688) % mb, ls(32689))): return False
		return True

	def doDownload(self, url, folder_dest, dest):
		headers = self.headers
		file = dest.rsplit(os.sep, 1)[-1]
		resp = self.getResponse(url, headers, 0)
		if not resp:
			hide_busy_dialog()
			xbmcgui.Dialog().ok('Fen', ls(32490))
			return
		try:    content = int(resp.headers['Content-Length'])
		except: content = 0
		try:    resumable = 'bytes' in resp.headers['Accept-Ranges'].lower()
		except: resumable = False
		if content < 1:
			hide_busy_dialog()
			xbmcgui.Dialog().ok('Fen', ls(32490))
			return
		size = 1024 * 1024
		mb   = content / (1024 * 1024)
		if content < size:
			size = content
		hide_busy_dialog()
		if not self.confirmDownload(mb): return
		if self.action not in ('image', 'meta.pack'):
			show_notifications = get_setting('download.notification') == 'true'
			suppress_during_playback = get_setting('download.suppress') == 'true'
			try: notification_frequency = int(get_setting('download.frequency'))
			except: notification_frequency = 10
		else:
			if self.action == 'meta.pack': notification(ls(32134), 3500, self.image)
			show_notifications = False
			notification_frequency = 0
		notify  = notification_frequency
		total   = 0
		errors  = 0
		count   = 0
		resume  = 0
		sleep_time   = 0
		xbmcvfs.mkdir(folder_dest)
		f = xbmcvfs.File(dest, 'w')
		chunk  = None
		chunks = []
		while True:
			downloaded = total
			for c in chunks: downloaded += len(c)
			percent = min(round(float(downloaded)*100 / content), 100)
			playing = xbmc.Player().isPlaying()
			if show_notifications:
				if percent >= notify:
					notify += notification_frequency
					try:
						line1 = '%s - [I]%s[/I]' % (str(percent)+'%', self.final_name)
						if playing and not suppress_during_playback: notification(line1, 3000, self.image)
						elif (not playing): notification(line1, 3000, self.image)
					except Exception as e:
						logger('download progress exception', str(e))
			chunk = None
			error = False
			try:        
				chunk  = resp.read(size)
				if not chunk:
					if percent < 99:
						error = True
					else:
						while len(chunks) > 0:
							c = chunks.pop(0)
							f.write(c)
							del c
						f.close()
						try: progressDialog.close()
						except Exception: pass
						return self.done(self.final_name, self.db_type, True, self.image)
			except Exception as e:
				logger('error', str(e))
				error = True
				sleep_time = 10
				errno = 0
				if hasattr(e, 'errno'):
					errno = e.errno
				if errno == 10035: # 'A non-blocking socket operation could not be completed immediately'
					pass
				if errno == 10054: #'An existing connection was forcibly closed by the remote host'
					errors = 10 #force resume
					sleep_time  = 30
				if errno == 11001: # 'getaddrinfo failed'
					errors = 10 #force resume
					sleep_time  = 30
			if chunk:
				errors = 0
				chunks.append(chunk)
				if len(chunks) > 5:
					c = chunks.pop(0)
					f.write(c)
					total += len(c)
					del c
			if error:
				errors += 1
				count  += 1
				sleep(sleep_time*1000)
			if (resumable and errors > 0) or errors >= 10:
				if (not resumable and resume >= 50) or resume >= 500:
					try:
						progressDialog.close()
					except Exception:
						pass
					return self.done(self.final_name, self.db_type, False, self.image)
				resume += 1
				errors  = 0
				if resumable:
					chunks  = []
					resp = self.getResponse(url, headers, total)
				else:
					pass

	def getResponse(self, url, headers, size):
		try:
			if size > 0:
				size = int(size)
				headers['Range'] = 'bytes=%d-' % size
			req = Request(url, headers=headers)
			resp = urlopen(req, timeout=15)
			return resp
		except:
			return None

	def done(self, title, db_type, downloaded, image):
		if self.db_type == 'thumb_url': return
		if self.db_type == 'image_url':
			if downloaded: notification('[I]%s[/I]' % ls(32576), 2500, image)
			else: notification('[I]%s[/I]' % ls(32691), 2500, image)
		else:
			playing = xbmc.Player().isPlaying()
			if downloaded:
				text = '[B]%s[/B] : %s' % (title, '[COLOR forestgreen]%s %s[/COLOR]' % (ls(32107), ls(32576)))
			else:
				text = '[B]%s[/B] : %s' % (title, '[COLOR red]%s %s[/COLOR]' % (ls(32107), ls(32490)))
			if (not downloaded) or (not playing): 
				xbmcgui.Dialog().ok('Fen', text)



