# -*- coding: utf-8 -*-
import time
import json
from threading import Thread
from urllib.parse import unquote
import metadata
from fenomscrapers import sources
from windows import open_window, create_window
from scrapers import external, folders
from modules import debrid, resolver, kodi_utils, settings
from modules.player import FenPlayer
from modules.settings_reader import get_setting
from modules.source_utils import internal_sources, internal_folders_import, scraper_names, get_cache_expiry
from modules.utils import clean_file_name, string_to_float, safe_string, remove_accents, get_datetime
from modules.kodi_utils import logger

show_busy_dialog, hide_busy_dialog = kodi_utils.show_busy_dialog, kodi_utils.hide_busy_dialog
close_all_dialog, select_dialog, confirm_dialog = kodi_utils.close_all_dialog, kodi_utils.select_dialog, kodi_utils.confirm_dialog
get_property, set_property, clear_property= kodi_utils.get_property, kodi_utils.set_property, kodi_utils.clear_property
ls, monitor, translate_path, notification, sleep = kodi_utils.local_string, kodi_utils.monitor, kodi_utils.translate_path, kodi_utils.notification, kodi_utils.sleep
auto_play, active_internal_scrapers, provider_sort_ranks,  = settings.auto_play, settings.active_internal_scrapers, settings.provider_sort_ranks
display_sleep_time, scraping_settings, include_prerelease_results = settings.display_sleep_time, settings.scraping_settings, settings.include_prerelease_results
ignore_results_filter, filter_status, results_sort_order = settings.ignore_results_filter, settings.filter_status, settings.results_sort_order
display_uncached_torrents, check_prescrape_sources = settings.display_uncached_torrents, settings.check_prescrape_sources
metadata_user_info, quality_filter, sort_to_top  = settings.metadata_user_info, settings.quality_filter, settings.sort_to_top
results_xml_style, results_xml_window_number = settings.results_xml_style, settings.results_xml_window_number
debrid_enabled, debrid_type_enabled, debrid_valid_hosts = debrid.debrid_enabled, debrid.debrid_type_enabled, debrid.debrid_valid_hosts
resolve_cached_torrents, resolve_uncached_torrents = resolver.resolve_cached_torrents, resolver.resolve_uncached_torrents
resolve_internal_sources, resolve_debrid = resolver.resolve_internal_sources, resolver.resolve_debrid
quality_ranks = {'4K': 1, '1080p': 2, '720p': 3, 'SD': 4, 'SCR': 5, 'CAM': 5, 'TELE': 5}
cloud_scrapers, folder_scrapers = ('rd_cloud', 'pm_cloud', 'ad_cloud'), ('folder1', 'folder2', 'folder3', 'folder4', 'folder5')
default_internal_scrapers = ('furk', 'easynews', 'rd_cloud', 'pm_cloud', 'ad_cloud', 'folders')
hevc_filter_key, hdr_filter_key, dolby_vision_filter_key = '[B]HEVC[/B]', '[B]HDR[/B]', '[B]D/VISION[/B]'
dialog_format, remaining_format = '[COLOR %s][B]%s[/B][/COLOR] 4K: %s | 1080p: %s | 720p: %s | SD: %s | Total: %s', ls(32676)
main_line = '%s[CR]%s[CR]%s'

class Sources():
	def __init__(self):
		self.params = {}
		self.clear_properties, self.filters_ignored, self.active_folders = True, False, False
		self.threads, self.providers, self.sources, self.internal_scraper_names = [], [], [], []
		self.prescrape_scrapers, self.prescrape_threads, self.prescrape_sources = [], [], []
		self.remove_scrapers = ['external']# needs to be mutable so leave as list.
		self.exclude_list = ['furk', 'easynews', 'ororo', 'filepursuit', 'library', 'gdrive']# needs to be mutable so leave as list.
		self.sourcesTotal = self.sources4K = self.sources1080p = self.sources720p = self.sourcesSD = 0
		self.prescrape, self.disabled_ignored = 'true', 'false'
		self.language = get_setting('meta_language')
		self.progress_dialog = None

	def playback_prep(self, params=None):
		if self.clear_properties: self._clear_properties()
		if params: self.params = params
		params_get = self.params.get
		self.prescrape = params_get('prescrape', self.prescrape) == 'true'
		self.background = params_get('background', 'false') == 'true'
		if self.background: hide_busy_dialog()
		else: show_busy_dialog()
		self.disabled_ignored = params_get('disabled_ignored', self.disabled_ignored) == 'true'
		self.from_library = params_get('library', 'False') == 'True'
		self.media_type = params_get('media_type')
		self.tmdb_id = params_get('tmdb_id')
		self.ep_name = params_get('ep_name')
		self.plot = params_get('plot')
		self.custom_title = params_get('custom_title', None)
		self.custom_year = params_get('custom_year', None)
		if 'autoplay' in self.params: self.autoplay = self.params.get('autoplay', 'False') == 'True'
		else: self.autoplay = auto_play(self.media_type)
		if 'season' in self.params: self.season = int(params_get('season'))
		else: self.season = ''
		if 'episode' in self.params: self.episode = int(params_get('episode'))
		else: self.episode = ''
		if 'meta' in self.params: self.meta = json.loads(params_get('meta'))
		else: self._grab_meta()
		self.active_internal_scrapers = active_internal_scrapers()
		self.active_external = 'external' in self.active_internal_scrapers
		self.provider_sort_ranks = provider_sort_ranks()
		self.sleep_time = display_sleep_time()
		self.scraper_settings = scraping_settings()
		self.include_prerelease_results = include_prerelease_results()
		self.ignore_results_filter = ignore_results_filter()
		self.ignore_scrape_filters = params_get('ignore_scrape_filters', 'false') == 'true'
		self.filter_hevc = filter_status('hevc')
		self.filter_hdr = filter_status('hdr')
		self.filter_dv = filter_status('dv')
		self.hybrid_allowed = self.filter_hdr in (0, 2)
		self.sort_function = results_sort_order()
		self.display_uncached_torrents = display_uncached_torrents()
		self.quality_filter = self._quality_filter()
		self.filter_size = get_setting('results.filter.size', '0') == 'true'
		self.include_unknown_size = get_setting('results.include.unknown.size') == 'true'
		self.include_3D_results = get_setting('include_3d_results') == 'true'
		self._update_meta()
		self._search_info()
		set_property('fen_playback_meta', json.dumps(self.meta))
		self.get_sources()

	def get_sources(self):
		results = []
		if any(x in self.active_internal_scrapers for x in default_internal_scrapers) and self.prescrape:
			self.prepare_internal_scrapers()
			results = self.collect_prescrape_results()
			if results: results = self.process_results(results)
		if not results:
			self.prescrape = False
			self.prepare_internal_scrapers()
			if self.active_external:
				self.activate_debrid_info()
				self.activate_external_providers()
			self.orig_results = self.collect_results()
			results = self.process_results(self.orig_results)
			playable_results = [i for i in results if not 'Uncached' in i.get('cache_provider', '')]
			if not playable_results: return self._process_post_results()
		self.play_source(results)

	def collect_results(self):
		self.sources.extend(self.prescrape_sources)
		threads_append = self.threads.append
		if self.active_folders: self.append_folder_scrapers(self.providers)
		self.providers.extend(internal_sources(self.active_internal_scrapers))
		if self.providers:
			for i in self.providers: threads_append(Thread(target=self.activate_providers, args=(i[0], i[1], False), name=i[2]))
			[i.start() for i in self.threads]
		if self.active_external or self.background:
			if self.active_external:
				self.external_args = (self.external_providers, self.debrid_torrent_enabled, self.debrid_hoster_enabled, self.internal_scraper_names,
										self.prescrape_sources, self.display_uncached_torrents, self.progress_dialog, self.disabled_ignored)
				self.activate_providers('external', external, False)
			if self.providers: [i.join() for i in self.threads]
		else: self.scrapers_dialog('internal')
		return self.sources

	def collect_prescrape_results(self):
		threads_append = self.prescrape_threads.append
		if self.active_folders:
			if self.autoplay or check_prescrape_sources('folders'):
				self.append_folder_scrapers(self.prescrape_scrapers)
				self.remove_scrapers.append('folders')
		self.prescrape_scrapers.extend(internal_sources(self.active_internal_scrapers, True))
		if not self.prescrape_scrapers: return []
		for i in self.prescrape_scrapers: threads_append(Thread(target=self.activate_providers, args=(i[0], i[1], True), name=i[2]))
		[i.start() for i in self.prescrape_threads]
		self.remove_scrapers.extend(i[2] for i in self.prescrape_scrapers)
		if self.background: [i.join() for i in self.prescrape_threads]
		else: self.scrapers_dialog('pre_scrape')
		return self.prescrape_sources

	def process_results(self, results):
		if self.prescrape: self.all_scrapers = self.active_internal_scrapers
		else: self.all_scrapers = list(set(self.active_internal_scrapers + self.remove_scrapers))
		if self.ignore_scrape_filters:
			self.filters_ignored = True
			results = self.sort_results(results)
			results = self._sort_first(results)
		else:
			results = self.filter_results(results)
			results = self.sort_results(results)
			results = self._special_filter(results, hevc_filter_key, self.filter_hevc)
			results = self._special_filter(results, hdr_filter_key, self.filter_hdr)
			results = self._special_filter(results, dolby_vision_filter_key, self.filter_dv)
			results = self._sort_first(results)
		return results

	def filter_results(self, results):
		results = [i for i in results if i['quality'] in self.quality_filter]
		if not self.include_3D_results: results = [i for i in results if not '3D' in i['extraInfo']]
		if self.filter_size:
			duration = self.meta['duration'] or (5400 if self.media_type == 'movie' else 2400)
			max_size = ((0.125 * (0.90 * string_to_float(get_setting('results.size.auto', '20'), '20'))) * duration)/1000
			if self.include_unknown_size: results = [i for i in results if i['scrape_provider'].startswith('folder') or i['size'] <= max_size]
			else: results = [i for i in results if i['scrape_provider'].startswith('folder') or 0.01 < i['size'] <= max_size]
		return results

	def sort_results(self, results):
		def _add_keys(item):
			provider = item['scrape_provider']
			if provider == 'external': account_type = item['debrid'].lower()
			else: account_type = provider.lower()
			item['provider_rank'] = self._get_provider_rank(account_type)
			item['quality_rank'] = self._get_quality_rank(item.get('quality', 'SD'))
		for item in results: _add_keys(item)
		results.sort(key=self.sort_function)
		if self.display_uncached_torrents: results = self._sort_uncached_torrents(results)
		return results

	def prepare_internal_scrapers(self):
		if self.active_external and len(self.active_internal_scrapers) == 1: return
		active_internal_scrapers = [i for i in self.active_internal_scrapers if not i in self.remove_scrapers]
		self.active_folders = 'folders' in active_internal_scrapers
		if self.active_folders:
			self.folder_info = self.get_folderscraper_info()
			self.internal_scraper_names = [i for i in active_internal_scrapers if not i == 'folders'] + [i[0] for i in self.folder_info]
			self.active_internal_scrapers = active_internal_scrapers
		else:
			self.folder_info = []
			self.internal_scraper_names = active_internal_scrapers[:]
			self.active_internal_scrapers = active_internal_scrapers

	def activate_providers(self, module_type, function, prescrape):
		sources = self._get_module(module_type, function).results(self.search_info)
		if not sources: return
		if prescrape: self.prescrape_sources.extend(sources)
		else: self.sources.extend(sources)

	def activate_debrid_info(self):
		self.debrid_enabled = debrid_enabled()
		self.debrid_torrent_enabled = debrid_type_enabled('torrent', self.debrid_enabled)
		self.debrid_hoster_enabled = debrid_valid_hosts(debrid_type_enabled('hoster', self.debrid_enabled))

	def activate_external_providers(self):
		if not self.debrid_torrent_enabled and not self.debrid_hoster_enabled:
			self._kill_progress_dialog()
			if len(self.active_internal_scrapers) == 1 and 'external' in self.active_internal_scrapers: notification(32854, 2000)
			self.active_external = False
		else:
			if not self.debrid_torrent_enabled: self.exclude_list.extend(scraper_names('torrents'))
			elif not self.debrid_hoster_enabled: self.exclude_list.extend(scraper_names('hosters'))
			external_providers = sources(ret_all=self.disabled_ignored)
			self.external_providers = [i for i in external_providers if not i[0] in self.exclude_list]

	def play_source(self, results):
		if self.background: return self.play_execute_background(results)
		if self.autoplay: return self.play_file(results, autoplay=True)
		return self.display_results(results)

	def append_folder_scrapers(self, current_list):
		current_list.extend(internal_folders_import(self.folder_info))

	def get_folderscraper_info(self):
		folder_info = [(get_setting('%s.display_name' % i), i) for i in folder_scrapers]
		return [i for i in folder_info if not i[0] in (None, 'None', '')]

	def scrapers_dialog(self, scrape_type):
		def _scraperDialog():
			if not self.progress_dialog: self._make_progress_dialog()
			while not self.progress_dialog.iscanceled():
				try:
					if monitor.abortRequested(): break
					remaining_providers = [x.getName() for x in _threads if x.is_alive() is True]
					self._process_internal_results()
					s4k_label, s1080_label = total_format % self.sources4K, total_format % self.sources1080p
					s720_label, ssd_label, stotal_label = total_format % self.sources720p, total_format % self.sourcesSD, total_format % self.sourcesTotal
					try:
						current_time = time.time()
						current_progress = current_time - start_time
						line2 = dialog_format % (int_dialog_hl, line2_inst, s4k_label, s1080_label, s720_label, ssd_label, stotal_label)
						line3 = remaining_format % ', '.join(remaining_providers).upper()
						percent = int((current_progress/float(timeout))*100)
						self.progress_dialog.update(main_line % (line1, line2, line3), percent)
						sleep(self.sleep_time)
						if len(remaining_providers) == 0: break
						if percent >= 100: break
					except: pass
				except: pass
		if scrape_type == 'internal': scraper_list, _threads, line1_inst, line2_inst = self.providers, self.threads, ls(32096), 'Int:'
		else: scraper_list, _threads, line1_inst, line2_inst = self.prescrape_scrapers, self.prescrape_threads, ' '.join([ls(32829), ls(32830)]), 'Pre:'
		self.internal_scrapers = self._get_active_scraper_names(scraper_list)
		if not self.internal_scrapers: return
		timeout = 25
		int_dialog_hl = get_setting('int_dialog_highlight') or 'dodgerblue'
		total_format = '[COLOR %s][B]%s[/B][/COLOR]' % (int_dialog_hl, '%s')
		line1 = '[COLOR %s][B]%s[/B][/COLOR]' % (int_dialog_hl, line1_inst)
		start_time = time.time()
		end_time = start_time + timeout
		_scraperDialog()

	def display_results(self, results):
		window_style = results_xml_style()
		action, chosen_item = open_window(('windows.sources', 'SourceResults'), 'sources_results.xml',
							window_style=window_style, window_id=results_xml_window_number(window_style), results=results,
							meta=self.meta, scraper_settings=self.scraper_settings, prescrape=self.prescrape, filters_ignored=self.filters_ignored)
		if not action: self._kill_progress_dialog()
		elif action == 'play':
			self._kill_progress_dialog()
			return self.play_file(results, chosen_item)
		elif self.prescrape and action == 'perform_full_search':
			self.prescrape, self.clear_properties = False, False
			return self.playback_prep()

	def play_execute_background(self, results):
		background_url = self.play_file(results, autoplay=True, background=True)
		set_property('fen_background_url', background_url)

	def _get_active_scraper_names(self, scraper_list):
		return [i[2] for i in scraper_list]

	def _process_post_results(self):
		if self.ignore_results_filter and self.orig_results: return self._process_ignore_filters()
		return self._no_results()

	def _process_ignore_filters(self):
		self.filters_ignored = True
		if self.autoplay:
			orig_results = self.orig_results[:]
			orig_results = [i for i in orig_results if not 'Uncached' in i.get('cache_provider', '')]
			if self.filter_size:
				duration = self.meta['duration'] or (5400 if self.media_type == 'movie' else 2400)
				min_size = 0
				max_size = ((0.125 * (0.90 * string_to_float(get_setting('results.size.auto', '20'), '20'))) * duration)/1000
				orig_results.sort(key=lambda x: x['size'])
				size_list = [i['size'] for i in orig_results]
				nearest_min_index = size_list.index(min(size_list, key=lambda x: abs(x - min_size)))
				nearest_max_index = size_list.index(min(size_list, key=lambda x: abs(x - max_size)))
				nearest_min_results = sorted(orig_results[:nearest_min_index + 1], key=lambda x: x['size'], reverse=True)[:5]
				nearest_max_results = sorted(orig_results[nearest_max_index:], key=lambda x: x['size'])[:5]
				orig_results = nearest_min_results + nearest_max_results
			include_quality = [i for i in orig_results if i['quality'] in self.quality_filter]
			exclude_quality = [i for i in orig_results if not i['quality'] in self.quality_filter]
			results = include_quality + exclude_quality
		else:
			results = self.sort_results(self.orig_results)
			results = self._sort_first(results)
		if self.autoplay: notification(32686)
		return self.play_source(results)

	def _no_results(self):
		hide_busy_dialog()
		if self.background: return notification('%s %s' % (ls(32801), ls(32760)), 5000)
		notification(32760, 2000)

	def _update_meta(self):
		if self.from_library: self.meta.update({'plot': self.plot if self.plot else self.meta.get('plot'), 'from_library': self.from_library, 'ep_name': self.ep_name})
		self.meta.update({'media_type': self.media_type, 'season': self.season, 'episode': self.episode, 'background': self.background})
		if self.custom_title: self.meta['custom_title'] = self.custom_title
		if self.custom_year: self.meta['custom_year'] = self.custom_year

	def _search_info(self):
		title = self._get_search_title(self.meta)
		year = self._get_search_year(self.meta)
		ep_name = self._get_ep_name()
		aliases = self._make_alias_dict(title)
		expiry_times = get_cache_expiry(self.media_type, self.meta, self.season)
		self.search_info = {'media_type': self.media_type, 'title': title, 'year': year, 'tmdb_id': self.tmdb_id, 'imdb_id': self.meta.get('imdb_id'), 'aliases': aliases,
							'season': self.season, 'episode': self.episode, 'tvdb_id': self.meta.get('tvdb_id'), 'ep_name': ep_name, 'expiry_times': expiry_times,
							'total_seasons': self.meta.get('total_seasons', 1)}

	def _get_search_title(self, meta):
		if 'custom_title' in meta: search_title = meta['custom_title']
		else:
			if self.language == 'en': search_title = meta['title']
			else:
				search_title = None
				if 'english_title' in meta: search_title = meta['english_title']
				else:
					try:
						media_type = 'movie' if self.media_type == 'movie' else 'tv'
						meta_user_info = metadata_user_info()
						english_title = metadata.english_translation(media_type, meta['tmdb_id'], meta_user_info)
						if english_title: search_title = english_title
						else: search_title = meta['original_title']
					except: pass
				if not search_title: search_title = meta['original_title']
			if '(' in search_title: search_title = search_title.split('(')[0]
			if '/' in search_title: search_title = search_title.replace('/', ' ')
		return search_title

	def _get_search_year(self, meta):
		if 'custom_year' in meta: year = meta['custom_year']
		else:
			year = meta.get('year')
			if self.active_external and get_setting('search.enable.yearcheck', 'false') == 'true':
				from apis.imdb_api import imdb_movie_year
				try: year = str(imdb_movie_year(meta.get('imdb_id')))
				except: pass
		return year

	def _get_ep_name(self):
		ep_name = None
		if self.media_type == 'episode':
			ep_name = self.meta.get('ep_name')
			try: ep_name = safe_string(remove_accents(ep_name))
			except: ep_name = safe_string(ep_name)
		return ep_name

	def _make_alias_dict(self, title):
		original_title = self.meta['original_title']
		alternative_titles = self.meta.get('alternative_titles', [])
		if not alternative_titles: return []
		country_codes = set([i.replace('GB', 'UK') for i in self.meta.get('country_codes', [])])
		aliases = [{'title': i, 'country': ''} for i in alternative_titles]
		if original_title not in aliases: aliases.append({'title': original_title, 'country': ''})
		if country_codes: aliases.extend([{'title': '%s %s' % (title, i), 'country': ''} for i in country_codes])
		return aliases

	def _process_internal_results(self):
		for i in self.internal_scrapers:
			win_property = get_property('%s.internal_results' % i)
			if win_property in ('checked', '', None): continue
			try: sources = json.loads(win_property)
			except: continue
			set_property('%s.internal_results' % i, 'checked')
			self._sources_quality_count(sources)
	
	def _sources_quality_count(self, sources):
		for i in sources:
			quality = i['quality']
			if quality == '4K': self.sources4K += 1
			elif quality in ('1440p', '1080p'): self.sources1080p += 1
			elif quality in ('720p', 'HD'): self.sources720p += 1
			else: self.sourcesSD += 1
			self.sourcesTotal += 1

	def _quality_filter(self):
		setting = 'results_quality_%s' % self.media_type if not self.autoplay else 'autoplay_quality_%s' % self.media_type
		filter_list = quality_filter(setting)
		if self.include_prerelease_results and 'SD' in filter_list: filter_list += ['SCR', 'CAM', 'TELE']
		return filter_list

	def _get_quality_rank(self, quality):
		return quality_ranks[quality]

	def _get_provider_rank(self, account_type):
		return self.provider_sort_ranks[account_type] or 11

	def _sort_first(self, results):
		try:
			sort_first_scrapers = []
			if 'folders' in self.all_scrapers and sort_to_top('folders'): sort_first_scrapers.append('folders')
			sort_first_scrapers.extend([i for i in self.all_scrapers if i in cloud_scrapers and sort_to_top(i)])
			if not sort_first_scrapers: return results
			sort_first = [i for i in results if i['scrape_provider'] in sort_first_scrapers]
			sort_first.sort(key=lambda k: (self._sort_folder_to_top(k['scrape_provider']), k['quality_rank']))
			sort_last = [i for i in results if not i in sort_first]
			results = sort_first + sort_last
		except: pass
		return results

	def _sort_folder_to_top(self, provider):
		if provider == 'folders': return 0
		else: return 1

	def _sort_uncached_torrents(self, results):
		uncached = [i for i in results if 'Uncached' in i.get('cache_provider', '')]
		cached = [i for i in results if not i in uncached]
		return cached + uncached

	def _special_filter(self, results, key, enable_setting):
		if enable_setting == 1:
			if key == dolby_vision_filter_key and self.hybrid_allowed:
				results = [i for i in results if all(x in i['extraInfo'] for x in (key, hdr_filter_key)) or not key in i['extraInfo']]
			else: results = [i for i in results if not key in i['extraInfo']]
		elif enable_setting == 2 and self.autoplay:
			priority_list = [i for i in results if key in i['extraInfo']]
			remainder_list = [i for i in results if not i in priority_list]
			results = priority_list + remainder_list
		return results

	def _grab_meta(self):
		meta_user_info = metadata_user_info()
		if self.media_type == 'movie':
			self.meta = metadata.movie_meta('tmdb_id', self.tmdb_id, meta_user_info, get_datetime())
		else:
			self.meta = metadata.tvshow_meta('tmdb_id', self.tmdb_id, meta_user_info, get_datetime())
			episodes_data = metadata.season_episodes_meta(self.season, self.meta, meta_user_info)
			try:
				episode_data = [i for i in episodes_data if i['episode'] == int(self.episode)][0]
				self.meta.update({'media_type': 'episode', 'season': episode_data['season'], 'episode': episode_data['episode'], 'premiered': episode_data['premiered'],
								'ep_name': episode_data['title'], 'plot': episode_data['plot']})
			except: pass

	def _get_module(self, module_type, function):
		if module_type == 'external': module = function.source(*self.external_args)
		elif module_type == 'folders': module = function[0](*function[1])
		else: module = function()
		return module

	def _clear_properties(self):
		for item in default_internal_scrapers: clear_property('%s.internal_results' % item)
		for item in self.get_folderscraper_info(): clear_property('%s.internal_results' % item[0])

	def _make_progress_dialog(self):
		self.progress_dialog = create_window(('windows.yes_no_progress_media', 'YesNoProgressMedia'), 'yes_no_progress_media.xml', meta=self.meta)
		Thread(target=self.progress_dialog.run).start()

	def _kill_progress_dialog(self):
		try: self.progress_dialog.close()
		except: close_all_dialog()
		try: del self.progress_dialog
		except: pass
		self.progress_dialog = None

	def furkPacks(self, name, file_id, highlight=None, download=False):
		from apis.furk_api import FurkAPI
		show_busy_dialog()
		t_files = FurkAPI().t_files(file_id)
		t_files = [i for i in t_files if 'video' in i['ct'] and 'bitrate' in i]
		t_files.sort(key=lambda k: k['name'].lower())
		hide_busy_dialog()
		if download: return t_files
		default_furk_icon = translate_path('special://home/addons/script.tikiart/resources/media/furk.png')
		list_items = [{'line1': '%.2f GB | %s' % (float(item['size'])/1073741824, clean_file_name(item['name']).upper()), 'icon': default_furk_icon} for item in t_files]
		kwargs = {'items': json.dumps(list_items), 'heading': name, 'highlight': highlight, 'enumerate': 'true', 'multi_choice': 'false', 'multi_line': 'false'}
		chosen_result = select_dialog(t_files, **kwargs)
		if chosen_result is None: return None
		link = chosen_result['url_dl']
		name = chosen_result['name']
		return FenPlayer().run(link, 'video')

	def debridPacks(self, debrid_provider, name, magnet_url, info_hash, highlight=None, download=False):
		if debrid_provider == 'Real-Debrid':
			from apis.real_debrid_api import RealDebridAPI as debrid_function
			icon = 'realdebrid.png'
		elif debrid_provider == 'Premiumize.me':
			from apis.premiumize_api import PremiumizeAPI as debrid_function
			icon = 'premiumize.png'
		elif debrid_provider == 'AllDebrid':
			from apis.alldebrid_api import AllDebridAPI as debrid_function
			icon = 'alldebrid.png'
		show_busy_dialog()
		try: debrid_files = debrid_function().display_magnet_pack(magnet_url, info_hash)
		except: debrid_files = None
		hide_busy_dialog()
		if not debrid_files: return notification(32574)
		debrid_files.sort(key=lambda k: k['filename'].lower())
		if download: return debrid_files, debrid_function
		default_debrid_icon = translate_path('special://home/addons/script.tikiart/resources/media/%s' % icon)
		list_items = [{'line1': '%.2f GB | %s' % (float(item['size'])/1073741824, clean_file_name(item['filename']).upper()), 'icon': default_debrid_icon} \
							for item in debrid_files]
		kwargs = {'items': json.dumps(list_items), 'heading': name, 'highlight': highlight, 'enumerate': 'true', 'multi_choice': 'false', 'multi_line': 'false'}
		chosen_result = select_dialog(debrid_files, **kwargs)
		if chosen_result is None: return None
		url_dl = chosen_result['link']
		if debrid_provider in ('Real-Debrid', 'AllDebrid'):
			link = debrid_function().unrestrict_link(url_dl)
		elif debrid_provider == 'Premiumize.me':
			link = debrid_function().add_headers_to_url(url_dl)
		name = chosen_result['filename']
		return FenPlayer().run(link, 'video')

	def play_file(self, results, source={}, autoplay=False, background=False):
		def _resolve_dialog():
			self.url = None
			for count, item in enumerate(items, 1):
				try:
					self.caching_confirmed = False
					if not background:
						try:
							if self.progress_dialog.iscanceled(): break
							if monitor.abortRequested(): break
							name = item['name'].replace('.', ' ').replace('-', ' ').upper()
							percent = int(count/float(total_items)*100)
							self.progress_dialog.update(main_line % ('', name, ''), percent)
						except: pass
					url = self.resolve_sources(item, self.meta)
					if url == 'uncached':
						url = _uncached_confirm(item)
						if url is None: return
					if url:
						self.url = url
						break
				except: pass
			self._kill_progress_dialog()
		def _uncached_confirm(item):
			if not confirm_dialog(text=ls(32831) % item['debrid'].upper()): return None
			else:
				self.caching_confirmed = True
				return item
		try:
			self._kill_progress_dialog()
			if autoplay:
				items = [i for i in results if not 'Uncached' in i.get('cache_provider', '')]
				if self.filters_ignored: notification(32686)
			else:
				results = [i for i in results if not 'Uncached' in i.get('cache_provider', '') or i == source]
				source_index = results.index(source)
				leading_index = max(source_index-20, 0)
				items_prev = results[leading_index:source_index]
				trailing_index = 41 - len(items_prev)
				items_next = results[source_index+1:source_index+trailing_index]
				items = [source] + items_next + items_prev
			total_items = len(items)
			if not background: self._make_progress_dialog()
			_resolve_dialog()
			if background: return self.url
			if self.caching_confirmed: return self.resolve_sources(self.url, self.meta, cache_item=True)
			return FenPlayer().run(self.url)
		except: pass

	def resolve_sources(self, item, meta, cache_item=False):
		try:
			if 'cache_provider' in item:
				cache_provider = item['cache_provider']
				if meta['media_type'] == 'episode': title, season, episode = meta['ep_name'], meta.get('season'), meta.get('episode')
				else: title, season, episode = self._get_search_title(meta), None, None
				if cache_provider in ('Real-Debrid', 'Premiumize.me', 'AllDebrid'):
					url = resolve_cached_torrents(cache_provider, item['url'], item['hash'], title, season, episode)
					return url
				if 'Uncached' in cache_provider:
					if cache_item:
						if not 'package' in item: title, season, episode  = None, None, None
						url = resolve_uncached_torrents(item['debrid'], item['url'], item['hash'], title, season, episode)
						if not url: return None
						if url == 'cache_pack_success': return
						return FenPlayer().run(url)
					else:
						url = 'uncached'
						return url
					return None
			if item.get('scrape_provider', None) in default_internal_scrapers:
				url = resolve_internal_sources(item['scrape_provider'], item['id'], item['url_dl'], item.get('direct_debrid_link', False))
				return url
			if item.get('debrid') in ('Real-Debrid', 'Premiumize.me', 'AllDebrid') and not item['source'].lower() == 'torrent':
				url = resolve_debrid(item['debrid'], item['provider'], item['url'])
				if url is not None: return url
				else: return None
			else:
				url = item['url']
				return url
		except: return
