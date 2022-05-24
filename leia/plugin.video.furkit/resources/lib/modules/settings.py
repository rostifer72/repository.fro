import xbmc, xbmcaddon
import os
# from resources.lib.modules.utils import logger

__addon__ = xbmcaddon.Addon(id='plugin.video.furkit')
ADDON_PATH = xbmc.translatePath(__addon__.getAddonInfo('path'))
DATA_PATH = xbmc.translatePath(__addon__.getAddonInfo('profile'))

def addon_installed(addon_id):
    if xbmc.getCondVisibility('System.HasAddon(%s)' % addon_id): return True
    else: return False

def get_theme():
    if __addon__.getSetting('theme_installed') == 'true':
        theme = __addon__.getSetting('furkit.theme').lower()
        result = os.path.join(xbmcaddon.Addon('script.tiki.artwork').getAddonInfo('path'), 'resources', 'media', theme)
    elif addon_installed('script.tiki.artwork'):
        __addon__.setSetting('theme_installed', 'true')
        theme = __addon__.getSetting('furkit.theme').lower()
        if theme in ['-', '']: theme = 'light'
        result = os.path.join(xbmcaddon.Addon('script.tiki.artwork').getAddonInfo('path'), 'resources', 'media', theme)
    else: result = 'null'
    return result

def tmdb_api():
    tmdb_api = __addon__.getSetting('tmdb_api')
    if not tmdb_api or tmdb_api == '':
        tmdb_api = '1b0d3c6ac6a6c0fa87b55a1069d6c9c8'
    return tmdb_api

def check_database(database):
    import xbmcvfs
    if not xbmcvfs.exists(database): initialize_databases()

def use_dialog():
    if __addon__.getSetting('use_dialog') == "1": return True
    else: return False

def cache_to_disc():
    if __addon__.getSetting('cache_to_disc') == "true": return True
    else: return False

def addon():
    return __addon__

def show_specials():
    if __addon__.getSetting('show_specials') == 'true': return True
    else: return False

def resume_type(origin):
    if __addon__.getSetting('resume_autoplay') == 'true' and auto_play(origin): return 'Automatic'
    return __addon__.getSetting('resume')

def adjusted_datetime(string=False, dt=False):
    from datetime import datetime, timedelta
    d = datetime.utcnow() + timedelta(hours=int(__addon__.getSetting('datetime.offset')))
    if dt: return d
    d = datetime.date(d)
    if string:
        try: d = d.strftime('%Y-%m-%d')
        except ValueError: d = d.strftime('%Y-%m-%d')
    else: return d
    
def movies_directory():
    return xbmc.translatePath(__addon__.getSetting('movies_directory'))
    
def tv_show_directory():
    return xbmc.translatePath(__addon__.getSetting('tv_shows_directory'))

def download_directory(db_type):
    setting = 'movie_download_directory' if db_type == 'movie' \
        else 'tvshow_download_directory' if db_type == 'episode' \
        else 'furk_file_download_directory' if db_type in ('furk_file', 'archive') \
        else 'easynews_file_download_directory'
    if __addon__.getSetting(setting) != '': return xbmc.translatePath( __addon__.getSetting(setting))
    else: return False

def backup_directory():
    return __addon__.getSetting('backup_directory')

def quality_filter(setting):
    return __addon__.getSetting(setting).split(', ')

def include_prerelease_results(origin=None):
    setting = 'include_prerelease_results' if origin == None else 'include_prerelease_results_library'
    if __addon__.getSetting(setting) == "true": return True
    else: return False

def include_local_in_filter(autoplay=None):
    setting = 'include_local_in_filter' if not autoplay else 'include_local_in_filter_autoplay'
    if __addon__.getSetting(setting) == "true": return True
    else: return False

def include_uncached_results():
    if __addon__.getSetting('include_uncached_results') == "true": return True
    else: return False

def auto_play(origin=None):
    setting = 'auto_play' if origin == None else 'auto_play_library'
    if __addon__.getSetting(setting) == "true": return True
    else: return False

def auto_resolve(origin=None):
    setting = 'auto_resolve' if origin == None else 'auto_resolve_library'
    if __addon__.getSetting(setting) == "true": return True
    else: return False

def autoplay_next_episode(origin=None):
    setting_autoplay = 'auto_play' if origin == None else 'auto_play_library'
    setting_next_ep = 'autoplay_next_episode' if origin == None else 'autoplay_next_episode_library'
    if __addon__.getSetting(setting_next_ep) == "true" and __addon__.getSetting(setting_autoplay) == 'true': return True
    else: return False

def autoplay_next_prompt(origin=None):
    setting = 'autoplay_next_still_watching' if origin == None else 'autoplay_next_still_watching_library'
    if __addon__.getSetting(setting) == 'true': return True
    else: return False

def autoplay_next_number(origin=None):
    setting = 'autoplay_next_number' if origin == None else 'autoplay_next_number_library'
    return int(__addon__.getSetting(setting))

def prefer_hevc(origin=None):
    setting = 'prefer_hevc' if origin == None else 'prefer_hevc_library'
    if __addon__.getSetting(setting) == "true": return True
    else: return False

def sync_kodi_library_watchstatus():
    if __addon__.getSetting('sync_kodi_library_watchstatus') == "true": return True
    else: return False

def define_origin(source=None):
    return None if source == None else 'context'

def watched_indicators():
    if __addon__.getSetting('trakt_user') == '': return 0
    elif __addon__.getSetting('watched_indicators') == '0': return 0
    elif __addon__.getSetting('watched_indicators') == '1' and __addon__.getSetting('sync_furkit_watchstatus') == 'true': return 1
    else: return 2

def check_library():
    if __addon__.getSetting('check_library') == "true" and __addon__.getSetting('auto_play') != "true": return True
    else: return False

def subscription_update():
    if __addon__.getSetting('subscription_update') == "true": return True
    else: return False

def skip_duplicates():
    if __addon__.getSetting('skip_duplicates') == "true": return True
    else: return False

def update_library_after_service():
    if __addon__.getSetting('update_library_after_service') == "true": return True
    else: return False

def results_sort_order():
    results_sort_order = __addon__.getSetting('results.sort_order')
    if results_sort_order == '0': return ('quality_rank', 'name_rank', 'size')
    elif results_sort_order == '1': return ('name_rank', 'quality_rank', 'size')
    else: return ('', '', '')

def local_sorted_first():
    if __addon__.getSetting('results.sort_local_first') == "true": return True
    else: return False

def provider_color(provider):
    return __addon__.getSetting('provider.%s_colour' % provider)

def active_scrapers():
    settings = ['provider.local', 'provider.furk', 'provider.easynews', 'provider.external']
    return [i.split('.')[1] for i in settings if __addon__.getSetting(i) == 'true']

def show_filenames():
    if __addon__.getSetting('results.show_filenames') == 'true': return True
    return False

def library_use_custom_list():
    if __addon__.getSetting('library_use_custom_list') == 'true': return True
    else: return False

def library_default_movie_list_valid():
    if __addon__.getSetting('library_default_movie_list') == 'None': return False
    else: return True

def library_default_tvshow_list_valid():
    if __addon__.getSetting('library_default_tvshow_list') == 'None': return False
    else: return True

def library_default_list_name(db_type):
    setting_id = 'library_default_movie_list' if db_type == 'movie' else 'library_default_tvshow_list'
    return __addon__.getSetting(setting_id)

def subscription_timer():
    hours_list = [1, 2, 4, 6, 8, 10, 12, 14, 15, 18, 24]
    return hours_list[int(__addon__.getSetting('subscription_timer'))]

def set_resume():
    return float(__addon__.getSetting('resume.threshold'))

def set_watched():
    return float(__addon__.getSetting('watched.threshold'))

def set_nextep():
    return float(__addon__.getSetting('nextep.threshold'))

def nav_jump_use_alphabet():
    if __addon__.getSetting('nav_jump') == '0': return False
    else: return True

def all_trailers():
    if __addon__.getSetting('all_trailers') == "true": return True
    else: return False

def use_season_title():
    if __addon__.getSetting('use_season_title') == "true": return True
    else: return False

def unaired_episode_colour():
    unaired_episode_colour = __addon__.getSetting('unaired_episode_colour')
    if not unaired_episode_colour or unaired_episode_colour == '': unaired_episode_colour = 'red'
    return unaired_episode_colour

def nextep_airdate_format():
    date_format = __addon__.getSetting('nextep.airdate_format')
    if date_format == '0': return '%d-%m-%Y'
    elif date_format == '1': return '%Y-%m-%d'
    elif date_format == '2': return '%m-%d-%Y'
    else: return '%Y-%m-%d'

def nextep_display_settings():
    from ast import literal_eval
    include_airdate = True
    airdate_colour = 'magenta'
    unaired_colour = 'red'
    unwatched_colour = 'darkgoldenrod'
    try: include_airdate = literal_eval(__addon__.getSetting('nextep.include_airdate').title())
    except: pass
    try: airdate_colour = __addon__.getSetting('nextep.airdate_colour')
    except: pass
    try: unaired_colour = __addon__.getSetting('nextep.unaired_colour')
    except: pass
    try: unwatched_colour = __addon__.getSetting('nextep.unwatched_colour')
    except: pass
    return {'include_airdate': include_airdate, 'airdate_colour': airdate_colour,
            'unaired_colour': unaired_colour, 'unwatched_colour': unwatched_colour}

def nextep_content_settings():
    from ast import literal_eval
    sort_type = int(__addon__.getSetting('nextep.sort_type'))
    sort_order = int(__addon__.getSetting('nextep.sort_order'))
    sort_direction = True if sort_order == 0 else False
    sort_key = 'curr_last_played_parsed' if sort_type == 0 else 'first_aired' if sort_type == 1 else 'name'
    include_unaired = literal_eval(__addon__.getSetting('nextep.include_unaired').title())
    include_unwatched = literal_eval(__addon__.getSetting('nextep.include_unwatched').title())
    return {'sort_key': sort_key, 'sort_direction': sort_direction, 'sort_type': sort_type, 'sort_order':sort_order,
            'include_unaired': include_unaired, 'include_unwatched': include_unwatched}

def create_directory(dir_path, dir_name=None):
    if dir_name:
        dir_path = os.path.join(dir_path, dir_name)
    dir_path = dir_path.strip()
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path

def initialize_databases():
    import xbmcvfs
    if not xbmcvfs.exists(DATA_PATH): xbmcvfs.mkdirs(DATA_PATH)
    NAVIGATOR_DB = os.path.join(DATA_PATH, "navigator.db")
    WATCHED_DB = os.path.join(DATA_PATH, "watched_status.db")
    FAVOURITES_DB = os.path.join(DATA_PATH, "favourites.db")
    SUBSCRIPTIONS_DB = os.path.join(DATA_PATH, "subscriptions.db")
    VIEWS_DB = os.path.join(DATA_PATH, "views.db")
    FURKIT_DB = os.path.join(DATA_PATH, "furkit_cache.db")
    if not xbmcvfs.exists(NAVIGATOR_DB):
        try: from sqlite3 import dbapi2 as database
        except ImportError: from pysqlite2 import dbapi2 as database
        dbcon = database.connect(NAVIGATOR_DB)
        dbcon.execute("""CREATE TABLE IF NOT EXISTS navigator
                          (list_name text, list_type text, list_contents text) 
                       """)
        dbcon.close()
    if not xbmcvfs.exists(WATCHED_DB):
        try: from sqlite3 import dbapi2 as database
        except: from pysqlite2 import dbapi2 as database
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
        try:from sqlite3 import dbapi2 as database
        except ImportError:from pysqlite2 import dbapi2 as database
        dbcon = database.connect(FAVOURITES_DB)
        dbcon.execute("""CREATE TABLE IF NOT EXISTS favourites
                          (db_type text, tmdb_id text, title text, unique (db_type, tmdb_id)) 
                       """)
        dbcon.close()
    if not xbmcvfs.exists(SUBSCRIPTIONS_DB):
        try: from sqlite3 import dbapi2 as database
        except ImportError: from pysqlite2 import dbapi2 as database
        dbcon = database.connect(SUBSCRIPTIONS_DB)
        dbcon.execute("""CREATE TABLE IF NOT EXISTS subscriptions
                          (db_type text, tmdb_id text, title text, unique (db_type, tmdb_id)) 
                       """)
        dbcon.close()
    if not xbmcvfs.exists(VIEWS_DB):
        try: from sqlite3 import dbapi2 as database
        except ImportError: from pysqlite2 import dbapi2 as database
        dbcon = database.connect(VIEWS_DB)
        dbcon.execute("""CREATE TABLE IF NOT EXISTS views
                          (view_type text, view_id text, unique (view_type)) 
                       """)
        dbcon.close()
    if not xbmcvfs.exists(FURKIT_DB):
        try: from sqlite3 import dbapi2 as database
        except ImportError: from pysqlite2 import dbapi2 as database
        dbcon = database.connect(FURKIT_DB)
        dbcon.execute("""CREATE TABLE IF NOT EXISTS furkitcache
                           (id text UNIQUE, expires integer, data text, checksum integer)
                            """)
        dbcon.close()
    return True
