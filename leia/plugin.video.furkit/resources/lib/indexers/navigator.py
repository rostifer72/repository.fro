import sys, os
import xbmc, xbmcvfs, xbmcaddon, xbmcplugin, xbmcgui
import urllib
import json
from urlparse import parse_qsl
from resources.lib.modules.default_menus import DefaultMenus
from resources.lib.modules import settings
try: from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database
# from resources.lib.modules.utils import logger

__addon_id__ = 'plugin.video.furkit'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])
addon_dir = xbmc.translatePath(__addon__.getAddonInfo('path'))
profile_dir = xbmc.translatePath(__addon__.getAddonInfo('profile'))
NAVIGATOR_DB = os.path.join(profile_dir, "navigator.db")

class Navigator:
    def __init__(self, list_name=None):
        self.view = 'view.main'
        self.icon_directory = settings.get_theme()
        self.list_name = list_name
        self.fanart = os.path.join(addon_dir, 'fanart.png')

    def main_lists(self):
        self.build_main_lists()
        if not __addon__.getSetting('new_addon_info_read') == 'true':
            xbmc.sleep(250)
            self.show_new_addon_info()

    def show_new_addon_info(self):
        from resources.lib.modules.nav_utils import show_text
        show_text(heading='Furk It - Important Information!!', text_file=xbmc.translatePath(os.path.join(addon_dir, "migration.txt")))
        __addon__.setSetting('new_addon_info_read', 'true')

    def certifications(self):
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        mode = 'build_movie_list' if params.get('menu_type') == 'movie' else 'build_tvshow_list'
        action = 'tmdb_movies_certifications' if params.get('menu_type') == 'movie' else 'trakt_tv_certifications'
        certifications = ('G','PG','PG-13','R','NC-17', 'NR') if params.get('menu_type') == 'movie' else ('tv-y','tv-y7','tv-g','tv-pg','tv-14','tv-ma')
        for cert in certifications:
            self.add_dir({'mode': mode, 'action': action, 'certification': cert, 'foldername': cert.upper(), 'list_name': '%ss %s Certification' % ((params.get('menu_type')).capitalize(), cert.upper()), 'info': 'Browse %s Certification for %sS.' % (cert.upper(), (params.get('menu_type')).upper())}, cert.upper(), iconImage='certifications.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def languages(self):
        languages = [('Arabic', 'ar'), ('Bosnian', 'bs'), ('Bulgarian', 'bg'), ('Chinese', 'zh'),
        ('Croatian', 'hr'), ('Dutch', 'nl'), ('English', 'en'), ('Finnish', 'fi'), ('French', 'fr'),
        ('German', 'de'), ('Greek', 'el'), ('Hebrew', 'he'), ('Hindi ', 'hi'), ('Hungarian', 'hu'),
        ('Icelandic', 'is'), ('Italian', 'it'), ('Japanese', 'ja'), ('Korean', 'ko'), ('Macedonian', 'mk'),
        ('Norwegian', 'no'), ('Persian', 'fa'), ('Polish', 'pl'), ('Portuguese', 'pt'), ('Punjabi', 'pa'),
        ('Romanian', 'ro'), ('Russian', 'ru'), ('Serbian', 'sr'), ('Slovenian', 'sl'), ('Spanish', 'es'),
        ('Swedish', 'sv'), ('Turkish', 'tr'), ('Ukrainian', 'uk')]
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        mode = 'build_movie_list' if params.get('menu_type') == 'movie' else 'build_tvshow_list'
        action = 'tmdb_movies_languages' if params.get('menu_type') == 'movie' else 'tmdb_tv_languages'
        for lang in languages:
            self.add_dir({'mode': mode, 'action': action, 'language': lang[1], 'foldername': lang, 'list_name': '%ss %s Language' % ((params.get('menu_type')).capitalize(), lang[0]), 'info': 'Browse %s Language %ss.' % (lang[0], (params.get('menu_type')).capitalize())}, lang[0], iconImage='languages.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def years(self):
        import datetime
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))
        year = datetime.strftime('%Y')
        mode = 'build_movie_list' if params.get('menu_type') == 'movie' else 'build_tvshow_list'
        action = 'tmdb_movies_year' if params.get('menu_type') == 'movie' else 'tmdb_tv_year'
        for i in range(int(year), 1900, -1):
            self.add_dir({'mode': mode, 'action': action, 'year': str(i), 'foldername': '%s - %s' % (str(i), params.get('menu_type')), 'list_name': '%ss %s Premiered' % ((params.get('menu_type')).capitalize(), str(i)), 'info': 'Browse %sS that Premiered in %s.' % (params.get('menu_type').upper(), str(i))}, str(i), iconImage='calender.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def genres(self):
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        mode = 'build_movie_list' if params.get('menu_type') == 'movie' else 'build_tvshow_list'
        action = 'tmdb_movies_genres' if params.get('menu_type') == 'movie' else 'tmdb_tv_genres'
        if params.get('menu_type') == 'movie':
            genre_list = ({'Action': ['28', 'genre_action.png'], 'Adventure': ['12', 'genre_adventure.png'],
            'Animation': ['16', 'genre_animation.png'], 'Comedy': ['35', 'genre_comedy.png'],
            'Crime': ['80', 'genre_crime.png'], 'Documentary': ['99', 'genre_documentary.png'],
            'Drama': ['18', 'genre_drama.png'], 'Family': ['10751', 'genre_family.png'],
            'Fantasy': ['14', 'genre_fantasy.png'], 'History': ['36', 'genre_history.png'],
            'Horror': ['27', 'genre_horror.png'], 'Music': ['10402', 'genre_music.png'],
            'Mystery': ['9648', 'genre_mystery.png'], 'Romance': ['10749', 'genre_romance.png'],
            'Science Fiction': ['878', 'genre_scifi.png'], 'TV Movie': ['10770', 'genre_soap.png'],
            'Thriller': ['53', 'genre_thriller.png'], 'War': ['10752', 'genre_war.png'], 
            'Western': ['37', 'genre_western.png']})
        else:
            genre_list = ({'Action & Adventure': ['10759', 'genre_action.png'], 'Animation': ['16', 'genre_animation.png'],
            'Comedy': ['35', 'genre_comedy.png'], 'Crime': ['80', 'genre_crime.png'],
            'Documentary': ['99', 'genre_documentary.png'], 'Drama': ['18', 'genre_drama.png'],
            'Family': ['10751', 'genre_family.png'], 'Kids': ['10762', 'genre_kids.png'],
            'Mystery': ['9648', 'genre_mystery.png'], 'News':['10763', 'genre_news.png'],
            'Reality': ['10764', 'genre_reality.png'], 'Sci-Fi & Fantasy': ['10765', 'genre_scifi.png'],
            'Soap': ['10766', 'genre_soap.png'], 'Talk': ['10767', 'genre_talk.png'],
            'War & Politics': ['10768', 'genre_war.png'], 'Western': ['37', 'genre_western.png']})
        self.add_dir({'mode': mode, 'action': action, 'genre_list': json.dumps(genre_list), 'exclude_external': 'true', 'foldername': 'Multiselect', 'info': 'Select Multiple Genres for Movies that Satisfy All Selected Genres.'}, '[B]Multiselect...[/B]', iconImage='genres.png')
        for genre, value in sorted(genre_list.items()):
            self.add_dir({'mode': mode, 'action': action, 'genre_id': value[0], 'foldername': genre, 'list_name': '%ss %s Genre' % ((params.get('menu_type')).capitalize(), genre), 'info': 'Browse %s Genre for %ss.' % (genre, (params.get('menu_type')).capitalize())}, genre, iconImage=value[1])
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def networks(self):
        networks = [{"id":54,"name":"Disney Channel", "logo": "https://i.imgur.com/ZCgEkp6.png"},{"id":44,"name":"Disney XD", "logo": "https://i.imgur.com/PAJJoqQ.png"},
        {"id":2,"name":"ABC", "logo": "https://i.imgur.com/qePLxos.png"},{"id":493,"name":"BBC America", "logo": "https://i.imgur.com/TUHDjfl.png"},{"id":6,"name":"NBC", "logo": "https://i.imgur.com/yPRirQZ.png"},
        {"id":13,"name":"Nickelodeon", "logo": "https://i.imgur.com/OUVoqYc.png"},{"id":14,"name":"PBS", "logo": "https://i.imgur.com/r9qeDJY.png"},{"id":16,"name":"CBS", "logo": "https://i.imgur.com/8OT8igR.png"},
        {"id":19,"name":"FOX", "logo": "https://i.imgur.com/6vc0Iov.png"},{"id":21,"name":"The WB", "logo": "https://i.imgur.com/rzfVME6.png"},{"id":24,"name":"BET", "logo": "https://i.imgur.com/ZpGJ5UQ.png"},
        {"id":30,"name":"USA Network", "logo": "https://i.imgur.com/Doccw9E.png"},{"id":32,"name":"CBC", "logo": "https://i.imgur.com/unQ7WCZ.png"},{"id":173,"name":"AT-X", "logo": "https://i.imgur.com/JshJYGN.png"},
        {"id":33,"name":"MTV", "logo": "https://i.imgur.com/QM6DpNW.png"},{"id":34,"name":"Lifetime", "logo": "https://i.imgur.com/tvYbhen.png"},{"id":35,"name":"Nick Junior", "logo": "https://i.imgur.com/leuCWYt.png"},
        {"id":41,"name":"TNT", "logo": "https://i.imgur.com/WnzpAGj.png"},{"id":43,"name":"National Geographic", "logo": "https://i.imgur.com/XCGNKVQ.png"},{"id":47,"name":"Comedy Central", "logo": "https://i.imgur.com/ko6XN77.png"},
        {"id":49,"name":"HBO", "logo": "https://i.imgur.com/Hyu8ZGq.png"},{"id":55,"name":"Spike", "logo": "https://i.imgur.com/BhXYytR.png"},{"id":67,"name":"Showtime", "logo": "https://i.imgur.com/SawAYkO.png"},
        {"id":56,"name":"Cartoon Network", "logo": "https://i.imgur.com/zmOLbbI.png"},{"id":65,"name":"History Channel", "logo": "https://i.imgur.com/LEMgy6n.png"},{"id":84,"name":"TLC", "logo": "https://i.imgur.com/c24MxaB.png"},
        {"id":68,"name":"TBS", "logo": "https://i.imgur.com/RVCtt4Z.png"},{"id":71,"name":"The CW", "logo": "https://i.imgur.com/Q8tooeM.png"},{"id":74,"name":"Bravo", "logo": "https://i.imgur.com/TmEO3Tn.png"},
        {"id":76,"name":"E!", "logo": "https://i.imgur.com/3Delf9f.png"},{"id":77,"name":"Syfy", "logo": "https://i.imgur.com/9yCq37i.png"},{"id":80,"name":"Adult Swim", "logo": "https://i.imgur.com/jCqbRcS.png"},
        {"id":91,"name":"Animal Planet", "logo": "https://i.imgur.com/olKc4RP.png"},{"id":110,"name":"CTV", "logo": "https://i.imgur.com/qUlyVHz.png"},{"id":129,"name":"A&E", "logo": "https://i.imgur.com/xLDfHjH.png"},
        {"id":158,"name":"VH1", "logo": "https://i.imgur.com/IUtHYzA.png"},{"id":174,"name":"AMC", "logo": "https://i.imgur.com/ndorJxi.png"},{"id":928,"name":"Crackle", "logo": "https://i.imgur.com/53kqZSY.png"},
        {"id":202,"name":"WGN America", "logo": "https://i.imgur.com/TL6MzgO.png"},{"id":209,"name":"Travel Channel", "logo": "https://i.imgur.com/mWXv7SF.png"},{"id":213, "name":"Netflix", "logo": "https://i.imgur.com/jI5c3bw.png"},
        {"id":251,"name":"Audience", "logo": "https://i.imgur.com/5Q3mo5A.png"},{"id":270,"name":"SundanceTV", "logo": "https://i.imgur.com/qldG5p2.png"},{"id":318,"name":"Starz", "logo": "https://i.imgur.com/Z0ep2Ru.png"},
        {"id":359,"name":"Cinemax", "logo": "https://i.imgur.com/zWypFNI.png"},{"id":364,"name":"truTV", "logo": "https://i.imgur.com/HnB3zfc.png"},{"id":384,"name":"Hallmark Channel", "logo": "https://i.imgur.com/zXS64I8.png"},
        {"id":397,"name":"TV Land", "logo": "https://i.imgur.com/1nIeDA5.png"},{"id":1024,"name":"Amazon", "logo": "https://i.imgur.com/ru9DDlL.png"},{"id":1267,"name":"Freeform", "logo": "https://i.imgur.com/f9AqoHE.png"},
        {"id":4,"name":"BBC One", "logo": "https://i.imgur.com/u8x26te.png"},{"id":332,"name":"BBC Two", "logo": "https://i.imgur.com/SKeGH1a.png"},{"id":3,"name":"BBC Three", "logo": "https://i.imgur.com/SDLeLcn.png"},
        {"id":100,"name":"BBC Four", "logo": "https://i.imgur.com/PNDalgw.png"},{"id":214,"name":"Sky One", "logo": "https://i.imgur.com/xbgzhPU.png"},{"id":9,"name":"ITV", "logo": "https://i.imgur.com/5Hxp5eA.png"},
        {"id":26,"name":"Channel 4", "logo": "https://i.imgur.com/6ZA9UHR.png"}, {"id":99,"name":"Channel 5", "logo": "https://i.imgur.com/5ubnvOh.png"},{"id":136,"name":"E4", "logo": "https://i.imgur.com/frpunK8.png"},
        {"id":210,"name":"HGTV", "logo": "https://i.imgur.com/INnmgLT.png"}, {"id":453,"name":"Hulu", "logo": "https://i.imgur.com/uSD2Cdw.png"}, {"id":1436,"name":"YouTube Red", "logo": "https://i.imgur.com/ZfewP1Y.png"},
        {"id":64,"name":"Discovery Channel", "logo": "https://i.imgur.com/8UrXnAB.png"}]
        for item in sorted(networks, key=lambda k: k['name']):
            self.add_dir({'mode': 'build_tvshow_list', 'action': 'tmdb_tv_networks', 'network_id': item['id'], 'foldername': item['name'], 'list_name': '%s %s Network' % ('Tvshows', item['name']), 'info': 'Browse %s Network.'% item['name']}, item['name'], iconImage=item['logo'])
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def trakt_mosts(self):
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        final_mode = 'build_movie_list' if params.get('menu_type') == 'movie' else 'build_tvshow_list'
        action = 'trakt_movies_mosts' if params.get('menu_type') == 'movie' else 'trakt_tv_mosts'
        trakt_mosts = {'Played': ['played', 'most__played.png'],
        'Collected': ['collected', 'most__collected.png'],
        'Watched': ['watched', 'most__watched.png']}
        for most, value in trakt_mosts.items():
            self.add_dir({'mode': 'navigator.trakt_mosts_duration', 'action': action, 'period': value[0], 'menu_type': params.get('menu_type'), 'final_mode': final_mode, 'iconImage': value[1], 'foldername': 'Most %s' % most, 'list_name': '%ss Most %s' % ((params.get('menu_type')).capitalize(), most), 'info': 'Trakt Most %s for %ss.'% (most, (params.get('menu_type')).capitalize())}, '[B]MOST: [/B]%s' % most, iconImage=value[1])
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def trakt_mosts_duration(self):
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        durations = [('This Week', 'weekly'), ('This Month', 'monthly'), ('This Year', 'yearly'), ('All Time', 'all')]
        for duration, urlitem in durations:
            self.add_dir({'mode': params['final_mode'], 'action': params['action'], 'period': params['period'], 'duration': urlitem, 'foldername': duration, 'list_name': '%ss Most %s %s' % ((params.get('menu_type')).capitalize(), params.get('period').capitalize(), duration), 'info': 'Trakt Most %s for %s.' % (params.get('period').capitalize(), duration)}, '[B]MOST %s:[/B] %s' % (params.get('period').upper(), duration), iconImage=params['iconImage'])
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def downloads(self):
        self.add_dir({'mode': 'navigator.download_navigator', 'db_type': 'movie', 'foldername': 'Movie Downloads', 'list_name': 'Movie Downloads', 'info': 'Browse Movies you have Downloaded.'}, '[B]DOWNLOADS: [/B]Movies', iconImage='movies.png')
        self.add_dir({'mode': 'navigator.download_navigator', 'db_type': 'episode', 'foldername': 'TV Show Downloads', 'list_name': 'TV Show Downloads', 'info': 'Browse TV Shows you have Downloaded.'}, '[B]DOWNLOADS: [/B]TV Shows', iconImage='tv.png')
        self.add_dir({'mode': 'navigator.download_navigator', 'db_type': 'furk_file', 'foldername': 'Furk File Downloads', 'list_name': 'Furk File Downloads', 'info': 'Browse Furk Files you have Downloaded'}, '[B]DOWNLOADS: [/B]Furk Files', iconImage='furk.png')
        self.add_dir({'mode': 'navigator.download_navigator', 'db_type': 'easynews_file', 'foldername': 'Easynews File Downloads', 'list_name': 'Easynews File Downloads', 'info': 'Browse Easynews Files you have Downloaded'}, '[B]DOWNLOADS: [/B]Easynews Files', iconImage='easynews.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def download_navigator(self):
        def make_down_directory(isFolder=True):
                url = os.path.join(DOWNLOAD_PATH, item)
                listitem = xbmcgui.ListItem(item)
                listitem.setInfo('video', {'title': item})
                return xbmcplugin.addDirectoryItem(handle=__handle__, url=url, listitem=listitem, isFolder=isFolder)
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        DOWNLOAD_PATH = settings.download_directory(params['db_type'])
        try:
            dirs, files = xbmcvfs.listdir(DOWNLOAD_PATH)
            for item in dirs: make_down_directory()
            for item in files: make_down_directory(False)
        except: pass
        xbmcplugin.setContent(__handle__, 'files')
        xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_FULLPATH)
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def furk(self):
        self.add_dir({'mode': 'furk.my_furk_files', 'list_type': 'file_get_video', 'foldername': 'My Furk Video Files', 'list_name': 'Furk Video Files', 'info': 'Browse Furk Video files saved to My Files in Furk.'}, '[B]FURK: [/B]Video Files', iconImage='lists.png')
        self.add_dir({'mode': 'furk.my_furk_files', 'list_type': 'file_get_audio', 'foldername': 'My Furk Audio Files', 'list_name': 'Furk Audio Files', 'info': 'Browse Furk Audio files saved to My Files in Furk.'}, '[B]FURK: [/B]Audio Files', iconImage='lists.png')
        self.add_dir({'mode': 'furk.my_furk_files', 'list_type': 'file_get_active', 'foldername': 'My Furk Active Downloads', 'list_name': 'My Furk Active Downloads', 'info': 'Browse Your Furk Active Downloads.'}, '[B]FURK: [/B]Active Downloads', iconImage='lists.png')
        self.add_dir({'mode': 'furk.my_furk_files', 'list_type': 'file_get_failed', 'foldername': 'My Furk Failed Downloads', 'list_name': 'My Furk Failed Downloads', 'info': 'Browse Your Furk Failed Downloads.'}, '[B]FURK: [/B]Failed Downloads', iconImage='lists.png')
        self.add_dir({'mode': 'furk.search_furk', 'db_type': 'video', 'foldername': 'Search Furk (Video)', 'list_name': 'Furk Search Video', 'info': 'Search Furk for Video files'}, '[B]FURK: [/B]Search (Video)', iconImage='search.png')
        self.add_dir({'mode': 'furk.search_furk', 'db_type': 'audio', 'foldername': 'Search Furk (Audio)', 'list_name': 'Furk Search Audio', 'info': 'Search Furk for Audio files'}, '[B]FURK: [/B]Search (Audio)', iconImage='search.png')
        self.add_dir({'mode': 'search_history', 'action': 'video', 'foldername': 'Video Search History', 'list_name': 'Furk Search History (Video)', 'info': 'Browse a History of Furk Video Searches. The last 10 searches are stored.'}, '[B]FURK: [/B]Search History (Video)', iconImage='search.png')
        self.add_dir({'mode': 'search_history', 'action': 'audio', 'foldername': 'Audio Search History', 'list_name': 'Furk Search History (Audio)', 'info': 'Browse a History of Furk Audio Searches. The last 10 searches are stored.'}, '[B]FURK: [/B]Search History (Audio)', iconImage='search.png')
        self.add_dir({'mode': 'furk.account_info', 'foldername': 'Account Info', 'list_name': 'Furk Account Info', 'info': 'Summary of information available from your Furk Account. Includes days remaining and current plan.'}, '[B]FURK: [/B]Account Info', iconImage='furk.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def favourites(self):
        self.add_dir({'mode': 'build_movie_list', 'action': 'favourites_movies', 'foldername': 'Movie Favourites', 'list_name': 'Movies Favourites', 'info': 'Browse Furk It Movie Favourites.'}, '[B]FAVOURITES : [/B]Movies', iconImage='movies.png')
        self.add_dir({'mode': 'build_tvshow_list', 'action': 'favourites_tvshows', 'foldername': 'TV Show Favourites', 'list_name': 'Tvshows Favourites', 'info': 'Browse Furk It TV Show Favourites.'}, '[B]FAVOURITES : [/B]TV Shows', iconImage='tv.png')
        self.add_dir({'mode': 'my_furk_audio_favourites', 'foldername': 'Audio Favourites', 'list_name': 'Audio Favourites', 'info': 'Browse Furk It Audio Favourites.'}, '[B]FAVOURITES : [/B]Music', iconImage='genre_music.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def subscriptions(self):
        self.add_dir({'mode': 'build_movie_list', 'action': 'subscriptions_movies', 'foldername': 'Furk It Subscriptions', 'list_name': 'Movies Subscriptions', 'info': 'Browse Furk It Movies in Subscriptions.'}, '[B]SUBSCRIPTIONS : [/B]Movies', iconImage='movies.png')
        self.add_dir({'mode': 'build_tvshow_list', 'action': 'subscriptions_tvshows', 'foldername': 'Furk It Subscriptions', 'list_name': 'Tvshows Subscriptions', 'info': 'Browse Furk It TV Shows in Subscriptions.'}, '[B]SUBSCRIPTIONS : [/B]TV Shows', iconImage='tv.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def kodi_library(self):
        self.add_dir({'mode': 'build_movie_list', 'action': 'kodi_library_movies', 'foldername': 'Movies Kodi Library', 'list_name': 'Movies Kodi Library', 'info': 'Browse Movies from your Local Kodi Library.'}, '[B]KODI LIBRARY : [/B]Movies', iconImage='movies.png')
        self.add_dir({'mode': 'build_tvshow_list', 'action': 'kodi_library_tvshows', 'foldername': 'TV Shows Kodi Library', 'list_name': 'Tvshows Kodi Library', 'info': 'Browse TV Shows from your Local Kodi Library.'}, '[B]KODI LIBRARY : [/B]TV Shows', iconImage='tv.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def in_progress(self):
        self.add_dir({'mode': 'build_movie_list', 'action': 'in_progress_movies', 'foldername': 'Movies In Progress', 'list_name': 'Movies In Progress', 'info': 'Browse Movies that are in the process of being watched.'}, '[B]IN PROGRESS : [/B]Movies', iconImage='movies.png')
        self.add_dir({'mode': 'build_tvshow_list', 'action': 'in_progress_tvshows', 'foldername': 'TV Shows In Progress', 'list_name': 'Tvshows In Progress', 'info': 'Browse TV Shows that are in the process of being watched.'}, '[B]IN PROGRESS : [/B]TV Shows', iconImage='tv.png')
        self.add_dir({'mode': 'build_in_progress_episode', 'foldername': 'Episodes In Progress', 'list_name': 'Episodes In Progress', 'info': 'Browse Episodes that are in the process of being watched.'}, '[B]IN PROGRESS : [/B]Episodes', iconImage='episode.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def watched(self):
        self.add_dir({'mode': 'build_movie_list', 'action': 'watched_movies', 'foldername': 'Furk It Watched Movies', 'list_name': 'Movies Watched', 'info': 'Browse Movies watched in Furk It.'}, '[B]WATCHED : [/B]Movies', iconImage='movies.png')
        self.add_dir({'mode': 'build_tvshow_list', 'action': 'watched_tvshows', 'foldername': 'Furk It Watched Shows', 'list_name': 'Tvshows Watched', 'info': 'Browse TV Shows watched in Furk It.'}, '[B]WATCHED : [/B]TV Shows', iconImage='tv.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def my_trakt_content(self):
        self.add_dir({'mode': 'navigator.trakt_collection', 'foldername': 'My Trakt Collections', 'list_name': 'Trakt My Collections', 'info': 'Browse your Trakt Collections.'}, '[B]TRAKT: [/B]Collections', iconImage='traktcollection.png')
        self.add_dir({'mode': 'navigator.trakt_watchlist', 'foldername': 'My Trakt Watchlists', 'list_name': 'Trakt My Watchlists', 'info': 'Browse your Trakt Watchlists.'}, '[B]TRAKT: [/B]Watchlists', iconImage='traktwatchlist.png')
        self.add_dir({'mode': 'trakt.get_trakt_my_lists', 'foldername': 'My Trakt Lists', 'list_name': 'Trakt My Lists', 'info': 'Browse your Trakt Lists.'}, '[B]TRAKT: [/B]Lists', iconImage='traktmylists.png')
        self.add_dir({'mode': 'trakt.get_trakt_liked_lists', 'foldername': 'My Trakt Liked Lists', 'list_name': 'Trakt My Liked Lists', 'info': 'Browse your Trakt Liked Lists.'}, '[B]TRAKT: [/B]Liked Lists', iconImage='traktlikedlists.png')
        self.add_dir({'mode': 'navigator.trakt_recommendations', 'foldername': 'My Trakt Recommended Lists', 'list_name': 'Trakt My Recommended Lists', 'info': 'Browse your Trakt Recommended Lists.'}, '[B]TRAKT: [/B]Recommended Lists', iconImage='traktrecommendations.png')
        self.add_dir({'mode': 'trakt.search_trakt_lists', 'foldername': 'Search Trakt Lists', 'list_name': 'Trakt Search Lists', 'info': 'Search Trakt for Lists.'}, '[B]TRAKT: [/B]Search User Lists', iconImage='search_trakt_lists.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def trakt_collection(self):
        self.add_dir({'mode': 'build_movie_list', 'action': 'trakt_collection', 'foldername': 'My Trakt Movie Collection', 'list_name': 'Movies Trakt Collection', 'info': 'Access your Trakt Movie Collection.'}, '[B]COLLECTION: [/B]Movies', iconImage='movies.png')
        self.add_dir({'mode': 'build_tvshow_list', 'action': 'trakt_collection', 'foldername': 'My Trakt TV Show Collection', 'list_name': 'Tvshows Trakt Collection', 'info': 'Access your Trakt TV Show Collection.'}, '[B]COLLECTION: [/B]TV Shows', iconImage='tv.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def trakt_watchlist(self):
        self.add_dir({'mode': 'build_movie_list', 'action': 'trakt_watchlist', 'foldername': 'My Trakt Movie Watchlist', 'list_name': 'Movies Trakt Watchlist', 'info': 'Access your Trakt Movie Watchlist.'}, '[B]WATCHLIST: [/B]Movies', iconImage='movies.png')
        self.add_dir({'mode': 'build_tvshow_list', 'action': 'trakt_watchlist', 'foldername': 'My Trakt TV Show Watchlist', 'list_name': 'Tvshows Trakt Watchlist', 'info': 'Access your Trakt TV Show Watchlist.'}, '[B]WATCHLIST: [/B]TV Shows', iconImage='tv.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def trakt_recommendations(self):
        self.add_dir({'mode': 'build_movie_list', 'action': 'trakt_recommendations', 'foldername': 'My Trakt Movie Recommendations', 'list_name': 'Trakt My Movie Recommendations', 'info': 'Access your Trakt Movie Recommendations.'}, '[B]RECOMMENDATIONS: [/B]Movies', iconImage='movies.png')
        self.add_dir({'mode': 'build_tvshow_list', 'action': 'trakt_recommendations', 'foldername': 'My Trakt TV Show Recommendations', 'list_name': 'Trakt My TV Show Recommendations', 'info': 'Access your Trakt TV Show Recommendations.'}, '[B]RECOMMENDATIONS: [/B]TV Shows', iconImage='tv.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def search(self):
        self.add_dir({'mode': 'build_movie_list', 'action': 'tmdb_movies_search', 'query': 'NA', 'foldername': 'Movies', 'variable': '$INFO[System.TotalUptime]', 'info': 'Search Movies.', 'list_name': 'Search Movies'}, '[B]SEARCH : [/B]Movies', iconImage='search_movie.png')
        self.add_dir({'mode': 'build_tvshow_list', 'action': 'tmdb_tv_search', 'query': 'NA', 'foldername': 'TV Shows', 'variable': '$INFO[System.TotalUptime]', 'info': 'Search TV Shows.', 'list_name': 'Search TV Shows'}, '[B]SEARCH : [/B]TV Shows', iconImage='search_tv.png')
        self.add_dir({'mode': 'build_movie_list', 'action': 'tmdb_movies_people_search', 'query': 'NA', 'foldername': 'People - Movies', 'variable': '$INFO[System.TotalUptime]', 'info': 'Search People (Movies).', 'list_name': 'Search People (Movies)'}, '[B]SEARCH : [/B]People (Movies)', iconImage='search_movies_people.png')
        self.add_dir({'mode': 'build_tvshow_list', 'action': 'tmdb_tv_people_search', 'query': 'NA', 'foldername': 'People - TV Shows', 'variable': '$INFO[System.TotalUptime]', 'info': 'Search People (TV Shows).', 'list_name': 'Search People (TV Shows)'}, '[B]SEARCH : [/B]People (TV Shows)', iconImage='search_tv_shows_people.png')
        self.add_dir({'mode': 'furk.search_furk', 'db_type': 'video', 'foldername': 'Search Furk (Video)', 'variable': '$INFO[System.TotalUptime]', 'info': 'Search Furk Video files.', 'list_name': 'Search Furk (Video)'}, '[B]SEARCH : [/B]Furk (Video)', iconImage='search_furk.png')
        self.add_dir({'mode': 'furk.search_furk', 'db_type': 'audio', 'foldername': 'Search Furk (Audio)', 'variable': '$INFO[System.TotalUptime]', 'info': 'Search Furk Audio files.', 'list_name': 'Search Furk (Audio)'}, '[B]SEARCH : [/B]Furk (Audio)', iconImage='search_furk.png')
        self.add_dir({'mode': 'easynews.search_easynews', 'foldername': 'Search Easynews (Video)', 'variable': '$INFO[System.TotalUptime]', 'info': 'Search Easynews Video files.', 'list_name': 'Search Easynews (Video)'}, '[B]SEARCH : [/B]Easynews (Video)', iconImage='search_easynews.png')
        self.add_dir({'mode': 'search_history', 'action': 'movie', 'foldername': 'Movie Search', 'info': 'Browse Movie Search History.', 'list_name': 'Search History Movies'}, '[B]HISTORY : [/B]Movie Search', iconImage='search.png')
        self.add_dir({'mode': 'search_history', 'action': 'tvshow', 'foldername': 'TV Show Search', 'info': 'Browse TV Show Search History.', 'list_name': 'Search History TV Show Search'}, '[B]HISTORY : [/B]TV Show Search', iconImage='search.png')
        self.add_dir({'mode': 'search_history', 'action': 'furk_video', 'foldername': 'Furk Video Search History', 'info': 'Browse Furk Video Search History.', 'list_name': 'Search History Furk (Video)'}, '[B]HISTORY : [/B]Furk Search (Video)', iconImage='search.png')
        self.add_dir({'mode': 'search_history', 'action': 'furk_audio', 'foldername': 'Furk Audio Search History', 'info': 'Browse Furk Audio Search History.', 'list_name': 'Search History Furk (Audio)'}, '[B]HISTORY : [/B]Furk Search (Audio)', iconImage='search.png')
        self.add_dir({'mode': 'search_history', 'action': 'easynews_video', 'foldername': 'Easynews Video Search History', 'info': 'Browse Easynews Video Search History.', 'list_name': 'Search History Easynews (Video)'}, '[B]HISTORY : [/B]Easynews Search (Video)', iconImage='search.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def tools(self):
        changelog_info = 'Read latest changes to Furk It and Tiki Modules'
        view_modes_info = 'Set Furk It View Modes for all media and lists.'
        next_episode_info = 'Adjust settings related to Furk It Next Episode Function.'
        clear_info = 'Access tools to clear Furk It databases, and other lists includings Favourites, Subscriptions etc.'
        remake_subs_info = 'Remake Furk It .STRM files for Subscriptions.'
        update_subs_info = 'Manually Update all TV Show Subscriptions.'
        trakt_auth_info = 'Authenticate your Trakt account using device pairing. A code will appear which you must enter on the Trakt webpage.'
        trakt_resync_info = 'ReSync Furk It Watched Info with Trakt Watched Info.'
        display_time = '[COLOR=grey]   (%s)[/COLOR]' % str(__addon__.getSetting('service_time'))
        self.add_dir({'mode': 'navigator.changelogs', 'foldername': 'Changelogs', 'list_name': 'Tools Changelogs', 'info': changelog_info}, '[B]TOOLS : [/B]Changelogs', iconImage='settings2.png')
        self.add_dir({'mode': 'navigator.set_view_modes', 'foldername': 'Set Views', 'list_name': 'Tools Set Views', 'info': view_modes_info}, '[B]TOOLS : [/B]Set Views', iconImage='settings2.png')
        self.add_dir({'mode': 'navigator.next_episode_menus', 'foldername': 'Manage Next Episode Options', 'list_name': 'Tools Manage Next Episode Options', 'info': next_episode_info}, '[B]TOOLS : [/B]Manage Next Episode Options', iconImage='settings2.png')
        self.add_dir({'mode': 'navigator.clear_info', 'foldername': 'Clear List and Data Info', 'list_name': 'Tools Clear List and Data Info', 'info': clear_info}, '[B]TOOLS : [/B]Clear List and Data Info', iconImage='settings2.png')
        self.add_dir({'mode': 'remake_subscriptions', 'foldername': 'Remake Furk It Subscriptions Stream Files', 'list_name': 'Tools Remake Furk It Subscriptions Stream Files', 'info': remake_subs_info}, '[B]TOOLS : [/B]Remake Furk It Subscriptions Stream Files', iconImage='settings2.png')
        self.add_dir({'mode': 'update_subscriptions', 'foldername': 'Update Subscriptions', 'list_name': 'Tools Update Subscriptions %s' % display_time, 'info': update_subs_info}, '[B]TOOLS : [/B]Update Subscriptions %s' % display_time, iconImage='settings2.png')
        if settings.watched_indicators() == 1: self.add_dir({'mode': 'trakt_sync_watched_to_furkit', 'refresh': True, 'foldername': 'ReSync Furk It Watched to Trakt Watched', 'list_name': '[B]TOOLS : [/B]ReSync Furk It Watched to Trakt Watched', 'info': trakt_resync_info}, '[B]TRAKT : [/B]ReSync Furk It Watched to Trakt Watched', iconImage='settings2.png')
        self.add_dir({'mode': 'trakt_authenticate', 'foldername': '(Re)Authenticate Trakt', 'list_name': 'Tools (Re)Authenticate Trakt', 'info': trakt_auth_info}, '[B]TRAKT : [/B](Re)Authenticate Trakt', iconImage='settings2.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def settings(self):
        self.add_dir({'mode': 'open_settings', 'query': '0.0', 'foldername': 'General', 'list_name': 'Settings General', 'info': 'Access General Settings.'}, '[B]SETTINGS : [/B]General', iconImage='settings.png')
        self.add_dir({'mode': 'open_settings', 'query': '1.0', 'foldername': 'Accounts', 'list_name': 'Settings Accounts', 'info': 'Access Account Settings.'}, '[B]SETTINGS : [/B]Accounts', iconImage='settings.png')
        self.add_dir({'mode': 'open_settings', 'query': '2.0', 'foldername': 'Next Episodes', 'list_name': 'Settings Next Episodes', 'info': 'Access Next Episodes Settings.'}, '[B]SETTINGS : [/B]Next Episodes', iconImage='settings.png')
        self.add_dir({'mode': 'open_settings', 'query': '3.0', 'foldername': 'Search', 'list_name': 'Settings Search', 'info': 'Access Search Settings.'}, '[B]SETTINGS : [/B]Search', iconImage='settings.png')
        self.add_dir({'mode': 'open_settings', 'query': '4.0', 'foldername': 'Playback', 'list_name': 'Settings Playback', 'info': 'Access Playback Settings.'}, '[B]SETTINGS : [/B]Playback', iconImage='settings.png')
        self.add_dir({'mode': 'open_settings', 'query': '5.0', 'foldername': 'Indicators', 'list_name': 'Settings Indicators', 'info': 'Access Indicators Settings.'}, '[B]SETTINGS : [/B]Indicators', iconImage='settings.png')
        self.add_dir({'mode': 'open_settings', 'query': '6.0', 'foldername': 'Library', 'list_name': 'Settings Library', 'info': 'Access Library Settings.'}, '[B]SETTINGS : [/B]Library', iconImage='settings.png')
        self.add_dir({'mode': 'open_settings', 'query': '7.0', 'foldername': 'Downloads', 'list_name': 'Settings Downloads', 'info': 'Access Downloads Settings.'}, '[B]SETTINGS : [/B]Downloads', iconImage='settings.png')
        self.add_dir({'mode': 'external_settings', 'ext_addon': 'script.module.tikiscrapers', 'foldername': 'Open Tiki Scraper Settings', 'list_name': 'Settings Open Tiki Scraper Settings', 'info': 'Open Tiki Scraper Settings.'}, '[B]EXTERNAL (SCRAPER) : [/B]Open Tiki Scraper Settings', iconImage='settings.png')
        self.add_dir({'mode': 'external_settings', 'ext_addon': 'script.module.tikimeta', 'foldername': 'Open Tiki Meta Settings', 'list_name': 'Settings Open Tiki Meta Settings', 'info': 'Open Tiki Meta Settings.'}, '[B]EXTERNAL (META) : [/B]Open Tiki Meta Settings', iconImage='settings.png')
        self.add_dir({'mode': 'resolveurl_settings', 'foldername': 'Open Resolve URL Settings', 'list_name': 'Settings Open Resolve URL Settings', 'info': 'Open Resolve URL Settings.'}, '[B]RESOLVEURL : [/B]Open Resolve URL Settings', iconImage='settings.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def clear_info(self):
        clear_favourites = 'Clear Furk It Movie - TV Show - Audio Favourites. This cannot be undone.'
        clear_subscriptions = 'Clear Furk It Movie or TV Show Subscriptions. This cannot be undone.'
        clear_search_history = 'Clear Furk It Movie - TV Show - Video or Audio Search History. This cannot be undone.'
        clear_meta_cache = 'Clear Furk It Meta Cache (Movie & TV Show Info and Artwork). This cannot be undone.'
        clear_list_cache = 'Clear Furk It List Cache (Furk It Menu Lists e.g. Trending). This cannot be undone.'
        clear_providers_cache = 'Clear Furk It External Providers Cache (External Scraper Results). This cannot be undone.'
        self.add_dir({'mode': 'clear_favourites', 'foldername': 'Clear Furk It Favourites', 'list_name': 'Tools Clear Furk It Favourites', 'info': clear_favourites}, '[B]CACHE : [/B]Clear Furk It Favourites', iconImage='settings2.png')
        self.add_dir({'mode': 'clear_subscriptions', 'foldername': 'Clear Furk It Subscriptions', 'list_name': 'Tools Clear Furk It Subscriptions', 'info': clear_subscriptions}, '[B]CACHE : [/B]Clear Furk It Subscriptions', iconImage='settings2.png')
        self.add_dir({'mode': 'clear_search_history', 'foldername': 'Clear Search History', 'list_name': 'Tools Clear Search History', 'info': clear_search_history}, '[B]CACHE : [/B]Clear Search History', iconImage='settings2.png')
        self.add_dir({'mode': 'clear_cache', 'cache': 'meta', 'foldername': 'Clear Meta Cache', 'list_name': 'Tools Clear Meta Cache', 'info': clear_meta_cache}, '[B]CACHE : [/B]Clear Meta Cache', iconImage='settings2.png')
        self.add_dir({'mode': 'clear_cache', 'cache': 'list', 'foldername': 'Clear List Cache', 'list_name': 'Tools Clear List Cache', 'info': clear_list_cache}, '[B]CACHE : [/B]Clear List Cache', iconImage='settings2.png')
        self.add_dir({'mode': 'clear_cache', 'cache': 'providers', 'foldername': 'Clear External Providers Cache', 'list_name': 'Tools Clear External Providers Cache', 'info': clear_providers_cache}, '[B]CACHE : [/B]Clear External Providers Cache', iconImage='settings2.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def next_episode_menus(self):
        self.add_dir({'mode': 'build_next_episode_manager', 'action': 'manage_in_progress', 'foldername': 'Manage In Progress Shows', 'exclude_external': 'true', 'info': 'Manage In Progress Shows.'}, '[B]NEXT EPISODE : [/B]Manage In Progress Shows', iconImage='settings.png')
        if settings.watched_indicators() == 0: self.add_dir({'mode': 'build_next_episode_manager', 'action': 'manage_unwatched', 'foldername': 'Manage Unwatched Shows', 'exclude_external': 'true', 'info': 'Manage Unwatched Shows.'}, '[B]NEXT EPISODE : [/B]Manage Unwatched Shows', iconImage='settings.png')
        self.add_dir({'mode': 'next_episode_options_choice', 'setting': 'Sort Type', 'foldername': 'Manage Sort Type', 'exclude_external': 'true', 'info': 'Sort Episodes by Recently Watched, Airdate or Title.'}, '[B]NEXT EPISODE : [/B]Manage Sort Type', iconImage='settings.png')
        self.add_dir({'mode': 'next_episode_options_choice', 'setting': 'Sort Order', 'foldername': 'Manage Sort Order', 'exclude_external': 'true', 'info': 'Arrange Episodes in Ascending or Descending Order.'}, '[B]NEXT EPISODE : [/B]Manage Sort Order', iconImage='settings.png')
        self.add_dir({'mode': 'next_episode_options_choice', 'setting': 'Include Unaired', 'foldername': 'Manage Unaired Episodes', 'exclude_external': 'true', 'info': 'Include or Exclude Unaired Episodes.'}, '[B]NEXT EPISODE : [/B]Manage Unaired Episodes', iconImage='settings.png')
        self.add_dir({'mode': 'next_episode_options_choice', 'setting': 'Include Trakt or Furk It Unwatched', 'foldername': 'Include Include Unwatched TV Shows', 'exclude_external': 'true', 'info': 'Depending on what you have set for Indicators, you can include either the Trakt Watchlist or Assigned Furk It Unwatched TV Shows.'}, '[B]NEXT EPISODE : [/B]Include Unwatched TV Shows', iconImage='settings.png')
        self.add_dir({'mode': 'next_episode_options_choice', 'setting': 'Include Airdate in Title', 'foldername': 'Include Airdate in title', 'exclude_external': 'true', 'info': 'Include or Exclude Airdate Info in the title.'}, '[B]NEXT EPISODE : [/B]Include Airdate in title', iconImage='settings.png')
        self.add_dir({'mode': 'next_episode_options_choice', 'setting': 'Airdate Format', 'foldername': 'Manage Airdate Format', 'exclude_external': 'true', 'info': 'Manage Airdate Format.'}, '[B]NEXT EPISODE : [/B]Manage Airdate Format', iconImage='settings.png')
        self.add_dir({'mode': 'next_episode_color_choice', 'setting': 'Airdate', 'foldername': 'Manage Airdate Color Highlight', 'exclude_external': 'true', 'info': 'Manage Airdate Color Highlight.'}, '[B]NEXT EPISODE : [/B]Manage Airdate Color Highlight', iconImage='settings.png')
        self.add_dir({'mode': 'next_episode_color_choice', 'setting': 'Unaired', 'foldername': 'Manage Unaired Color Highlight', 'exclude_external': 'true', 'info': 'Manage Unaired Color Highlight.'}, '[B]NEXT EPISODE : [/B]Manage Unaired Color Highlight', iconImage='settings.png')
        self.add_dir({'mode': 'next_episode_color_choice', 'setting': 'Unwatched', 'foldername': 'Manage Unwatched Color Highlight', 'exclude_external': 'true', 'info': 'Manage Unwatched Color Highlight.'}, '[B]NEXT EPISODE : [/B]Manage Unwatched Color Highlight', iconImage='settings.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def changelogs(self):
        main_text_file, main_heading = xbmc.translatePath(os.path.join(addon_dir, "changelog.txt")), 'Furk It Changelog'
        scrapers_text_file, scrapers_heading = xbmc.translatePath(os.path.join(xbmc.translatePath(xbmcaddon.Addon(id='script.module.tikiscrapers').getAddonInfo('path')), "changelog.txt")), 'Tiki Scrapers Changelog'
        meta_text_file, meta_heading = xbmc.translatePath(os.path.join(xbmc.translatePath(xbmcaddon.Addon(id='script.module.tikimeta').getAddonInfo('path')), "changelog.txt")), 'Tiki Meta Changelog'
        self.add_dir({'mode': 'show_text', 'text_file': main_text_file, 'heading': main_heading, 'foldername': main_heading, 'list_name': 'Tools %s' % main_heading, 'info': 'Show Furk It Changelog'}, '[B]CHANGELOG : [/B] Furk It', iconImage='lists.png')
        self.add_dir({'mode': 'show_text', 'text_file': scrapers_text_file, 'heading': scrapers_heading, 'foldername': scrapers_heading, 'list_name': 'Tools %s' % scrapers_heading, 'info': 'Show Tiki Scrapers Changelog'}, '[B]CHANGELOG : [/B] Tiki Scrapers', iconImage='lists.png')
        self.add_dir({'mode': 'show_text', 'text_file': meta_text_file, 'heading': meta_heading, 'foldername': meta_heading, 'list_name': 'Tools %s' % meta_heading, 'info': 'Show Tiki Meta Changelog'}, '[B]CHANGELOG : [/B] Tiki Meta', iconImage='lists.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def set_view_modes(self):
        self.add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.main', 'title': 'Set Main List View', 'view_type': 'files', 'exclude_external': 'true', 'info': 'Set Main List View.'},'[B]SET VIEW : [/B]Main List', iconImage='settings.png')
        self.add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.movies', 'title': 'Set Movies View', 'view_type': 'movies', 'exclude_external': 'true', 'info': 'Set Movies View.'},'[B]SET VIEW : [/B]Movies', iconImage='settings.png')
        self.add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.tvshows', 'title': 'Set TV Show View', 'view_type': 'tvshows', 'exclude_external': 'true', 'info': 'Set TV Show View.'},'[B]SET VIEW : [/B]TV Shows', iconImage='settings.png')
        self.add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.seasons', 'title': 'Set Seasons View', 'view_type': 'seasons', 'exclude_external': 'true', 'info': 'Set Seasons View.'},'[B]SET VIEW : [/B]Seasons', iconImage='settings.png')
        self.add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.episodes', 'title': 'Set Episodes View', 'view_type': 'episodes', 'exclude_external': 'true', 'info': 'Set Episodes View.'},'[B]SET VIEW : [/B]Episodes', iconImage='settings.png')
        self.add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.progress_next_episode', 'title': 'Set Progress/Next Episode View', 'view_type': 'episodes', 'exclude_external': 'true', 'info': 'Set Progress/Next Episode View'},'[B]SET VIEW : [/B]Progress/Next Episode', iconImage='settings.png')
        self.add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.trakt_list', 'title': 'Set Trakt Lists View', 'view_type': 'videos', 'exclude_external': 'true', 'info': 'Set Trakt Lists View.'},'[B]SET VIEW : [/B]Trakt Lists', iconImage='settings.png')
        self.add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.media_results', 'title': 'Set Media Results View', 'view_type': 'files', 'exclude_external': 'true', 'info': 'Set Media Results View.'},'[B]SET VIEW : [/B]Media Results', iconImage='settings.png')
        self.add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.pack_results', 'title': 'Set PACK Results View', 'view_type': 'files', 'exclude_external': 'true', 'info': 'Set PACK Results View.'},'[B]SET VIEW : [/B]PACK Results', iconImage='settings.png')
        self.add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.furk_files', 'title': 'Set Furk Files View', 'view_type': 'files', 'exclude_external': 'true', 'info': 'Set Furk Files View.'},'[B]SET VIEW : [/B]Furk Files', iconImage='settings.png')
        self.add_dir({'mode': 'navigator.view_chooser', 'view_setting_id': 'view.easynews_files', 'title': 'Set Easynews Files View', 'view_type': 'files', 'exclude_external': 'true', 'info': 'Set Easynews Files View.'},'[B]SET VIEW : [/B]Easynews Files', iconImage='settings.png')
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def view_chooser(self):
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        self.add_dir({'mode': 'navigator.set_views', 'view_setting_id': params.get('view_setting_id'), 'title': params.get('title'), 'view_type': params.get('view_type'), 'exclude_external': 'true'}, 'Set view and then click here', iconImage='settings.png')
        xbmcplugin.setContent(__handle__, params.get('view_type'))
        xbmcplugin.endOfDirectory(__handle__)
        self._setView(params.get('view_setting_id'))

    def set_views(self):
        from resources.lib.modules.nav_utils import notification
        VIEWS_DB = os.path.join(profile_dir, "views.db")
        settings.check_database(VIEWS_DB)
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        view_type = params.get('view_setting_id')
        view_id = str(xbmcgui.Window(xbmcgui.getCurrentWindowId()).getFocusId())
        dbcon = database.connect(VIEWS_DB)
        dbcon.execute("DELETE FROM views WHERE view_type = '%s'" % (str(view_type)))
        dbcon.execute("INSERT INTO views VALUES (?, ?)", (str(view_type), str(view_id)))
        dbcon.commit()
        notification("%s set to %s" % (params.get('title')[3:], xbmc.getInfoLabel('Container.Viewmode').upper()), time=2000)

    def add_dir(self, url_params, list_name, iconImage='DefaultFolder.png', isFolder=True):
        cm = []
        icon = iconImage if 'network_id' in url_params else os.path.join(self.icon_directory, iconImage)
        info = url_params.get('info', '')
        url_params['iconImage'] = icon
        url = self._build_url(url_params)
        listitem = xbmcgui.ListItem(list_name, iconImage=icon)
        listitem.setArt({'fanart': self.fanart})
        listitem.setInfo('video', {'title': list_name, 'plot': info})
        if not 'exclude_external' in url_params:
            cm.append(("[B]Add this item to a Menu[/B]",'XBMC.RunPlugin(%s)'% self.dump_menu_item(url_params)))
            listitem.addContextMenuItems(cm)
        xbmcplugin.addDirectoryItem(handle=__handle__, url=url, listitem=listitem, isFolder=isFolder)

    def adjust_main_lists(self):
        def db_execute():
            dbcon = database.connect(NAVIGATOR_DB)
            dbcon.execute("DELETE FROM navigator where list_name=? and list_type=?", (list_name, 'edited'))
            dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (list_name, 'edited', json.dumps(li)))
            dbcon.commit()
        def menu_select(heading, position_list=False):
            for item in choice_items:
                line = 'Place [B]%s[/B] below [B]%s[/B]' % (menu_name, item['name']) if position_list else item['info']
                icon = item.get('iconImage') if item.get('network_id', '') != '' else os.path.join(self.icon_directory, item.get('iconImage'))
                listitem = xbmcgui.ListItem(item['name'], line, iconImage=icon)
                choice_list.append(listitem)
            if position_list: choice_list.insert(0, xbmcgui.ListItem('Top Position', 'Place [B]%s[/B] at Top of List' % menu_name, iconImage=os.path.join(self.icon_directory, 'furk.png')))
            return dialog.select(heading, choice_list, useDetails=True)
        from resources.lib.modules.nav_utils import notification
        dialog = xbmcgui.Dialog()
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        menu_name = params.get('menu_name', '')
        list_name = params.get('list_name', '')
        li = None
        method = params.get('method')
        choice_list = []
        try:
            current_position = int(params.get('position', '0'))
            default_list, edited_list = self._db_lists(list_name)
            def_file = default_list if not edited_list else edited_list
            li, def_li = def_file, default_list
            choice_items = [i for i in def_li if i not in li]
        except: pass
        try:
            if method == 'move':
                choice_items = [i for i in li if i['name'] != menu_name]
                new_position = menu_select('Choose New Position of Menu Item (Insert Below Chosen Item)...', position_list=True)
                if new_position < 0 or new_position == current_position: return
                li.insert(new_position, li.pop(current_position))
                db_execute()
            elif method == 'remove':
                li = [x for x in li if x['name'] != menu_name]
                db_execute()
            elif method == 'add':
                selection = menu_select("Choose item to add to menu")
                if selection < 0: return
                selection = choice_items[selection]
                choice_list = []
                choice_items = li
                item_position = menu_select('Choose Insert Position of Menu Item (Insert Below Chosen Item)...', position_list=True)
                if item_position < 0: return
                li.insert((item_position), selection)
                db_execute()
            elif method == 'add_external':
                choice_items = self.select_from_main_menus(params.get('list_name'), params.get('item_name'))
                selection = menu_select("Choose Menu to add %s List Item Into.." % params.get('item_name'))
                if selection < 0: return
                add_to_menu_choice = choice_items[selection]
                list_name = add_to_menu_choice['action']
                default_list, edited_list = self._db_lists(list_name)
                def_file = default_list if not edited_list else edited_list
                li = def_file
                menu_item = self.make_menu_item(params)
                if not menu_item or menu_item in li: return
                choice_list = []
                choice_items = li
                item_position = menu_select('Choose Insert Position of Menu Item (Insert Below Chosen Item)...', position_list=True)
                if item_position < 0: return
                li.insert((item_position), menu_item)
                db_execute()
            elif method == 'add_trakt':
                from resources.lib.modules.trakt import get_trakt_list_selection
                trakt_selection = json.loads(params['trakt_selection']) if 'trakt_selection' in params else get_trakt_list_selection(list_choice=True)
                if not trakt_selection: return
                name = dialog.input('Choose Display Name', type=xbmcgui.INPUT_ALPHANUM, defaultt=trakt_selection['name'])
                if not name: return
                choice_list = []
                choice_items = li
                item_position = menu_select('Choose Insert Position of Menu Item (Insert Below Chosen Item)...', position_list=True)
                if item_position < 0: return
                li.insert(item_position, {"iconImage": "traktmylists.png", "mode": "trakt.build_trakt_list", "name": name, "foldername": name, "user": trakt_selection['user'], "slug": trakt_selection['slug'], 'external_list_item': True, "info": '%s (Trakt List item).' % name})
                db_execute()
            elif method == 'add_trakt_external':
                name = dialog.input('Choose Display Name', type=xbmcgui.INPUT_ALPHANUM, defaultt=params['name'])
                if not name: return
                if not li:
                    choice_items = self.select_from_main_menus()
                    selection = menu_select("Choose Menu to add %s  Into.." % name)
                    if selection < 0: return
                    add_to_menu_choice = choice_items[selection]
                    list_name = add_to_menu_choice['action']
                    default_list, edited_list = self._db_lists(list_name)
                    li = default_list if not edited_list else edited_list
                if name in [i['name'] for i in li]: return
                choice_list = []
                choice_items = li
                item_position = 0 if len(li) == 0 else menu_select('Choose Insert Position of Menu Item (Insert Below Chosen Item)...', position_list=True)
                if item_position < 0: return
                li.insert(item_position, {"iconImage": "traktmylists.png", "mode": "trakt.build_trakt_list", "name": name, "foldername": name, "user": params['user'], "slug": params['slug'], 'external_list_item': True, "info": '%s (Trakt List item).' % name})
                db_execute()
            elif method == 'browse':
                heading = "Choose Removed Item to Browse Into.."
                selection = menu_select(heading)
                if selection < 0: return
                mode, action, url_mode, menu_type, query = choice_items[selection]['mode'] if 'mode' in choice_items[selection] else '', choice_items[selection]['action'] if 'action' in choice_items[selection] else '', choice_items[selection]['url_mode'] if 'url_mode' in choice_items[selection] else '', choice_items[selection]['menu_type'] if 'menu_type' in choice_items[selection] else '', choice_items[selection]['query'] if 'query' in choice_items[selection] else ''
                xbmc.executebuiltin("XBMC.Container.Update(%s)" % self._build_url({'mode': mode, 'action': action, 'url_mode': url_mode, 'menu_type': menu_type, 'query': query}))
            elif method == 'reload_menu_item':
                default = eval('DefaultMenus().%s()' % list_name)
                default_item = [i for i in default if i['name'] == menu_name][0]
                li = [default_item if x['name'] == menu_name else x for x in def_file]
                list_type = 'edited' if self._db_lists(list_name)[1] else 'default'
                dbcon = database.connect(NAVIGATOR_DB)
                dbcon.execute("DELETE FROM navigator where list_name=? and list_type=?", (list_name, list_type))
                dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (list_name, list_type, json.dumps(li)))
                dbcon.commit()
            elif method == 'restore':
                confirm = dialog.yesno('Are you sure?', 'Continuing will load the default Menu.')
                if not confirm: return
                dbcon = database.connect(NAVIGATOR_DB)
                for item in ['edited', 'default']: dbcon.execute("DELETE FROM navigator where list_name=? and list_type=?", (list_name, item))
                dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (list_name, 'default', json.dumps(eval('DefaultMenus().%s()' % list_name))))
                dbcon.commit()
            if not method in ('browse'):
                    xbmc.executebuiltin('Container.Refresh')
                    notification("Process Successful", time=1500)
        except: return

    def build_main_lists(self):
        from resources.lib.modules import workers
        def make_listing(item_position, item):
            try:
                cm = []
                info = item.get('info', '')
                name = item.get('name', '')
                icon = item.get('iconImage') if item.get('network_id', '') != '' else os.path.join(self.icon_directory, item.get('iconImage'))
                url_params = {'mode': item.get('mode', ''), 'action': item.get('action', ''),
                    'query': item.get('query', ''), 'foldername': item.get('foldername', ''),
                    'url_mode': item.get('url_mode', ''), 'menu_type': item.get('menu_type', ''),
                    'user': item.get('user', ''), 'slug': item.get('slug', ''), 'type': item.get('db_type', ''),
                    'certification': item.get('certification', ''), 'language': item.get('language', ''),
                    'year': item.get('year', ''), 'genre_id': item.get('genre_id', ''), 'iconImage': icon,
                    'network_id': item.get('network_id', ''), 'period': item.get('period', ''),
                    'duration': item.get('duration', ''), 'final_mode': item.get('final_mode', ''),
                    'db_type': item.get('db_type', ''), 'refresh': item.get('refresh', ''),
                    'heading': item.get('heading', ''), 'text_file': item.get('text_file', '')}
                url = self._build_url(url_params)
                cm.append(("[B]Edit Menu[/B]",'XBMC.RunPlugin(%s)' % self._build_url(
                    {'mode': 'navigator.edit_menu', 'default_menu': self.default_menu, 'menu_item': item,
                    'edited_list': self.edited_list, 'list_name': self.list_name, 'menu_name': name,
                    'position': item_position, 'list_is_full': list_is_full, 'list_slug': item.get('slug', '')})))
                if not list_is_full:
                    cm.append(("[B]Browse Removed item[/B]",'XBMC.RunPlugin(%s)' % \
                    self._build_url({'mode': 'navigator.adjust_main_lists', 'method': 'browse', 'list_name': self.list_name, 'position': item_position})))
                listitem = xbmcgui.ListItem(name, thumbnailImage=icon)
                listitem.setArt({'fanart': self.fanart})
                listitem.setInfo('video', {'title': name, 'plot': info})
                listitem.addContextMenuItems(cm)
                item_list.append({'list_item': (url, listitem, True), 'item_position': item_position})
            except: return
        self.default_list, self.edited_list = self._db_lists()
        self.default_menu = self.default_list if not self.edited_list else self.edited_list
        current_items_from_default = [i for i in self.default_menu if not i.get('external_list_item', False)]
        list_is_full = True if len(current_items_from_default) >= len(self.default_list) else False
        item_list = []
        threads = []
        for item_position, item in enumerate(self.default_menu): threads.append(workers.Thread(make_listing, item_position, item))
        [i.start() for i in threads]
        [i.join() for i in threads]
        item_list = sorted(item_list, key=lambda k: k['item_position'])
        xbmcplugin.addDirectoryItems(__handle__, [i['list_item'] for i in item_list])
        xbmcplugin.endOfDirectory(__handle__)
        self._setView()

    def edit_menu(self):
        from resources.lib.modules.utils import selection_dialog
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        default_menu = params.get('default_menu')
        edited_list = params.get('edited_list')
        list_name = params.get('list_name')
        menu_name = params.get('menu_name')
        position = params.get('position')
        list_is_full = eval(params.get('list_is_full', 'False'))
        list_slug = params.get('list_slug', '')
        menu_item = eval(params.get('menu_item'))
        menu_item['list_name'] = list_name
        string = 'Edit %s...' % list_name
        listing = []
        if len(default_menu) != 1:
            listing += [("Move this item to a different position in the list", 'move')]
            listing += [("Remove this item from the list", 'remove')]
        listing += [("Add this item to a different Menu list", 'add_external')]
        if list_name in ('RootList', 'MovieList', 'TVShowList'): listing += [("Add a Trakt list to this Menu", 'add_trakt')]
        if not list_is_full: listing += [("Re-add a removed item from this Menu", 'add_original')]
        if edited_list: listing += [("Restore this Menu to default", 'restore')]
        if not list_slug: listing += [("Reload this item", 'reload')]
        if list_slug: listing += [("Add this Trakt list to Furk It Subscriptions", 'trakt_subscriptions')]
        choice = selection_dialog([i[0] for i in listing], [i[1] for i in listing], string)
        if choice in (None, 'save_and_exit'): return
        elif choice == 'move': url = self._build_url({'mode': 'navigator.adjust_main_lists', 'method': 'move', 'list_name': list_name, 'menu_name': menu_name, 'position': position})
        elif choice == 'remove': url = self._build_url({'mode': 'navigator.adjust_main_lists', 'method': 'remove', 'list_name': list_name, 'menu_name': menu_name, 'position': position})
        elif choice == 'add_original': url = self._build_url({'mode': 'navigator.adjust_main_lists', 'method': 'add', 'list_name': list_name, 'position': position})
        elif choice == 'restore': url = self._build_url({'mode': 'navigator.adjust_main_lists', 'method': 'restore', 'list_name': list_name, 'position': position})
        elif choice == 'add_external': url = self.dump_menu_item(menu_item)
        elif choice == 'add_trakt': url = self._build_url({'mode': 'navigator.adjust_main_lists', 'method': 'add_trakt', 'list_name': list_name, 'position': position})
        elif choice == 'trakt_subscriptions': url = self._build_url({'mode': 'trakt.add_list_to_subscriptions', 'user': menu_item.get('user', ''), 'list_slug': list_slug})
        elif choice == 'reload': url = self._build_url({'mode': 'navigator.adjust_main_lists', 'method': 'reload_menu_item', 'list_name': list_name, 'menu_name': menu_name, 'position': position})
        xbmc.executebuiltin('RunPlugin(%s)' % url)

    def select_from_main_menus(self, current_list=[], item_list=[]):
        include_list = DefaultMenus().DefaultMenuItems()
        menus = DefaultMenus().RootList()
        menus.insert(0, {'info': 'Furk It Root Menu.', 'name': 'Root', 'iconImage': 'furk.png', 'foldername': 'Root', 'mode': 'navigator.main', 'action': 'RootList'})
        include_list = [i for i in include_list if i != current_list]
        menus = [i for i in menus if i.get('action', None) in include_list and not i.get('name') == item_list]
        return menus

    def make_menu_item(self, params):
        dialog = xbmcgui.Dialog()
        name_append_list = [('RootList', ''), ('MovieList', 'Movies '), ('TVShowList', 'Tvshows '), ('AudioList', 'Audio ')]
        orig_name = params.get('list_name', None)
        try: name = '%s%s' % ([i[1] for i in name_append_list if i[0] == orig_name][0], params.get('item_name'))
        except: name = orig_name
        name = dialog.input('Choose Display Name', type=xbmcgui.INPUT_ALPHANUM, defaultt=name)
        if not name: return
        return {'info': params.get('item_info', ''), 'name': name, 'iconImage': params.get('item_iconImage', ''),
            'mode': params.get('item_mode', ''), 'action': params.get('item_action', ''),
            'query': params.get('item_query', ''), 'foldername': params.get('item_foldername', ''),
            'url_mode': params.get('item_url_mode', ''), 'menu_type': params.get('item_menu_type', ''),
            'user': params.get('item_user', ''), 'slug': params.get('item_slug', ''),
            'type': params.get('item_db_type', ''), 'external_list_item': True, 'year': params.get('item_year', ''),
            'certification': params.get('item_certification', ''), 'language': params.get('item_language', ''),
            'genre_id': params.get('item_genre_id', ''), 'network_id': params.get('item_network_id', ''),
            'period': params.get('item_period', ''), 'duration': params.get('item_duration', ''),
            'final_mode': params.get('item_final_mode', ''), 'db_type': params.get('item_db_type', ''),
            'refresh': params.get('item_refresh', ''), 'heading': params.get('item_heading', ''),
            'text_file': params.get('item_text_file', '')}

    def dump_menu_item(self, menu_item):
        list_name = menu_item['list_name'] if 'list_name' in menu_item else self.list_name
        url_params = {'mode': 'navigator.adjust_main_lists ', 'method': 'add_external', 'list_name': list_name,
            'item_mode': menu_item.get('mode', ''), 'item_action': menu_item.get('action', ''),
            'item_query': menu_item.get('query', ''), 'item_foldername': menu_item.get('foldername', ''),
            'item_info': menu_item.get('info', ''), 'item_url_mode': menu_item.get('url_mode', ''),
            'item_menu_type': menu_item.get('menu_type', ''), 'item_user': menu_item.get('user', ''),
            'item_slug': menu_item.get('slug', ''), 'item_db_type': menu_item.get('db_type', ''),
            'item_name': menu_item.get('name', ''), 'item_iconImage': menu_item.get('iconImage', ''),
            'item_certification': menu_item.get('certification', ''), 'item_language': menu_item.get('language', ''),
            'item_year': menu_item.get('year', ''), 'item_genre_id': menu_item.get('genre_id', ''),
            'item_network_id': menu_item.get('network_id', ''),'item_period': menu_item.get('period', ''),
            'item_duration': menu_item.get('duration', ''), 'item_final_mode': menu_item.get('final_mode', ''),
            'item_refresh': menu_item.get('refresh', ''), 'item_heading': menu_item.get('heading', ''),
            'item_text_file': menu_item.get('text_file', '')}
        return self._build_url(url_params)

    def _build_url(self, query):
        return __url__ + '?' + urllib.urlencode(query)

    def _setView(self, view=None):
        try:
            try: from sqlite3 import dbapi2 as database
            except: from pysqlite2 import dbapi2 as database
            view_type = self.view if not view else view
            VIEWS_DB = os.path.join(profile_dir, "views.db")
            settings.check_database(VIEWS_DB)
            dbcon = database.connect(VIEWS_DB)
            dbcon.row_factory = database.Row
            dbcur = dbcon.cursor()
            dbcur.execute("SELECT view_id FROM views WHERE view_type = ?", (str(view_type),))
            view_id = dbcur.fetchone()[0]
            xbmc.sleep(250)
            xbmc.executebuiltin("Container.SetViewMode(%s)" % str(view_id))
        except: pass

    def _db_lists(self, list_name=None):
        list_name = self.list_name if not list_name else list_name
        if not xbmcvfs.exists(NAVIGATOR_DB):
            settings.initialize_databases()
            self._build_database()
        dbcon = database.connect(NAVIGATOR_DB)
        dbcur = dbcon.cursor()
        dbcur.execute("SELECT list_contents FROM navigator WHERE list_name = ? AND list_type = ?", (str(list_name), 'default'))
        default_contents = json.loads(dbcur.fetchone()[0])
        if len(default_contents) != len(eval('DefaultMenus().%s()' % list_name)):
            self._rebuild_single_database(dbcon, list_name)
            dbcur.execute("SELECT list_contents FROM navigator WHERE list_name = ? AND list_type = ?", (str(list_name), 'default'))
            default_contents = json.loads(dbcur.fetchone()[0])
        dbcur.execute("SELECT list_contents FROM navigator WHERE list_name = ? AND list_type = ?", (str(list_name), 'edited'))
        try: edited_contents = json.loads(dbcur.fetchone()[0])
        except: edited_contents = None
        return default_contents, edited_contents

    def _rebuild_single_database(self, dbcon, list_name):
        dbcon.execute("DELETE FROM navigator WHERE list_type=? and list_name=?", ('default', list_name))
        dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (list_name, 'default', json.dumps(eval('DefaultMenus().%s()' % list_name))))
        dbcon.commit()

    def _build_database(self):
        default_menus = DefaultMenus().DefaultMenuItems()
        dbcon = database.connect(NAVIGATOR_DB)
        for content in default_menus:
            dbcon.execute("INSERT INTO navigator VALUES (?, ?, ?)", (content, 'default', json.dumps(eval('DefaultMenus().%s()' % content))))
        dbcon.commit()
