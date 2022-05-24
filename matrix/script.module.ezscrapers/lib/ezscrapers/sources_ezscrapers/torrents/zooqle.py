# -*- coding: utf-8 -*-

"""
	EzScrapers Project
"""

import re
from urllib.parse import quote_plus, unquote_plus
from ezscrapers.modules import client
from ezscrapers.modules import source_utils
from ezscrapers.modules import workers


class source:
	priority = 5
	pack_capable = True
	hasMovies = True
	hasEpisodes = True
	def __init__(self):
		self.language = ['en', 'de', 'fr', 'ko', 'pl', 'pt', 'ru']
		self.base_link = "https://zooqle.com"
		self.search_link = '/search?pg=1&q=%s'
		self.min_seeders = 1

	def sources(self, data, hostDict):
		self.sources = []
		if not data: return self.sources
		self.sources_append = self.sources.append
		try:
			self.title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			self.title = self.title.replace('&', 'and').replace('Special Victims Unit', 'SVU').replace('/', ' ')
			self.aliases = data['aliases']
			self.episode_title = data['title'] if 'tvshowtitle' in data else None
			self.year = data['year']
			self.hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else self.year
			self.undesirables = source_utils.get_undesirables()
			self.check_foreign_audio = source_utils.check_foreign_audio()

			category = '+category%3ATV' if 'tvshowtitle' in data else '+category%3AMovies'
			query = '%s %s' % (self.title, self.hdlr)
			query = re.sub(r'[^A-Za-z0-9\s\.-]+', '', query)
			urls = []
			url = ('%s%s' % (self.base_link, self.search_link % quote_plus(query))) + str(category) + '&v=t&s=sz&sd=d'

			urls.append(url)
			urls.append(url.replace('pg=1', 'pg=2'))
			# log_utils.log('urls = %s' % urls)
			threads = []
			append = threads.append
			for url in urls:
				append(workers.Thread(self.get_sources, url))
			[i.start() for i in threads]
			[i.join() for i in threads]
			return self.sources
		except:
			source_utils.scraper_error('ZOOQLE')
			return self.sources

	def get_sources(self, url):
		try:
			# For some reason Zooqle returns 404 even though the response has a body.
			# This is probably a bug on Zooqle's server and the error should just be ignored.
			html = client.request(url, ignoreErrors=404, timeout=5)
			if not html: return
			html = html.replace('&nbsp;', ' ')
			try: table = client.parseDOM(html, 'table', attrs={'class': 'table table-condensed table-torrents vmiddle'})[0]
			except: return
			rows = client.parseDOM(table, 'tr')
			if not rows: return
		except:
			source_utils.scraper_error('ZOOQLE')
			return
		for row in rows:
			try:
				try:
					if 'magnet:' not in row: continue
					url = re.search(r'href\s*=\s*["\'](magnet:[^"\']+)["\']', row, re.I).group(1)
					url = unquote_plus(url).replace('&amp;', '&').split('&tr')[0].replace(' ', '.')
				except: continue
				hash = re.search(r'btih:(.*?)&', url, re.I).group(1)
				try:
					name = re.search(r'<a\s*class\s*=\s*["\'].+?>(.+?)</a>', row, re.I).group(1)
					name = source_utils.clean_name(unquote_plus(client.cleanHTML(name)))
				except: continue

				# some titles have foreign title translation in front so remove it
				if './.' in name: name = name.split('./.', 1)[1]
				if '.com.' in name.lower():
					try: name = re.sub(r'(.*?)\W{2,10}', '', name)
					except: name = name.split('-.', 1)[1].lstrip()

				if not source_utils.check_title(self.title, self.aliases, name, self.hdlr, self.year): continue
				name_info = source_utils.info_from_name(name, self.title, self.year, self.hdlr, self.episode_title)
				if source_utils.remove_lang(name_info, self.check_foreign_audio): continue
				if self.undesirables and source_utils.remove_undesirables(name_info, self.undesirables): continue

				if not self.episode_title: #filter for eps returned in movie query (rare but movie and show exists for Run in 2020)
					ep_strings = [r'[.-]s\d{2}e\d{2}([.-]?)', r'[.-]s\d{2}([.-]?)', r'[.-]season[.-]?\d{1,2}[.-]?']
					name_lower = name.lower()
					if any(re.search(item, name_lower) for item in ep_strings): continue

				try:
					seeders = int(re.search(r'["\']Seeders:\s*([0-9]+|[0-9]+,[0-9]+)\s*\|', row, re.I).group(1).replace(',', ''))
					if self.min_seeders > seeders: continue
				except: seeders = 0

				quality, info = source_utils.get_release_quality(name_info, url)
				try:
					size = re.search(r'((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', row).group(0)
					dsize, isize = source_utils._size(size)
					info.insert(0, isize)
				except: dsize = 0
				info = ' | '.join(info)

				self.sources_append({'provider': 'zooqle', 'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info,
												'quality': quality, 'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
			except:
				source_utils.scraper_error('ZOOQLE')

	def sources_packs(self, data, hostDict, search_series=False, total_seasons=None, bypass_filter=False):
		self.sources = []
		if not data: return self.sources
		self.sources_append = self.sources.append
		try:
			self.search_series = search_series
			self.total_seasons = total_seasons
			self.bypass_filter = bypass_filter

			self.title = data['tvshowtitle'].replace('&', 'and').replace('Special Victims Unit', 'SVU').replace('/', ' ')
			self.aliases = data['aliases']
			self.imdb = data['imdb']
			self.year = data['year']
			self.season_x = data['season']
			self.season_xx = self.season_x.zfill(2)
			self.undesirables = source_utils.get_undesirables()
			self.check_foreign_audio = source_utils.check_foreign_audio()
			category = '+category%3ATV'

			# query = re.sub(r'(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', self.title)
			query = re.sub(r'[^A-Za-z0-9\s\.-]+', '', self.title)
			if search_series:
				queries = [
						self.search_link % quote_plus(query + ' Season'),
						self.search_link % quote_plus(query + ' Complete')]
			else:
				queries = [
						self.search_link % quote_plus(query + ' S%s' % self.season_xx),
						self.search_link % quote_plus(query + ' Season %s' % self.season_x)]
			threads = []
			append = threads.append
			for url in queries:
				link = ('%s%s' % (self.base_link, url)) + str(category) + '&v=t&s=sz&sd=d'
				append(workers.Thread(self.get_sources_packs, link))
			[i.start() for i in threads]
			[i.join() for i in threads]
			return self.sources
		except:
			source_utils.scraper_error('ZOOQLE')
			return self.sources

	def get_sources_packs(self, link):
		try:
			# For some reason Zooqle returns 404 even though the response has a body.
			# This is probably a bug on Zooqle's server and the error should just be ignored.
			html = client.request(link, ignoreErrors=404, timeout=5)
			if not html: return
			html = html.replace('&nbsp;', ' ')
			try: table = client.parseDOM(html, 'table', attrs={'class': 'table table-condensed table-torrents vmiddle'})[0]
			except: return
			rows = client.parseDOM(table, 'tr')
			if not rows: return
		except:
			source_utils.scraper_error('ZOOQLE')
			return
		for row in rows:
			try:
				try:
					if 'magnet:' not in row: continue
					url = re.search(r'href\s*=\s*["\'](magnet:[^"\']+)["\']', row, re.I).group(1)
					url = unquote_plus(url).replace('&amp;', '&').split('&tr')[0].replace(' ', '.')
				except: continue
				hash = re.search(r'btih:(.*?)&', url, re.I).group(1)
				try:
					name = re.search(r'<a\s*class\s*=\s*["\'].+?>(.+?)</a>', row, re.I).group(1)
					name = source_utils.clean_name(unquote_plus(client.cleanHTML(name)))
				except: continue

				# some titles have foreign title translation in front so remove it
				if './.' in name: name = name.split('./.', 1)[1]
				if '.com.' in name.lower():
					try: name = re.sub(r'(.*?)\W{2,10}', '', name)
					except: name = name.split('-.', 1)[1].lstrip()

				episode_start, episode_end = 0, 0
				if not self.search_series:
					if not self.bypass_filter:
						valid, episode_start, episode_end = source_utils.filter_season_pack(self.title, self.aliases, self.year, self.season_x, name)
						if not valid: continue
					package = 'season'

				elif self.search_series:
					if not self.bypass_filter:
						valid, last_season = source_utils.filter_show_pack(self.title, self.aliases, self.imdb, self.year, self.season_x, name, self.total_seasons)
						if not valid: continue
					else: last_season = self.total_seasons
					package = 'show'

				name_info = source_utils.info_from_name(name, self.title, self.year, season=self.season_x, pack=package)
				if source_utils.remove_lang(name_info, self.check_foreign_audio): continue
				if self.undesirables and source_utils.remove_undesirables(name_info, self.undesirables): continue
				try:
					seeders = int(re.search(r'["\']Seeders:\s*([0-9]+|[0-9]+,[0-9]+)\s*\|', row, re.I).group(1).replace(',', ''))
					if self.min_seeders > seeders: continue
				except: seeders = 0

				quality, info = source_utils.get_release_quality(name_info, url)
				try:
					size = re.search(r'((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', row).group(0)
					dsize, isize = source_utils._size(size)
					info.insert(0, isize)
				except: dsize = 0
				info = ' | '.join(info)

				item = {'provider': 'zooqle', 'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info, 'quality': quality,
							'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize, 'package': package}
				if self.search_series: item.update({'last_season': last_season})
				elif episode_start: item.update({'episode_start': episode_start, 'episode_end': episode_end}) # for partial season packs
				self.sources_append(item)
			except:
				source_utils.scraper_error('ZOOQLE')
