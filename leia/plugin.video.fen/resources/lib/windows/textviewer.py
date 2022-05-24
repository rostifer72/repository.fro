# -*- coding: utf-8 -*-
from windows.base_dialog import BaseDialog
# from modules.utils import logger

class TextViewerXML(BaseDialog):
	def __init__(self, *args, **kwargs):
		super(TextViewerXML, self).__init__(self, args)
		self.window_id = 2000
		self.text = kwargs.get('text')
		self.heading = kwargs.get('heading')

	def onInit(self):
		super(TextViewerXML, self).onInit()
		self.set_properties()

	def run(self):
		self.doModal()

	def onAction(self, action):
		if action in self.closing_actions:
			self.close()

	def set_properties(self):
		self.setProperty('tikiskins.text', self.text)
		self.setProperty('tikiskins.heading', self.heading)
