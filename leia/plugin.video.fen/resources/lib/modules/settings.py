import xbmc, xbmcvfs
from modules.nav_utils import translate_path
from modules.settings_reader import get_setting
# from modules.utils import logger

source_window_dict = {'list': 2000, 'infolist': 2001, 'shift': 2002, 'thumb': 2003}

def addon():
	from xbmcaddon import Addon
	return Addon(id='plugin.video.fen')

def ext_addon(addon_id):
	from xbmcaddon import Addon
	return Addon(id=addon_id)

def addon_installed(addon_id):
	if xbmc.getCondVisibility('System.HasAddon(%s)' % addon_id): return True
	else: return False

def get_theme():
	theme = 'light' if get_setting('fen.theme') in ('0', '-', '') else 'heavy'
	return translate_path('special://home/addons/script.tikiart/resources/media/%s' % theme)

def skin_location():
	return translate_path('special://home/addons/script.tikiskins')

def date_offset():
	return int(get_setting('datetime.offset', '0')) + 5

def results_xml_style():
	return str(get_setting('results.xml_style', 'List Default').lower())

def results_xml_window_number(window_style=None):
	if not window_style: window_style = results_xml_style()
	return source_window_dict[window_style.split(' ')[0]]

def check_database(database):
	import xbmcvfs
	if not xbmcvfs.exists(database): initialize_databases()

def store_resolved_torrent_to_cloud(debrid_service):
	return get_setting('store_torrent.%s' % debrid_service.lower()) == 'true'

def debrid_enabled(debrid_service):
	enabled = get_setting('%s.enabled' % debrid_service) == 'true'
	if not enabled: return False
	authed = get_setting('%s.token' % debrid_service)
	if authed not in (None, ''): return True
	return False

def debrid_priority(debrid_service):
	return int(get_setting('%s.priority' % debrid_service, '10'))

def display_sleep_time():
	return 100

def show_specials():
	return get_setting('show_specials') == 'true'

def auto_start_fen():
	return get_setting('auto_start_fen') == 'true'

def setview_delay():
	return float(int(get_setting('setview_delay', '800')))/1000
	
def movies_directory():
	return translate_path(get_setting('movies_directory'))
	
def tv_show_directory():
	return translate_path(get_setting('tv_shows_directory'))

def download_directory(db_type):
	setting = 'movie_download_directory' if db_type == 'movie' \
		else 'tvshow_download_directory' if db_type == 'episode' \
		else 'image_download_directory' if db_type in ('thumb_url', 'image_url', 'image') \
		else 'premium_download_directory'
	if get_setting(setting) != '': return translate_path(get_setting(setting))
	else: return False

def source_folders_directory(db_type, source):
	setting = '%s.movies_directory' % source if db_type == 'movie' else '%s.tv_shows_directory' % source
	if get_setting(setting) not in ('', 'None', None): return translate_path( get_setting(setting))
	else: return False

def paginate():
	return get_setting('paginate.lists') == "true"

def page_limit():
	return int(get_setting('page_limit', '20'))

def ignore_articles():
	return get_setting('ignore_articles') == "true"

def default_all_episodes():
	return int(get_setting('default_all_episodes'))

def quality_filter(setting):
	return get_setting(setting).split(', ')

def include_prerelease_results():
	return get_setting('include_prerelease_results') == "true"

def include_sources_in_filter(source_setting):
	return get_setting('%s_in_filter' % source_setting) == "true"

def auto_play():
	return get_setting('auto_play') == "true"

def autoplay_next_episode():
	if auto_play() and get_setting('autoplay_next_episode') == "true": return True
	else: return False

def autoplay_next_check_threshold():
	return int(get_setting('autoplay_next_check_threshold', '3'))

def filter_hevc():
	return int(get_setting('filter_hevc', '0'))

def sync_kodi_library_watchstatus():
	return get_setting('sync_kodi_library_watchstatus') == "true"

def refresh_trakt_on_startup():
	return get_setting('refresh_trakt_on_startup') == "true"
	
def trakt_cache_duration():
	duration = (1, 24, 168)
	return duration[int(get_setting('trakt_cache_duration'))]

def calendar_focus_today():
	return get_setting('calendar_focus_today') == 'true'

def furk_easynews_active():
	furk_api = get_setting('furk_api_key')
	if not furk_api:
		if not get_setting('furk_login') or not get_setting('furk_password'): furk_enabled = False
		else: furk_enabled = True
	else: furk_enabled = True
	easynews_enabled = False if '' in (get_setting('easynews_user'), get_setting('easynews_password')) else True
	return furk_enabled, easynews_enabled

def watched_indicators():
	if get_setting('trakt_user') == '': return 0
	watched_indicators = get_setting('watched_indicators')
	if watched_indicators == '0': return 0
	if watched_indicators == '1' and get_setting('sync_fen_watchstatus') == 'true': return 1
	return 2

def sync_fen_watchstatus():
	if get_setting('sync_fen_watchstatus') == 'false': return False
	if get_setting('trakt_user') == '': return False
	if watched_indicators() in (0, 2): return False
	return True

def check_prescrape_sources(scraper):
	if scraper in ('furk', 'easynews', 'rd-cloud', 'pm-cloud', 'ad-cloud'): return get_setting('check.%s' % scraper) == "true"
	if get_setting('check.%s' % scraper) == "true" and get_setting('auto_play') != "true": return True
	else: return False

def skip_duplicates():
	return get_setting('skip_duplicates') == "true"

def internal_scraper_order():
	setting = get_setting('results.internal_scrapers_order')
	if setting in ('', None):
		setting = 'FILES, FURK, EASYNEWS, CLOUD'
	return setting.split(', ')

def internal_scrapers_order_display():
	setting = get_setting('results.internal_scrapers_order_display')
	if setting in ('', None):
		setting = '$ADDON[plugin.video.fen 32493], $ADDON[plugin.video.fen 32069], $ADDON[plugin.video.fen 32070], $ADDON[plugin.video.fen 32586]'
	return setting.split(', ')

def results_sort_order():
	results_sort_order = get_setting('results.sort_order')
	if results_sort_order == '0': return ['quality_rank', 'internal_rank', 'host_rank', 'name_rank', 'external_size', 'size', 'debrid_rank'] #Quality, Provider, Size, Debrid
	if results_sort_order == '1': return ['quality_rank', 'internal_rank', 'host_rank', 'external_size', 'size', 'name_rank', 'debrid_rank'] #Quality, Size, Provider, Debrid
	if results_sort_order == '2': return ['internal_rank', 'host_rank', 'name_rank', 'quality_rank', 'external_size', 'size', 'debrid_rank'] #Provider, Quality, Size, Debrid
	if results_sort_order == '3': return ['internal_rank', 'host_rank', 'name_rank', 'external_size', 'size', 'quality_rank', 'debrid_rank'] #Provider, Size, Quality, Debrid
	if results_sort_order == '4': return ['external_size', 'size', 'quality_rank', 'internal_rank', 'host_rank', 'name_rank', 'debrid_rank'] #Size, Quality, Provider, Debrid
	if results_sort_order == '5': return ['external_size', 'size', 'internal_rank', 'host_rank', 'name_rank', 'quality_rank', 'debrid_rank'] #Size, Provider, Quality, Debrid
	return ['quality_rank', 'internal_rank', 'host_rank', 'name_rank', 'external_size', 'size', 'debrid_rank'] #Quality, Provider, Size, Debrid

def sorted_first(scraper_setting):
	return get_setting('results.%s' % scraper_setting) == "true"

def active_scrapers(group_folders=False):
	folders = ['folder1', 'folder2', 'folder3', 'folder4', 'folder5']
	settings = ['provider.external', 'provider.furk', 'provider.easynews', 'provider.rd-cloud', 'provider.pm-cloud', 'provider.ad-cloud']
	active = [i.split('.')[1] for i in settings if get_setting(i) == 'true']
	if get_setting('provider.folders') == 'true':
		if group_folders: active.append('folders')
		else: active += folders
	return active

def auto_resume():
	auto_resume = get_setting('auto_resume')
	if auto_resume == '1': return True
	if auto_resume == '2' and auto_play(): return True
	else: return False

def set_resume():
	return float(get_setting('resume.threshold'))

def set_watched():
	return float(get_setting('watched.threshold'))

def nextep_threshold():
	return float(get_setting('nextep.threshold'))

def nav_jump_use_alphabet():
	if get_setting('cache_browsed_page') == 'true': return False
	if get_setting('nav_jump') == '0': return False
	else: return True

def use_season_title():
	return get_setting('use_season_title') == "true"

def unaired_color():
	return get_setting('unaired_color', 'red')

def single_ep_format():
	date_format = get_setting('single_ep_format')
	if date_format == '0': return '%d-%m-%Y'
	elif date_format == '1': return '%Y-%m-%d'
	elif date_format == '2': return '%m-%d-%Y'
	else: return '%Y-%m-%d'

def single_ep_display_title():
	return int(get_setting('single_ep_display', '0'))

def nextep_display_settings():
	include_title = get_setting('nextep.include_title') == 'true'
	include_airdate = get_setting('nextep.include_airdate') == 'true'
	airdate_colour = get_setting('nextep.airdate_colour', 'magenta')
	unaired_colour = get_setting('nextep.unaired_colour', 'red')
	unwatched_colour = get_setting('nextep.unwatched_colour', 'darkgoldenrod')
	return {'include_title': include_title, 'include_airdate': include_airdate, 'airdate_colour': airdate_colour,
			'unaired_colour': unaired_colour, 'unwatched_colour': unwatched_colour}

def nextep_content_settings():
	sort_type = int(get_setting('nextep.sort_type'))
	sort_order = int(get_setting('nextep.sort_order'))
	sort_direction = True if sort_order == 0 else False
	sort_key = 'curr_last_played_parsed' if sort_type == 0 else 'first_aired' if sort_type == 1 else 'name'
	cache_to_disk = get_setting('nextep.cache_to_disk') == 'true'
	include_unaired = get_setting('nextep.include_unaired') == 'true'
	include_unwatched = get_setting('nextep.include_unwatched') == 'true'
	include_in_progress = get_setting('nextep.include_in_progress', 'false') == 'true'
	return {'cache_to_disk': cache_to_disk, 'sort_key': sort_key, 'sort_direction': sort_direction, 'sort_type': sort_type, 'sort_order':sort_order,
			'include_unaired': include_unaired, 'include_unwatched': include_unwatched, 'include_in_progress': include_in_progress}

def scraping_settings():
	def provider_color(provider, fallback):
		return get_setting('provider.%s_colour' % provider, fallback)
	highlight_type = int(get_setting('highlight.type', '0'))
	hoster_highlight, torrent_highlight = '', ''
	furk_highlight, easynews_highlight, debrid_cloud_highlight, folders_highlight = '', '', '', ''
	rd_highlight, pm_highlight, ad_highlight, free_highlight = '', '', '', ''
	highlight_4K, highlight_1080P, highlight_720P, highlight_SD = '', '', '', ''
	if highlight_type in (0, 1):
		furk_highlight = provider_color('furk', 'crimson')
		easynews_highlight = provider_color('easynews', 'limegreen')
		debrid_cloud_highlight = provider_color('debrid_cloud', 'darkviolet')
		folders_highlight = provider_color('folders', 'darkgoldenrod')
		free_highlight = provider_color('free', 'teal')
		if highlight_type == 0:
			hoster_highlight = get_setting('hoster.identify', 'dodgerblue')
			torrent_highlight = get_setting('torrent.identify', 'fuchsia')
		else:
			rd_highlight = provider_color('rd', 'seagreen')
			pm_highlight = provider_color('pm', 'orangered')
			ad_highlight = provider_color('ad', 'goldenrod')
	else:
		highlight_4K = get_setting('scraper_4k_highlight', 'fuchsia')
		highlight_1080P = get_setting('scraper_1080p_highlight', 'lawngreen')
		highlight_720P = get_setting('scraper_720p_highlight', 'gold')
		highlight_SD = get_setting('scraper_SD_highlight', 'lightsaltegray')
	return {'highlight_type': highlight_type, 'hoster_highlight': hoster_highlight, 'torrent_highlight': torrent_highlight,'real-debrid': rd_highlight, 'premiumize': pm_highlight,
			'alldebrid': ad_highlight, 'gdrive': free_highlight, 'ororo': free_highlight, 'ad-cloud': debrid_cloud_highlight, 'rd-cloud': debrid_cloud_highlight,
			'pm-cloud': debrid_cloud_highlight, 'furk': furk_highlight, 'easynews': easynews_highlight, 'folders': folders_highlight, '4k': highlight_4K, '1080p': highlight_1080P,
			'720p': highlight_720P, 'sd': highlight_SD}

def get_fanart_data():
	return get_setting('get_fanart_data') == 'true'

def fanarttv_client_key():
	return get_setting('fanart_client_key', 'fe073550acf157bdb8a4217f215c0882')

def tmdb_api_key():
	return get_setting('tmdb_api', '1b0d3c6ac6a6c0fa87b55a1069d6c9c8')

def get_resolution():
	resolution = get_setting('image_resolutions', '2')
	if resolution == '0': return {'poster': 'w185', 'fanart': 'w300', 'still': 'w185', 'profile': 'w185'}
	if resolution == '1': return {'poster': 'w342', 'fanart': 'w780', 'still': 'w300', 'profile': 'w185'}
	if resolution == '2': return {'poster': 'w780', 'fanart': 'w1280', 'still': 'original', 'profile': 'h632'}
	if resolution == '3': return {'poster': 'original', 'fanart': 'original', 'still': 'original', 'profile': 'original'}
	else: return {'poster': 'w780', 'fanart': 'w1280', 'still': 'original', 'profile': 'h632'}

def get_language():
	return get_setting('meta_language', 'en')

def user_info():
	tmdb_api = tmdb_api_key()
	extra_fanart_enabled = get_fanart_data()
	image_resolution = get_resolution()
	meta_language = get_language()
	if extra_fanart_enabled: fanart_client_key = fanarttv_client_key()
	else: fanart_client_key = ''
	return {'extra_fanart_enabled': extra_fanart_enabled, 'image_resolution': image_resolution , 'language': meta_language,
			'fanart_client_key': fanart_client_key, 'tmdb_api': tmdb_api, }

def list_actions_global():
	global list_actions
	list_actions = []

def initialize_databases():
	import xbmcvfs
	import os
	try: from sqlite3 import dbapi2 as database
	except ImportError: from pysqlite2 import dbapi2 as database
	from modules.settings_reader import make_settings_dict
	DATA_PATH = translate_path('special://profile/addon_data/plugin.video.fen/')
	if not xbmcvfs.exists(DATA_PATH): xbmcvfs.mkdirs(DATA_PATH)
	NAVIGATOR_DB = os.path.join(DATA_PATH, "navigator.db")
	WATCHED_DB = os.path.join(DATA_PATH, "watched_status.db")
	FAVOURITES_DB = os.path.join(DATA_PATH, "favourites.db")
	VIEWS_DB = os.path.join(DATA_PATH, "views.db")
	TRAKT_DB = os.path.join(DATA_PATH, "fen_trakt2.db")
	FEN_DB = os.path.join(DATA_PATH, "fen_cache2.db")
	make_settings_dict()
	#Always check NAVIGATOR.
	dbcon = database.connect(NAVIGATOR_DB)
	dbcon.execute("""CREATE TABLE IF NOT EXISTS navigator
					  (list_name text, list_type text, list_contents text) 
				   """)
	if not xbmcvfs.exists(WATCHED_DB):
		dbcon = database.connect(WATCHED_DB)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS progress
						  (db_type text, media_id text, season integer, episode integer,
						  resume_point text, curr_time text,
						  unique(db_type, media_id, season, episode)) 
					   """)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS watched_status
						  (db_type text, media_id text, season integer,
						  episode integer, last_played text, title text,
						  unique(db_type, media_id, season, episode)) 
					   """)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS exclude_from_next_episode
						  (media_id text, title text) 
					   """)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS unwatched_next_episode
						  (media_id text) 
					   """)
		dbcon.close()
	if not xbmcvfs.exists(FAVOURITES_DB):
		dbcon = database.connect(FAVOURITES_DB)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS favourites
						  (db_type text, tmdb_id text, title text, unique (db_type, tmdb_id)) 
					   """)
		dbcon.close()
	if not xbmcvfs.exists(VIEWS_DB):
		dbcon = database.connect(VIEWS_DB)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS views
						  (view_type text, view_id text, unique (view_type)) 
					   """)
		dbcon.close()
	if not xbmcvfs.exists(TRAKT_DB):
		dbcon = database.connect(TRAKT_DB)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS fentrakt(
					id text unique, data text, expires INTEGER)
							""")
		dbcon.close()
	if not xbmcvfs.exists(FEN_DB):
		dbcon = database.connect(FEN_DB)
		dbcon.execute("""CREATE TABLE IF NOT EXISTS fencache(
					id text unique, data text, expires INTEGER)
							""")
		dbcon.close()
	return True
