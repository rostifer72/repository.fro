# -*- coding: utf-8 -*-

import xbmcgui, xbmcaddon
import requests
from caches.metacache import cache_function
# from modules.utils import logger

# Code snippets from nixgates. Thankyou.

base_url = "http://webservice.fanart.tv/v3/%s/%s"
api_key = "a7ad21743fd710fccb738232f2fbdcfc"
window = xbmcgui.Window(10000)

def get(db_type, language, remote_id, client_key):
	def error_notification(line):
		if window.getProperty('fen_fanart_error') == 'true': return
		from modules.nav_utils import notification
		window.setProperty('fen_fanart_error', 'true')
		notification(line, 3000)
		notification('Consider disabling fanart until issue resolves.', 6000)
	def request_art(dummy):
		try:
			art = requests.get(query, headers=headers, timeout=15.0)
		except requests.exceptions.Timeout as e:
			error_notification('Fanart.tv response timeout error')
			return None
		status = art.status_code
		if not status in (200, 404):
			error_notification('Fanart.tv response error: [B]%s[/B]' % str(status))
			return None
		art = art.json()
		return art
	def parse_art(art):
		if art is None: return ''
		try:
			result = [(x['url'], x['likes']) for x in art if x.get('lang') == language]
			if not result and language != 'en': result = [(x['url'], x['likes']) for x in art if x.get('lang') == 'en']
			if not result: result = [(x['url'], x['likes']) for x in art if any(value == x.get('lang') for value in ['00', ''])]
			if not result: result = [(x['url'], x['likes']) for x in art]
			result = sorted(result, key=lambda x: int(x[1]), reverse=True)
			result = [x[0] for x in result][0]
		except:
			result = ''
		if not 'http' in result: result = ''
		return result
	query = base_url % (db_type, remote_id)
	headers = {'client-key': client_key, 'api-key': api_key}
	string = "%s_%s_%s_%s" % ('fanart', db_type, language, remote_id)
	art = cache_function(request_art, string, 'dummy', 720, json=False)
	if db_type == 'movies':
		fanart_data = {'fanarttv_poster': parse_art(art.get('movieposter')),
						'fanarttv_fanart': parse_art(art.get('moviebackground')),
						'banner': parse_art(art.get('moviebanner')),
						'clearart': parse_art(art.get('movieart', []) + art.get('hdmovieclearart', [])),
						'clearlogo': parse_art(art.get('movielogo', []) + art.get('hdmovielogo', [])),
						'landscape': parse_art(art.get('moviethumb')),
						'discart': parse_art(art.get('moviedisc')),
						'fanart_added': True}
	else:
		fanart_data = {'fanarttv_poster': parse_art(art.get('tvposter')),
						'fanarttv_fanart': parse_art(art.get('showbackground')),
						'banner': parse_art(art.get('tvbanner')),
						'clearart': parse_art(art.get('clearart', []) + art.get('hdclearart', [])),
						'clearlogo': parse_art(art.get('hdtvlogo', []) + art.get('clearlogo', [])),
						'landscape': parse_art(art.get('tvthumb')),
						'discart': '',
						'fanart_added': True}
	return fanart_data

def add(db_type, language, remote_id, meta, client_key):
	try:
		fanart_data = get(db_type, language, remote_id, client_key)
		meta['fanarttv_poster'] = fanart_data['fanarttv_poster']
		meta['fanarttv_fanart'] = fanart_data['fanarttv_fanart']
		meta['banner'] = fanart_data['banner']
		meta['clearart'] = fanart_data['clearart']
		meta['clearlogo'] = fanart_data['clearlogo']
		meta['landscape'] = fanart_data['landscape']
		meta['discart'] = fanart_data['discart']
		meta['fanart_added'] = fanart_data['fanart_added']
	except: pass
	return meta

