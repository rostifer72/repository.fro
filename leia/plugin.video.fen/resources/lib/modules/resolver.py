# -*- coding: utf-8 -*-
# from modules.utils import logger

def resolve_cached_torrents(debrid_provider, item_url, _hash, season, episode, ep_title):
	from modules.settings import store_resolved_torrent_to_cloud
	url = None
	if debrid_provider == 'Real-Debrid':
		from apis.real_debrid_api import RealDebridAPI as debrid_function
	elif debrid_provider == 'Premiumize.me':
		from apis.premiumize_api import PremiumizeAPI as debrid_function
	elif debrid_provider == 'AllDebrid':
		from apis.alldebrid_api import AllDebridAPI as debrid_function
	store_to_cloud = store_resolved_torrent_to_cloud(debrid_provider)
	try: url = debrid_function().resolve_magnet(item_url, _hash, store_to_cloud, season, episode, ep_title)
	except: pass
	return url

def resolve_uncached_torrents(debrid_provider, item_url, _hash, season, episode, ep_title):
	if debrid_provider == 'Real-Debrid':
		from apis.real_debrid_api import RealDebridAPI as debrid_function
	elif debrid_provider == 'Premiumize.me':
		from apis.premiumize_api import PremiumizeAPI as debrid_function
	elif debrid_provider == 'AllDebrid':
		from apis.alldebrid_api import AllDebridAPI as debrid_function
	if season: pack = True
	else: pack = False
	success = debrid_function().add_uncached_torrent(item_url, pack)
	if success:
		if pack: return 'cache_pack_success'
		return resolve_cached_torrents(debrid_provider, item_url, _hash, season, episode, ep_title)
	else: return None

def resolve_debrid(debrid_provider, item_provider, item_url):
	from importlib import import_module
	url = None
	try:
		if debrid_provider == 'Real-Debrid':
			from apis.real_debrid_api import RealDebridAPI as debrid_function
		elif debrid_provider == 'Premiumize.me':
			from apis.premiumize_api import PremiumizeAPI as debrid_function
		elif debrid_provider == 'AllDebrid':
			from apis.alldebrid_api import AllDebridAPI as debrid_function
		url = debrid_function().unrestrict_link(item_url)
	except: pass
	return url

def resolve_internal_sources(scrape_provider, item_id, url_dl, direct_debrid_link=False):
	url = None
	try:
		if scrape_provider == 'furk':
			import xbmcgui
			import json
			from indexers.furk import t_file_browser
			from modules.source_utils import seas_ep_query_list
			meta = json.loads(xbmcgui.Window(10000).getProperty('fen_media_meta'))
			filtering_list = seas_ep_query_list(meta['season'], meta['episode']) if meta['vid_type'] == 'episode' else ''
			t_files = t_file_browser(item_id, filtering_list)
			url = t_files[0]['url_dl']
		elif scrape_provider == 'easynews':
			from indexers.easynews import resolve_easynews
			url = resolve_easynews({'url_dl': url_dl, 'play': 'false'})
		elif scrape_provider == 'rd-cloud':
			if direct_debrid_link: return url_dl
			from apis.real_debrid_api import RealDebridAPI
			url = RealDebridAPI().unrestrict_link(item_id)
		elif scrape_provider == 'pm-cloud':
			from apis.premiumize_api import PremiumizeAPI
			details = PremiumizeAPI().get_item_details(item_id)
			url = details['link']
			if url.startswith('/'): url = 'https' + url
		elif scrape_provider == 'ad-cloud':
			from apis.alldebrid_api import AllDebridAPI
			url = AllDebridAPI().unrestrict_link(item_id)
		elif scrape_provider in ('folder1', 'folder2', 'folder3', 'folder4', 'folder5'):
			if url_dl.endswith('.strm'):
				import xbmcvfs
				f = xbmcvfs.File(url_dl)
				url = f.read()
				f.close()
			else:
				url = url_dl
	except: pass
	return url
