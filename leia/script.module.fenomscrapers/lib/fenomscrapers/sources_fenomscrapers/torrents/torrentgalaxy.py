# -*- coding: utf-8 -*-
# created by Venom for Fenomscrapers (updated 2-26-2021)
"""
	Fenomscrapers Project
"""

import re
try: #Py2
	from urlparse import parse_qs, urljoin
	from urllib import urlencode, quote_plus, unquote_plus
except ImportError: #Py3
	from urllib.parse import parse_qs, urljoin, urlencode, quote_plus, unquote_plus

from fenomscrapers.modules import cfscrape
from fenomscrapers.modules import client
from fenomscrapers.modules import py_tools
from fenomscrapers.modules import source_utils
from fenomscrapers.modules import workers


class source:
	def __init__(self):
		self.priority = 2
		self.language = ['en']
		self.domains = ['torrentgalaxy.to', 'torrentgalaxy.mx', 'torrentgalaxy.su']
		self.base_link = 'https://torrentgalaxy.to'
		self.search_link = '/torrents.php?search=%s&sort=seeders&order=desc'
		self.min_seeders = 0
		self.pack_capable = True


	def movie(self, imdb, title, aliases, year):
		try:
			url = {'imdb': imdb, 'title': title, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			return


	def tvshow(self, imdb, tvdb, tvshowtitle, aliases, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			return


	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if not url: return
			url = parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
			url = urlencode(url)
			return url
		except:
			return


	def sources(self, url, hostDict):
		sources = []
		if not url: return sources
		try:
			scraper = cfscrape.create_scraper()
			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			title = title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			aliases = data['aliases']
			episode_title = data['title'] if 'tvshowtitle' in data else None
			year = data['year']
			hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else year

			if 'tvshowtitle' in data:
				query = '%s %s' % (title, hdlr)
				query = re.sub(r'[^A-Za-z0-9\s\.-]+', '', query)
				url = self.search_link % quote_plus(query)
			else:
				url = self.search_link % data['imdb']
			url = urljoin(self.base_link, url)
			# log_utils.log('url = %s' % url, log_utils.LOGDEBUG)
			r = py_tools.ensure_str(scraper.get(url).content, errors='replace')
			posts = client.parseDOM(r, 'div', attrs={'class': 'tgxtable'})
			if not posts: return sources
		except:
			source_utils.scraper_error('TORRENTGALAXY')
			return sources

		for post in posts:
			try:
				links = zip(
							re.findall(r'href\s*=\s*["\'](magnet:[^"\']+)["\']', post, re.DOTALL | re.I),
							re.findall(r'<span\s*class\s*=\s*["\']badge\s*badge-secondary["\']\s*style\s*=\s*["\']border-radius:4px;["\']>(.*?)</span>', post, re.DOTALL | re.I),
							re.findall(r'<span\s*title\s*=\s*["\']Seeders/Leechers["\']>\[<font\s*color\s*=\s*["\']green["\']><b>(.*?)<', post, re.DOTALL | re.I))
				for link in links:
					url = unquote_plus(link[0]).split('&tr')[0].replace(' ', '.')
					url = source_utils.strip_non_ascii_and_unprintable(url)
					hash = re.compile(r'btih:(.*?)&', re.I).findall(url)[0]

					name = url.split('&dn=')[1]
					name = source_utils.clean_name(name)
					if not source_utils.check_title(title, aliases, name, hdlr, year): continue
					name_info = source_utils.info_from_name(name, title, year, hdlr, episode_title)
					if source_utils.remove_lang(name_info): continue

					if not episode_title: #filter for eps returned in movie query (rare but movie and show exists for Run in 2020)
						ep_strings = [r'[.-]s\d{2}e\d{2}([.-]?)', r'[.-]s\d{2}([.-]?)', r'[.-]season[.-]?\d{1,2}[.-]?']
						if any(re.search(item, name.lower()) for item in ep_strings): continue

					try:
						seeders = int(link[2])
						if self.min_seeders > seeders: continue
					except: seeders = 0

					quality, info = source_utils.get_release_quality(name_info, url)
					try:
						dsize, isize = source_utils._size(link[1])
						info.insert(0, isize)
					except: dsize = 0
					info = ' | '.join(info)

					sources.append({'provider': 'torrentgalaxy', 'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info, 'quality': quality,
												'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
			except:
				source_utils.scraper_error('TORRENTGALAXY')
		return sources


	def sources_packs(self, url, hostDict, search_series=False, total_seasons=None, bypass_filter=False):
		self.sources = []
		if not url: return self.sources
		try:
			self.scraper = cfscrape.create_scraper()
			self.search_series = search_series
			self.total_seasons = total_seasons
			self.bypass_filter = bypass_filter

			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			self.title = data['tvshowtitle'].replace('&', 'and').replace('Special Victims Unit', 'SVU')
			self.aliases = data['aliases']
			self.imdb = data['imdb']
			self.year = data['year']
			self.season_x = data['season']
			self.season_xx = self.season_x.zfill(2)

			query = re.sub(r'[^A-Za-z0-9\s\.-]+', '', self.title)
			queries = [
						self.search_link % quote_plus(query + ' S%s' % self.season_xx),
						self.search_link % quote_plus(query + ' Season %s' % self.season_x)]
			if search_series:
				queries = [
						self.search_link % quote_plus(query + ' Season'),
						self.search_link % quote_plus(query + ' Complete')]
			threads = []
			for url in queries:
				link = urljoin(self.base_link, url)
				threads.append(workers.Thread(self.get_sources_packs, link))
			[i.start() for i in threads]
			[i.join() for i in threads]
			return self.sources
		except:
			source_utils.scraper_error('TORRENTGALAXY')
			return self.sources


	def get_sources_packs(self, link):
		# log_utils.log('link = %s' % str(link), __name__, log_utils.LOGDEBUG)
		try:
			r = py_tools.ensure_str(self.scraper.get(link).content, errors='replace')
			if not r: return
			posts = client.parseDOM(r, 'div', attrs={'class': 'tgxtable'})
			if not posts: return
		except:
			source_utils.scraper_error('TORRENTGALAXY')
			return

		for post in posts:
			try:
				links = zip(
							re.findall(r'href\s*=\s*["\'](magnet:[^"\']+)["\']', post, re.DOTALL | re.I),
							re.findall(r'<span\s*class\s*=\s*["\']badge\s*badge-secondary["\']\s*style\s*=\s*["\']border-radius:4px;["\']>(.*?)</span>', post, re.DOTALL | re.I),
							re.findall(r'<span\s*title\s*=\s*["\']Seeders/Leechers["\']>\[<font\s*color\s*=\s*["\']green["\']><b>(.*?)<', post, re.DOTALL | re.I))
				for link in links:
					url = unquote_plus(link[0]).split('&tr')[0].replace(' ', '.')
					url = source_utils.strip_non_ascii_and_unprintable(url)
					hash = re.compile(r'btih:(.*?)&', re.I).findall(url)[0]

					name = url.split('&dn=')[1]
					name = source_utils.clean_name(name)
					if not self.search_series:
						if not self.bypass_filter:
							if not source_utils.filter_season_pack(self.title, self.aliases, self.year, self.season_x, name):
								continue
						package = 'season'

					elif self.search_series:
						if not self.bypass_filter:
							valid, last_season = source_utils.filter_show_pack(self.title, self.aliases, self.imdb, self.year, self.season_x, name, self.total_seasons)
							if not valid: continue
						else:
							last_season = self.total_seasons
						package = 'show'

					name_info = source_utils.info_from_name(name, self.title, self.year, season=self.season_x, pack=package)
					if source_utils.remove_lang(name_info): continue

					try:
						seeders = int(link[2])
						if self.min_seeders > seeders: continue
					except: seeders = 0

					quality, info = source_utils.get_release_quality(name_info, url)
					try:
						dsize, isize = source_utils._size(link[1])
						info.insert(0, isize)
					except: dsize = 0
					info = ' | '.join(info)

					item = {'provider': 'torrentgalaxy', 'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info, 'quality': quality,
								'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize, 'package': package}
					if self.search_series: item.update({'last_season': last_season})
					self.sources.append(item)
			except:
				source_utils.scraper_error('TORRENTGALAXY')


	def resolve(self, url):
		return url