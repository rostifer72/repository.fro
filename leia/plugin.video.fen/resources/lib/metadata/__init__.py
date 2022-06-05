# -*- coding: utf-8 -*-

import xbmc
from metadata import tmdb
from metadata import fanarttv
from caches.metacache import metacache
from modules.nav_utils import translate_path
from modules.utils import try_parse_int, safe_string, remove_accents, to_utf8
# from modules.utils import logger

backup_resolutions = {'poster': 'w780', 'fanart': 'w1280', 'still': 'original', 'profile': 'h632'}

def movie_meta(id_type, media_id, user_info):
	from datetime import timedelta
	meta = None
	tmdb_api = user_info['tmdb_api']
	image_resolution = user_info.get('image_resolution', backup_resolutions)
	language = user_info['language']
	extra_fanart_enabled = user_info['extra_fanart_enabled']
	fanart_client_key = user_info['fanart_client_key']
	hours = 4368
	def tmdb_meta(language):
		data = tmdb.tmdbMovies
		result = tmdb.tmdbMoviesExternalID
		return data(media_id, language, tmdb_api) if id_type == 'tmdb_id' else data(result(id_type, media_id, tmdb_api)['id'], language, tmdb_api)
	def fanarttv_meta(fanart_id):
		if extra_fanart_enabled: return fanarttv.get('movies', language, fanart_id, fanart_client_key)
		else: return None
	def cached_meta():
		return metacache.get('movie', id_type, media_id)
	def set_cache_meta():
		metacache.set('movie', meta, timedelta(hours=hours))
	def delete_cache_meta():
		metacache.delete('movie', 'tmdb_id', meta['tmdb_id'])
	def check_tmdb_data(data):
		if language != 'en' and data['overview'] == '':
			overview = tmdb_meta('en')['overview']
			data['overview'] = overview
		return data
	meta = cached_meta()
	if meta and extra_fanart_enabled and not meta.get('fanart_added', False):
		try:
			meta = fanarttv.add('movies', language, meta['tmdb_id'], meta, fanart_client_key)
			delete_cache_meta()
			set_cache_meta()
		except: pass
	if not meta:
		try:
			fetch_fanart_art = False
			data = check_tmdb_data(tmdb_meta(language))
			if not data.get('poster_path', None):
				if extra_fanart_enabled: fetch_fanart_art = True
			fanarttv_data = fanarttv_meta(data['id'])
			if fetch_fanart_art:
				data['external_poster'] = fanarttv_data.get('fanarttv_poster', None)
				data['external_fanart'] = fanarttv_data.get('fanarttv_fanart', None)
			data['image_resolution'] = image_resolution
			meta = build_movie_meta(data, fanarttv_data=fanarttv_data)
			set_cache_meta()
		except: pass
	return meta

def tvshow_meta(id_type, media_id, user_info):
	from datetime import timedelta
	meta = None
	tmdb_api = user_info['tmdb_api']
	image_resolution = user_info.get('image_resolution', backup_resolutions)
	language = user_info['language']
	extra_fanart_enabled = user_info['extra_fanart_enabled']
	fanart_client_key = user_info['fanart_client_key']
	def tmdb_meta():
		data = tmdb.tmdbTVShows
		result = tmdb.tmdbTVShowsExternalID
		return data(media_id, language, tmdb_api) if id_type == 'tmdb_id' else data(result(id_type, media_id, tmdb_api)['id'], language, tmdb_api)
	def fanarttv_meta(fanart_id):
		if extra_fanart_enabled: return fanarttv.get('tv', language, fanart_id, fanart_client_key)
		else: return None
	def cached_meta():
		return metacache.get('tvshow', id_type, media_id)
	def set_cache_meta():
		metacache.set('tvshow', meta, timedelta(hours=hours))
	def delete_cache_meta():
		metacache.delete('tvshow', 'tmdb_id', meta['tmdb_id'])
	meta = cached_meta()
	if meta and extra_fanart_enabled and not meta.get('fanart_added', False):
		try:
			meta = fanarttv.add('tv', language, meta['tvdb_id'], meta, fanart_client_key)
			delete_cache_meta()
			set_cache_meta()
		except: pass
	if not meta:
		try:
			fanarttv_data = None
			data = tmdb_meta()
			data['image_resolution'] = image_resolution
			if data['status'].lower() in ('ended', 'canceled'): hours = 4368
			else: hours = 96
			tvdb_id = data['external_ids']['tvdb_id']
			fanarttv_data = fanarttv_meta(tvdb_id)
			if not data['poster_path']:
				if fanarttv_data:
					if fanarttv_data['fanarttv_poster'] != '': data['external_poster'] = fanarttv_data['fanarttv_poster']
			if not data['backdrop_path']:
				if fanarttv_data:
					if fanarttv_data['fanarttv_fanart'] != '': data['external_fanart'] = fanarttv_data['fanarttv_fanart']
			meta = build_tvshow_meta(data, fanarttv_data=fanarttv_data)
			set_cache_meta()
		except: pass
	return meta

def season_episodes_meta(season, meta, user_info):
	data = None
	episodes_data = None
	media_id = meta['tmdb_id']
	string = '%s_%s' % (media_id, season)
	data = metacache.get('season', 'tmdb_id', string)
	if data: return data
	from datetime import timedelta
	try:
		if meta['extra_info']['status'].lower() in ('ended', 'canceled'): hours = 4368
		elif meta['total_seasons'] > int(season): hours = 4368
		else: hours = 96
		image_resolution = user_info.get('image_resolution', backup_resolutions)
		data = tmdb.tmdbSeasonEpisodes(media_id, season, user_info['language'], user_info['tmdb_api'])['episodes']
		episodes_data = build_episodes_meta(data, image_resolution['still'])
		metacache.set('season', episodes_data, timedelta(hours=hours), string)
	except: pass
	return episodes_data

def all_episodes_meta(meta, user_info):
	def _get_tmdb_episodes(season):
		try:
			episodes = season_episodes_meta(season, meta, user_info)
			all_episodes.extend(episodes)
		except: pass
	all_episodes = []
	threads = []
	try:
		from datetime import timedelta
		from threading import Thread
		season_numbers = [str(i['season_number']) for i in meta['season_data']]
		for i in season_numbers: threads.append(Thread(target=_get_tmdb_episodes, args=(int(i),)))
		[i.start() for i in threads]
		[i.join() for i in threads]
	except: pass
	return all_episodes

def build_movie_meta(data, fanarttv_data=None):
	meta = {}
	writer = []
	meta['cast'] = []
	meta['studio'] = []
	meta['all_trailers'] = []
	meta['extra_info'] = {}
	meta['mpaa'] = ''
	meta['country'] = []
	meta['country_codes'] = []
	meta['director'] = ''
	meta['writer'] = ''
	meta['trailer'] = ''
	meta['tmdb_id'] = data.get('id', '')
	meta['imdb_id'] = data.get('imdb_id', '')
	meta['imdbnumber'] = meta['imdb_id']
	meta['tvdb_id'] = 'None'
	if data.get('poster_path'):
		meta['poster'] = "https://image.tmdb.org/t/p/%s%s" % (data['image_resolution']['poster'], data['poster_path'])
	elif data.get('external_poster'):
		meta['poster'] = data['external_poster']
	else:
		meta['poster'] = translate_path('special://home/addons/script.tikiart/resources/default_images/meta_blank_poster.png')
	if data.get('backdrop_path'):
		meta['fanart'] = "https://image.tmdb.org/t/p/%s%s" % (data['image_resolution']['fanart'], data['backdrop_path'])
	elif data.get('external_fanart'):
		meta['fanart'] = data['external_fanart']
	else:
		meta['fanart'] = translate_path('special://home/addons/script.tikiart/resources/default_images/meta_blank_fanart.png')
	if fanarttv_data:
		meta['banner'] = fanarttv_data['banner']
		meta['clearart'] = fanarttv_data['clearart']
		meta['clearlogo'] = fanarttv_data['clearlogo']
		meta['landscape'] = fanarttv_data['landscape']
		meta['discart'] = fanarttv_data['discart']
		meta['fanart_added'] = True
	else:
		meta['banner'] = translate_path('special://home/addons/script.tikiart/resources/default_images/meta_blank_banner.png')
		meta['clearart'] = ''
		meta['clearlogo'] = ''
		meta['landscape'] = ''
		meta['discart'] = ''
		meta['fanart_added'] = False
	meta['rating'] = data.get('vote_average', '')
	try: meta['genre'] = ', '.join([item['name'] for item in data['genres']])
	except: meta['genre'] == []
	meta['plot'] = to_utf8(data.get('overview', ''))
	meta['tagline'] = to_utf8(data.get('tagline', ''))
	meta['votes'] = data.get('vote_count', '')
	meta['mediatype'] = 'movie'
	meta['title'] = to_utf8(data['title'])
	try: meta['search_title'] = to_utf8(safe_string(remove_accents(data['title'])))
	except: meta['search_title'] = to_utf8(safe_string(data['title']))
	try: meta['original_title'] = to_utf8(safe_string(remove_accents(data['original_title'])))
	except: meta['original_title'] = to_utf8(safe_string(data['original_title']))
	try: meta['year'] = try_parse_int(data['release_date'].split('-')[0])
	except: meta['year'] = ''
	meta['duration'] = int(data.get('runtime', '90') * 60)
	if data.get('production_companies'): meta['studio'] = [item['name'] for item in data['production_companies']][0]
	meta['premiered'] = data.get('release_date', '')
	meta['rootname'] = '%s (%s)' % (meta['search_title'], meta['year'])
	if 'production_countries' in data:
		meta['country'] = [i['name'] for i in data['production_countries']]
		meta['country_codes'] = [i['iso_3166_1'] for i in data['production_countries']]
	if 'release_dates' in data:
		for rel_info in data['release_dates']['results']:
			if rel_info['iso_3166_1'] == 'US':
				for cert in rel_info['release_dates']:
					if cert['certification']:
						meta['mpaa'] = cert['certification']
						break
	if 'credits' in data:
		if 'cast' in data['credits']:
			for cast_member in data['credits']['cast']:
				cast_thumb = ''
				if cast_member['profile_path']:
					cast_thumb = 'https://image.tmdb.org/t/p/%s%s' % (data['image_resolution']['profile'], cast_member['profile_path'])
				meta['cast'].append({'name': cast_member['name'], 'role': cast_member['character'], 'thumbnail': cast_thumb})
		if 'crew' in data['credits']:
			for crew_member in data['credits']['crew']:
				cast_thumb = ''
				if crew_member['profile_path']:
					cast_thumb = 'https://image.tmdb.org/t/p/%s%s' % (data['image_resolution']['profile'], crew_member['profile_path'])
				if crew_member['job'] in ['Author', 'Writer', 'Screenplay', 'Characters']:
					writer.append(crew_member['name'])
				if crew_member['job'] == 'Director':
					meta['director'] = crew_member['name']
			if writer: meta['writer'] = ', '.join(writer)
	if 'alternative_titles' in data:
		alternatives = data['alternative_titles']['titles']
		meta['alternative_titles'] = [i['title'] for i in alternatives if i['iso_3166_1']  in ('US', 'GB', 'UK', '')]
	if 'videos' in data:
		meta['all_trailers'] = data['videos']['results']
		for video in data['videos']['results']:
			if video['site'] == 'YouTube' and video['type'] == 'Trailer' or video['type'] == 'Teaser':
				meta['trailer'] = 'plugin://plugin.video.youtube/play/?video_id=%s' % video['key']
				break
	if data.get('belongs_to_collection', False):
		meta['extra_info']['collection_name'] = data['belongs_to_collection']['name']
		meta['extra_info']['collection_id'] = data['belongs_to_collection']['id']
	else:
		meta['extra_info']['collection_name'] = None
		meta['extra_info']['collection_id'] = None
	meta['extra_info']['budget'] = '${:,}'.format(data['budget'])
	meta['extra_info']['revenue'] = '${:,}'.format(data['revenue'])
	meta['extra_info']['homepage'] = data.get('homepage', 'N/A')
	meta['extra_info']['status'] = data.get('status', 'N/A')
	return meta

def build_tvshow_meta(data, fanarttv_data=None):
	meta = {}
	writer = []
	creator = []
	meta['cast'] = []
	meta['studio'] = []
	meta['all_trailers'] = []
	meta['extra_info'] = {}
	meta['mpaa'] = ''
	meta['country'] = []
	meta['country_codes'] = []
	meta['director'] = ''
	meta['writer'] = ''
	meta['trailer'] = ''
	meta['tmdb_id'] = data['id'] if 'id' in data else ''
	meta['imdb_id'] = data['external_ids'].get('imdb_id', '')
	meta['imdbnumber'] = meta['imdb_id']
	meta['tvdb_id'] = data['external_ids'].get('tvdb_id', 'None')
	if data.get('poster_path'):
		meta['poster'] = "https://image.tmdb.org/t/p/%s%s" % (data['image_resolution']['poster'], data['poster_path'])
	elif data.get('external_poster'):
		meta['poster'] = data['external_poster']
	else:
		meta['poster'] = translate_path('special://home/addons/script.tikiart/resources/default_images/meta_blank_poster.png')
	if data.get('backdrop_path'):
		meta['fanart'] = "https://image.tmdb.org/t/p/%s%s" % (data['image_resolution']['fanart'], data['backdrop_path'])
	elif data.get('external_fanart'):
		meta['fanart'] = data['external_fanart']
	else:
		meta['fanart'] = translate_path('special://home/addons/script.tikiart/resources/default_images/meta_blank_fanart.png')
	if fanarttv_data:
		meta['banner'] = fanarttv_data['banner']
		meta['clearart'] = fanarttv_data['clearart']
		meta['clearlogo'] = fanarttv_data['clearlogo']
		meta['landscape'] = fanarttv_data['landscape']
		meta['discart'] = fanarttv_data['discart']
		meta['fanart_added'] = True
	else:
		meta['banner'] = translate_path('special://home/addons/script.tikiart/resources/default_images/meta_blank_banner.png')
		meta['clearart'] = ''
		meta['clearlogo'] = ''
		meta['landscape'] = ''
		meta['discart'] = ''
		meta['fanart_added'] = False
	meta['rating'] = data.get('vote_average', '')
	try: meta['genre'] = ', '.join([item['name'] for item in data['genres']])
	except: meta['genre'] == []
	meta['plot'] = to_utf8(data.get('overview', ''))
	meta['tagline'] = to_utf8(data.get('tagline', ''))
	meta['votes'] = data.get('vote_count', '')
	meta['mediatype'] = 'tvshow'
	meta['title'] = to_utf8(data['name'])
	try: meta['search_title'] = to_utf8(safe_string(remove_accents(data['name'])))
	except: meta['search_title'] = to_utf8(safe_string(data['name']))
	try: meta['original_title'] = to_utf8(safe_string(remove_accents(data['original_name'])))
	except: meta['original_title'] = to_utf8(safe_string(data['original_name']))
	meta['tvshowtitle'] = meta['title']
	try: meta['year'] = try_parse_int(data['first_air_date'].split('-')[0])
	except: meta['year'] = ''
	meta['premiered'] = data['first_air_date']
	meta['season_data'] = data['seasons']
	meta['total_episodes'] = data['number_of_episodes']
	meta['total_seasons'] = data['number_of_seasons']
	try: meta['duration'] = min(data['episode_run_time']) * 60
	except: meta['duration'] = 30 * 60
	if data.get('networks'):
		try: meta['studio'] = [item['name'] for item in data['networks']][0]
		except: meta['studio'] = ''
	meta['rootname'] = '%s (%s)' % (meta['search_title'], meta['year'])
	if 'production_countries' in data:
		meta['country'] = [i['name'] for i in data['production_countries']]
		meta['country_codes'] = [i['iso_3166_1'] for i in data['production_countries']]
	if 'content_ratings' in data:
		for rat_info in data['content_ratings']['results']:
			if rat_info['iso_3166_1'] == 'US':
				meta['mpaa'] = rat_info['rating']
	if 'release_dates' in data:
		for rel_info in data['release_dates']['results']:
			if rel_info['iso_3166_1'] == 'US':
				meta['mpaa'] = rel_info['release_dates'][0]['certification']
	if 'credits' in data:
		if 'cast' in data['credits']:
			for cast_member in data['credits']['cast']:
				cast_thumb = ''
				if cast_member['profile_path']:
					cast_thumb = 'https://image.tmdb.org/t/p/%s%s' % (data['image_resolution']['profile'], cast_member['profile_path'])
				meta['cast'].append({'name': cast_member['name'], 'role': cast_member['character'], 'thumbnail': cast_thumb})
		if 'crew' in data['credits']:
			for crew_member in data['credits']['crew']:
				cast_thumb = ''
				if crew_member['profile_path']:
					cast_thumb = 'https://image.tmdb.org/t/p/%s%s' % (data['image_resolution']['profile'], crew_member['profile_path'])
				if crew_member['job'] in ['Author', 'Writer', 'Screenplay', 'Characters']:
					writer.append(crew_member['name'])
				if crew_member['job'] == 'Director':
					meta['director'] = crew_member['name']
			if writer: meta['writer'] = ', '.join(writer)
	if 'alternative_titles' in data:
		alternatives = data['alternative_titles']['results']
		meta['alternative_titles'] = [i['title'] for i in alternatives if i['iso_3166_1'] in ('US', 'GB', 'UK', '')]
	if 'videos' in data:
		meta['all_trailers'] = data['videos']['results']
		for video in data['videos']['results']:
			if video['site'] == 'YouTube' and video['type'] == 'Trailer' or video['type'] == 'Teaser':
				meta['trailer'] = 'plugin://plugin.video.youtube/play/?video_id=%s' % video['key']
				break
	if data.get('created_by', False):
		for person in data['created_by']:
			creator.append(person['name'])
		if creator: meta['extra_info']['created_by'] = ', '.join(creator)
	else: meta['extra_info']['created_by'] = 'N/A'
	if data.get('next_episode_to_air', False):
		next_ep = data['next_episode_to_air']
		meta['extra_info']['next_episode_to_air'] = '[%s] S%.2dE%.2d - %s' % \
					(next_ep['air_date'], next_ep['season_number'], next_ep['episode_number'], next_ep['name'])
	else: meta['extra_info']['next_episode_to_air'] = 'N/A'
	if data.get('last_episode_to_air', False):
		last_ep = data['last_episode_to_air']
		meta['extra_info']['last_episode_to_air'] = '[%s] S%.2dE%.2d - %s' % \
					(last_ep['air_date'], last_ep['season_number'], last_ep['episode_number'], last_ep['name'])
	else: meta['extra_info']['last_episode_to_air'] = 'N/A'
	meta['extra_info']['type'] = data.get('type', 'N/A')
	meta['extra_info']['status'] = data.get('status', 'N/A')
	meta['extra_info']['homepage'] = data.get('homepage', 'N/A')
	return meta

def build_episodes_meta(data, image_resolution):
	meta = []
	for episode in data:
		episode_info = {}
		writer = []
		episode_info['writer'] = ''
		episode_info['director'] = ''
		if 'crew' in episode:
			for crew_member in episode['crew']:
				if crew_member['job'] in ['Author', 'Writer', 'Screenplay', 'Characters']:
					writer.append(crew_member['name'])
				if crew_member['job'] == 'Director':
					episode_info['director'] = crew_member['name']
			if writer: episode_info['writer'] = ', '.join(writer)
		episode_info['mediatype'] = 'episode'
		episode_info['title'] = episode['name']
		episode_info['plot'] = episode['overview']
		episode_info['premiered'] = episode['air_date']
		episode_info['season'] = episode['season_number']
		episode_info['episode'] = episode['episode_number']
		if episode.get('still_path', None) is not None:
			episode_info['thumb'] = 'https://image.tmdb.org/t/p/%s%s' % (image_resolution, episode['still_path'])
		else: episode_info['thumb'] = None
		episode_info['rating'] = episode['vote_average']
		episode_info['votes'] = episode['vote_count']
		meta.append(episode_info)
	return meta

def movie_meta_external_id(external_source, external_id):
	return tmdb.tmdbMoviesExternalID(external_source, external_id)

def tvshow_meta_external_id(external_source, external_id):
	return tmdb.tmdbTVShowsExternalID(external_source, external_id)

def delete_cache_item(db_type, id_type, media_id):
	return metacache.delete(db_type, id_type, media_id)

def delete_all_seasons_memory_cache(media_id):
	return metacache.delete_all_seasons_memory_cache(media_id)

def retrieve_user_info():
	import xbmcgui
	from modules.settings import user_info
	xbmcgui.Window(10000).setProperty('fen_fanart_error', 'true')
	return user_info()

def check_meta_database():
	metacache.check_database()

def delete_meta_cache(silent=False):
	from modules.utils import local_string as ls
	try:
		if not silent:
			import xbmcgui
			if not xbmcgui.Dialog().yesno('Fen', ls(32580)): return False
		metacache.delete_all()
		return True
	except:
		return False
