# -*- coding: utf-8 -*-
import xbmcgui, xbmcplugin, xbmcvfs
import os
from sys import argv
from threading import Thread
import json
from windows.slideshow import SlideShowXML
from modules.settings import skin_location
from apis.tmdb_api import tmdb_media_images, tmdb_people_pictures, tmdb_people_tagged_pictures
from apis.imdb_api import imdb_images, people_get_imdb_id, imdb_people_images
from modules.nav_utils import build_url, add_dir, setView, translate_path, execute_builtin, notification
from modules.utils import local_string as ls
# from modules.utils import logger

addon_dir = translate_path('special://home/addons/plugin.video.fen')
profile_dir = translate_path('special://profile/addon_data/plugin.video.fen/')

icon = os.path.join(addon_dir, "icon.png")
fanart = os.path.join(addon_dir, "fanart.png")
tmdb_image_base = 'https://image.tmdb.org/t/p/%s%s'


class Images():
	def run(self, params):
		self.params = params
		self.mode = self.params.pop('mode')
		if self.mode == 'people_image_results':
			self.people_image_results()
		elif self.mode == 'people_tagged_image_results':
			self.people_tagged_image_results()
		elif self.mode == 'tmdb_artwork_image_results':
			self.tmdb_artwork_image_results()
		elif self.mode == 'imdb_image_results':
			self.imdb_image_results()
		elif self.mode == 'browser_image':
			self.browser_image(params['folder_path'])
		elif self.mode == 'slideshow_image':
			return self.slideshow_image()
		elif self.mode == 'delete_image':
			folder_path = self.delete_image()
			try: self.list_items, self.all_images_json, self.next_page_params = self.browser_image(folder_path)
			except: return
		if len(self.list_items) == 0:
			return notification(ls(32575))
		if not 'in_progress' in params:
			self.open_window_xml()
		else:
			return self.list_items, self.all_images_json, self.next_page_params

	def open_window_xml(self):
		from windows.thumbviewer import ThumbViewerXML
		self.win = ThumbViewerXML('thumbviewer.xml', skin_location(), list_items=self.list_items, next_page_params= self.next_page_params,
								all_images_json=self.all_images_json, ImagesInstance=self)
		self.win.run()
		del self.win

	def tmdb_artwork_image_results(self):
		def builder():
			for count, item in enumerate(image_info, 1):
				try:
					listitem = xbmcgui.ListItem()
					image_url = tmdb_image_base % ('original', item['file_path'])
					thumb_url = tmdb_image_base % ('w185', item['file_path'])
					name = '%03d_%sx%s' % (count, item['height'], item['width'])
					listitem.setProperty('tikiskins.thumb', thumb_url)
					listitem.setProperty('tikiskins.image', image_url)
					listitem.setProperty('tikiskins.name', name)
					yield listitem
				except: pass
		db_type = self.params['db_type']
		tmdb_id = self.params['tmdb_id']
		image_type = self.params['image_type']
		results = tmdb_media_images(db_type, tmdb_id)
		image_info = sorted(results[image_type], key=lambda x: x['file_path'])
		self.all_images_json = json.dumps([(tmdb_image_base % ('original', i['file_path']), '%sx%s' % (i['height'], i['width'])) for i in image_info])
		self.list_items = list(builder())
		self.next_page_params = {}

	def imdb_image_results(self):
		def builder(rolling_count):
			for item in image_info:
				try:
					listitem = xbmcgui.ListItem()
					rolling_count += 1
					name = '%s_%03d' % (item['title'], rolling_count)
					listitem.setProperty('tikiskins.thumb', item['thumb'])
					listitem.setProperty('tikiskins.image', item['image'])
					listitem.setProperty('tikiskins.name', name)
					yield listitem
				except: pass
		imdb_id = self.params['imdb_id']
		page_no = self.params['page_no']
		rolling_count = int(self.params['rolling_count'])
		image_info, next_page = imdb_images(imdb_id, page_no)
		image_info = sorted(image_info, key=lambda x: x['title'])
		self.all_images_json = json.dumps([(i['image'], i['title']) for i in image_info])
		self.list_items = list(builder(rolling_count))
		rolling_count = rolling_count + len(image_info)
		self.next_page_params = {'mode': 'imdb_image_results', 'imdb_id': imdb_id, 'page_no': next_page, 'rolling_count': rolling_count}

	def people_image_results(self):
		def get_tmdb():
			try: tmdb_results.append(tmdb_people_pictures(actor_id))
			except: pass
		def get_imdb():
			imdb_id = people_get_imdb_id(actor_name, actor_id)
			try: imdb_results.append(imdb_people_images(imdb_id, page_no)[0])
			except: pass
		def builder():
			for item in all_images:
				try:
					listitem = xbmcgui.ListItem()
					listitem.setProperty('tikiskins.thumb', item[2])
					listitem.setProperty('tikiskins.image', item[1])
					listitem.setProperty('tikiskins.name', item[0])
					yield listitem
				except: pass
		threads = []
		tmdb_images = []
		all_images = []
		tmdb_results = []
		imdb_results = []
		actor_name = self.params['actor_name']
		actor_id = self.params['actor_id']
		actor_image = self.params['actor_image']
		page_no = self.params['page_no']
		rolling_count = int(self.params['rolling_count'])
		if page_no == 1: threads.append(Thread(target=get_tmdb))
		threads.append(Thread(target=get_imdb))
		[i.start() for i in threads]
		[i.join() for i in threads]
		if page_no == 1:
			tmdb_image_info = sorted(tmdb_results[0]['profiles'], key=lambda x: x['file_path'])
			tmdb_images = [('%sx%s_%03d' % (i['height'], i['width'], count), tmdb_image_base % ('original', i['file_path']), tmdb_image_base % ('w185', i['file_path'])) for count, i in enumerate(tmdb_image_info, rolling_count+1)]
			all_images.extend(tmdb_images)
		rolling_count = rolling_count + len(tmdb_images)
		imdb_image_info = sorted(imdb_results[0], key=lambda x: x['title'])
		imdb_images = [('%s_%03d' % (i['title'], count), i['image'], i['thumb']) for count, i in enumerate(imdb_image_info, rolling_count+1)]
		all_images.extend(imdb_images)
		rolling_count = rolling_count + len(imdb_images)
		self.all_images_json = json.dumps([(i[1], i[0]) for i in all_images])
		self.list_items = list(builder())
		self.next_page_params = {'mode': 'people_image_results', 'actor_id': actor_id, 'actor_name': actor_name, 'actor_image': actor_image, 'page_no': page_no+1, 'rolling_count': rolling_count}

	def people_tagged_image_results(self):
		def builder(rolling_count):
			for item in image_info:
				try:
					rolling_count += 1
					thumb_url = tmdb_image_base % ('w185', item['file_path'])
					image_url = tmdb_image_base % ('original', item['file_path'])
					name = '%s_%03d' % (item['media']['title'], rolling_count)
					listitem = xbmcgui.ListItem()
					listitem.setProperty('tikiskins.thumb', thumb_url)
					listitem.setProperty('tikiskins.image', image_url)
					listitem.setProperty('tikiskins.name', name)
					yield listitem
				except: pass
		actor_name = self.params['actor_name']
		actor_id = self.params['actor_id']
		actor_image = self.params['actor_image']
		page_no = self.params['page_no']
		rolling_count = int(self.params['rolling_count'])
		try: results = tmdb_people_tagged_pictures(actor_id, page_no)
		except: results = []
		image_info = sorted(results['results'], key=lambda x: x['file_path'])
		self.all_images_json = json.dumps([(tmdb_image_base % ('original', i['file_path']), i['media']['title']) for i in image_info])
		self.list_items = list(builder(rolling_count))
		self.next_page_params = {'mode': 'people_tagged_image_results', 'actor_id': actor_id, 'actor_name': actor_name, 'actor_image': actor_image, 'page_no': page_no+1, 'rolling_count': rolling_count}

	def browser_image(self, folder_path):
		def builder():
			for item in files:
				try:
					listitem = xbmcgui.ListItem()
					image_url = os.path.join(folder_path, item)
					try:
						thumb_url = [i for i in thumbs if i == item][0]
						thumb_url = os.path.join(thumbs_path, thumb_url)
					except:
						thumb_url = image_url
					listitem.setProperty('tikiskins.thumb', thumb_url)
					listitem.setProperty('tikiskins.image', image_url)
					listitem.setProperty('tikiskins.name', item)
					listitem.setProperty('tikiskins.delete', 'true')
					listitem.setProperty('tikiskins.folder_path', folder_path)
					yield listitem
				except: pass
		files = xbmcvfs.listdir(folder_path)[1]
		files = sorted(files)
		thumbs_path = os.path.join(folder_path, '.thumbs')
		thumbs = xbmcvfs.listdir(thumbs_path)[1]
		thumbs = sorted(thumbs)
		self.all_images_json = json.dumps([(os.path.join(folder_path, i), i)for i in files])
		self.list_items = list(builder())
		self.next_page_params = {}

	def delete_image(self):
		image_url = self.params['image_url']
		thumb_url = self.params['thumb_url']
		folder_path = self.params['folder_path']
		if not xbmcgui.Dialog().yesno('Fen', ls(32580)): return
		xbmcvfs.delete(thumb_url)
		try:
			xbmcvfs.delete(image_url)
		except:
			notification(ls(32490), 1500)
			return folder_path
		notification(ls(32576), 1500)
		return folder_path

	def slideshow_image(self):
		all_images = self.params['all_images']
		current_index = self.params['current_index']
		all_images = json.loads(all_images)
		window = SlideShowXML('slideshow.xml', skin_location(), all_images=all_images, index=int(current_index))
		ending_position = window.run()
		del window
		return ending_position
