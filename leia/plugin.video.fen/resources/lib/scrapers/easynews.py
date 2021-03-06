# -*- coding: utf-8 -*-
import sys
import json
from apis.easynews_api import import_easynews
from modules.source_utils import get_release_quality, get_file_info, check_title, internal_results
from modules.utils import clean_file_name, normalize
from modules.settings_reader import get_setting
# from modules.utils import logger

EasyNews = import_easynews()

class EasyNewsSource:
	def __init__(self):
		self.scrape_provider = 'easynews'
		self.title_filter = get_setting('%s.title_filter' % self.scrape_provider) == 'true'
		self.sources = []

	def results(self, info):
		try:
			self.title = info.get('title')
			self.search_title = clean_file_name(self.title)
			self.db_type = info.get('db_type')
			self.year = info.get('year')
			self.years = '%s,%s,%s' % (str(int(self.year - 1)), self.year, str(int(self.year + 1)))
			self.season = info.get('season')
			self.episode = info.get('episode')
			search_name = self._search_name()
			files = EasyNews.search(search_name)
			if not files: return internal_results(self.scrape_provider, self.sources)
			aliases = json.loads(info.get('aliases', []))
			try: self.aliases = [i['title'] for i in aliases]
			except: self.aliases = []
			def _process():
				for item in files:
					try:
						file_name = normalize(item['name'])
						if self.title_filter:
							if not check_title(self.title, file_name, self.aliases, self.year, self.season, self.episode): continue
						URLName = clean_file_name(file_name).replace('html', ' ').replace('+', ' ').replace('-', ' ')
						url_dl = item['url_dl']
						size = float(int(item['rawSize']))/1073741824
						details = get_file_info(file_name)
						video_quality = get_release_quality(file_name, url_dl)
						source_item = {'name': file_name,
										'title': file_name,
										'URLName': URLName,
										'quality': video_quality,
										'size': size,
										'size_label': '%.2f GB' % size,
										'extraInfo': details,
										'url_dl': url_dl,
										'id': url_dl,
										'local': False,
										'direct': True,
										'source': self.scrape_provider,
										'scrape_provider': self.scrape_provider}
						yield source_item
					except Exception as e:
						from modules.utils import logger
						logger('FEN easynews yield source', str(e))
			self.sources = list(_process())
		except Exception as e:
			from modules.utils import logger
			logger('FEN easynews scraper Exception', str(e))
		internal_results(self.scrape_provider, self.sources)
		return self.sources

	def _search_name(self):
		if self.db_type == 'movie': search_name = '"%s" %s' % (self.search_title, self.years)
		else: search_name = '%s S%02dE%02d' % (self.search_title,  int(self.season), int(self.episode))
		return search_name

	def to_bytes(self, num, unit):
		unit = unit.upper()
		if unit.endswith('B'): unit = unit[:-1]
		units = ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']
		try: mult = pow(1024, units.index(unit))
		except: mult = sys.maxint
		return int(float(num) * mult)

