# -*- coding: utf-8 -*-
import os
from windows.base_dialog import BaseDialog
from windows.base_contextmenu import BaseContextMenu
from modules.nav_utils import translate_path, show_busy_dialog, hide_busy_dialog
from modules.utils import local_string as ls
from modules.settings import skin_location, get_theme
# from modules.utils import logger

addon_dir = translate_path('special://home/addons/plugin.video.fen')
icon = os.path.join(addon_dir, "icon.png")
fanart = os.path.join(addon_dir, "fanart.png")

class ThumbViewerXML(BaseDialog):
	def __init__(self, *args, **kwargs):
		super(ThumbViewerXML, self).__init__(self, args)
		self.window_id = 2000
		self.list_items = kwargs.get('list_items')
		self.all_images_json = kwargs.get('all_images_json')
		self.next_page_params = kwargs.get('next_page_params')
		self.ImagesInstance = kwargs.get('ImagesInstance')
		self.current_page = 1

	def onInit(self):
		super(ThumbViewerXML, self).onInit()
		self.set_properties()
		if self.next_page_params and len(self.list_items) >= 48: self.make_next_page()
		self.win = self.getControl(self.window_id)
		self.win.addItems(self.list_items)
		self.setFocusId(self.window_id)

	def run(self):
		self.doModal()
		try: del self.cm
		except: pass

	def onAction(self, action):
		action_id = action.getId()
		position = self.get_position(self.window_id)
		if action_id in self.closing_actions:
			self.previous_page()
		if action_id in self.selection_actions:
			chosen_listitem = self.list_items[position]
			if chosen_listitem.getProperty('tikiskins.next_page_item') == 'true':
				self.new_page()
			else:
				slideshow_params = {'mode': 'slideshow_image', 'all_images': self.all_images_json, 'current_index': self.get_position(self.window_id)}
				ending_position = self.ImagesInstance.run(slideshow_params)
				self.win.selectItem(ending_position)
		elif action_id in self.context_actions:
			chosen_listitem = self.list_items[position]
			self.cm = ThumbContextMenuXML('contextmenu.xml', skin_location(), list_item=chosen_listitem)
			cm_choice = self.cm.run()
			if cm_choice: self.execute_code(cm_choice)
			del self.cm

	def new_page(self):
		try:
			show_busy_dialog()
			self.win.reset()
			self.current_page += 1
			self.next_page_params['in_progress'] = 'true'
			self.list_items, self.all_images_json, self.next_page_params = self.ImagesInstance.run(self.next_page_params)
			hide_busy_dialog()
			self.onInit()
		except: self.close()

	def previous_page(self):
		try:
			self.win.reset()
			self.current_page -= 1
			if self.current_page < 1: self.close()
			self.next_page_params['page_no'] = self.current_page
			self.next_page_params['in_progress'] = 'true'
			self.list_items, self.all_images_json, self.next_page_params = self.ImagesInstance.run(self.next_page_params)
			self.onInit()
		except: self.close()

	def make_next_page(self):
		listitem = self.make_listitem()
		listitem.setProperty('tikiskins.name', ls(32799))
		listitem.setProperty('tikiskins.thumb', os.path.join(get_theme(), 'item_next.png'))
		listitem.setProperty('tikiskins.next_page_item', 'true')
		self.list_items.append(listitem)

	def set_properties(self):
		self.setProperty('tikiskins.page_no', str(self.current_page))

class ThumbContextMenuXML(BaseContextMenu):
	def __init__(self, *args, **kwargs):
		super(ThumbContextMenuXML, self).__init__(self, args)
		self.window_id = 2002
		self.list_item = kwargs['list_item']
		self.item_list = []
		self.selected = None
		self.make_context_menu()

	def onInit(self):
		super(ThumbContextMenuXML, self).onInit()
		self.set_properties()
		win = self.getControl(self.window_id)
		win.addItems(self.item_list)
		self.setFocusId(self.window_id)

	def run(self):
		self.doModal()
		return self.selected

	def onAction(self, action):
		action_id = action.getId()
		if action_id in self.selection_actions:
			chosen_listitem = self.item_list[self.get_position(self.window_id)]
			self.selected = chosen_listitem.getProperty('tikiskins.context.action')
			return self.close()
		if action_id in self.context_actions:
			return self.close()
		if action_id in self.closing_actions:
			return self.close()

	def set_properties(self):
		self.setProperty('tikiskins.context.highlight', 'royalblue')

	def make_context_menu(self):
		enable_delete = self.list_item.getProperty('tikiskins.delete') == 'true'
		image_url = self.list_item.getProperty('tikiskins.image')
		thumb_url = self.list_item.getProperty('tikiskins.thumb')
		if enable_delete:
			folder_path = self.list_item.getProperty('tikiskins.folder_path')
			delete_file_params = {'mode': 'delete_image', 'image_url': image_url, 'thumb_url': thumb_url, 'folder_path': folder_path, 'in_progress': 'true'}
			self.item_list.append(self.make_item('[B]%s[/B]' % ls(32785), 'RunPlugin(%s)', delete_file_params))
		else:
			name = self.list_item.getProperty('tikiskins.name')
			down_file_params = {'mode': 'downloader', 'action': 'image', 'name': name, 'thumb_url': thumb_url, 'image_url': image_url, 'db_type': 'image', 'image': icon}
			self.item_list.append(self.make_item(ls(32747), 'RunPlugin(%s)', down_file_params))
		
