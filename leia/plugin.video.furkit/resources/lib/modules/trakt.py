# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import os, sys
import requests
from urlparse import parse_qsl
import time
from resources.lib.modules.nav_utils import cache_object, build_url, setView, add_dir, notification
from resources.lib.modules.utils import to_utf8
from resources.lib.modules import settings
# from resources.lib.modules.utils import logger

__addon_id__ = 'plugin.video.furkit'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
addon_dir = xbmc.translatePath(__addon__.getAddonInfo('path'))
profile_dir = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])
dialog = xbmcgui.Dialog()
icon_directory = settings.get_theme()
fanart = os.path.join(addon_dir, "fanart.png")
my_list_icon = os.path.join(icon_directory, 'traktmylists.png')
liked_list_icon = os.path.join(icon_directory, 'traktlikedlists.png')

API_ENDPOINT = "https://api-v2launch.trakt.tv"
CLIENT_ID = "1038ef327e86e7f6d39d80d2eb5479bff66dd8394e813c5e0e387af0f84d89fb"
CLIENT_SECRET = "8d27a92e1d17334dae4a0590083a4f26401cb8f721f477a79fd3f218f8534fd1"
LIST_PRIVACY_IDS = ('private', 'friends', 'public')

def call_trakt(path, params={}, data=None, is_delete=False, with_auth=True, method=None, pagination=False, page=1):
    params = dict([(k, to_utf8(v)) for k, v in params.items() if v])
    
    headers = {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': CLIENT_ID
    }
    def send_query():
        if with_auth:
            try:
                expires_at = __addon__.getSetting('trakt_expires_at')
                if time.time() > expires_at:
                    trakt_refresh_token()
            except:
                pass
                
            token = __addon__.getSetting('trakt_access_token')
            if token:
                headers['Authorization'] = 'Bearer ' + token
        if method:
            if method == 'post':
                return requests.post("{0}/{1}".format(API_ENDPOINT, path), headers=headers)
            elif method == 'delete':
                return requests.delete("{0}/{1}".format(API_ENDPOINT, path), headers=headers)
            elif method == 'sort_by_headers':
                return requests.get("{0}/{1}".format(API_ENDPOINT, path), params, headers=headers)

        elif data is not None:
            assert not params
            return requests.post("{0}/{1}".format(API_ENDPOINT, path), json=data, headers=headers)
        elif is_delete:
            return requests.delete("{0}/{1}".format(API_ENDPOINT, path), headers=headers)
        else:
            return requests.get("{0}/{1}".format(API_ENDPOINT, path), params, headers=headers)

    def paginated_query(page):
        lists = []
        params['page'] = page
        results = send_query()
        if with_auth and results.status_code == 401 and dialog.yesno(_("Authenticate Trakt"), _(
                "You must authenticate with Trakt. Do you want to authenticate now?")) and trakt_authenticate():
            response = paginated_query()
            return response
        else: pass
        results.raise_for_status()
        results.encoding = 'utf-8'
        lists.extend(results.json())
        return lists, results.headers["X-Pagination-Page-Count"]

    if pagination == False:
        response = send_query()
        if with_auth and response.status_code == 401 and dialog.yesno(("Authenticate Trakt"), (
                "You must authenticate with Trakt. Do you want to authenticate now?")) and trakt_authenticate():
            response = send_query()
        else: pass
        response.raise_for_status()
        response.encoding = 'utf-8'
        if method == 'sort_by_headers':
            result = response.json()
            headers = response.headers
            if 'X-Sort-By' in headers and 'X-Sort-How' in headers:
                from resources.lib.modules.utils import sort_list
                result = sort_list(headers['X-Sort-By'], headers['X-Sort-How'], result)
            try: return result
            except: return
        try: return response.json()
        except: return
    else:
        (response, numpages) = paginated_query(page)
        return response, numpages
            
def trakt_get_device_code():
    data = { 'client_id': CLIENT_ID }
    return call_trakt("oauth/device/code", data=data, with_auth=False)

def trakt_get_device_token(device_codes):
    data = {
        "code": device_codes["device_code"],
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    start = time.time()
    expires_in = device_codes["expires_in"]
    progress_dialog = xbmcgui.DialogProgress()
    progress_dialog.create(
        ("Authenticate Trakt"), 
        ("Please go to [B]https://trakt.tv/activate[/B] and enter the code"),
        "[B]%s[/B]" % str(device_codes["user_code"])
    )
    try:
        time_passed = 0
        while not xbmc.abortRequested and not progress_dialog.iscanceled() and time_passed < expires_in:            
            try:
                response = call_trakt("oauth/device/token", data=data, with_auth=False)
            except requests.HTTPError, e:
                if e.response.status_code != 400:
                    raise e
                
                progress = int(100 * time_passed / expires_in)
                progress_dialog.update(progress)
                xbmc.sleep(max(device_codes["interval"], 1)*1000)
            else:
                return response
                
            time_passed = time.time() - start
            
    finally:
        progress_dialog.close()
        del progress_dialog
        
    return None

def trakt_refresh_token():
    data = {        
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "grant_type": "refresh_token",
        "refresh_token": __addon__.getSetting('trakt_refresh_token')
    }
    response = call_trakt("oauth/token", data=data, with_auth=False)
    if response:
        __addon__.setSetting('trakt_access_token', response["access_token"])
        __addon__.setSetting('trakt_refresh_token', response["refresh_token"])

def trakt_authenticate():
    code = trakt_get_device_code()
    token = trakt_get_device_token(code)
    trakt_icon = os.path.join(icon_directory, 'trakt.png')
    if token:
        expires_at = time.time() + 60*60*24*30
        __addon__.setSetting('trakt_expires_at', str(expires_at))
        __addon__.setSetting('trakt_access_token', token["access_token"])
        __addon__.setSetting('trakt_refresh_token', token["refresh_token"])
        __addon__.setSetting('trakt_indicators_active', 'true')
        __addon__.setSetting('watched_indicators', '1')
        xbmc.sleep(1000)
        try:
            user = call_trakt("/users/me", with_auth=True)
            __addon__.setSetting('trakt_user', str(user['username']))
        except: pass
        notification('Trakt Account Authorized', 3000, trakt_icon)
        return True
    notification('Trakt Error Authorizing', 3000, trakt_icon)
    return False

def trakt_remove_authentication():
    data = {"token": __addon__.getSetting('trakt_access_token')}
    response = call_trakt("oauth/revoke", data=data, with_auth=False)
    __addon__.setSetting('trakt_user', '')
    __addon__.setSetting('trakt_expires_at', '')
    __addon__.setSetting('trakt_access_token', '')
    __addon__.setSetting('trakt_refresh_token', '')
    __addon__.setSetting('trakt_indicators_active', 'false')
    __addon__.setSetting('watched_indicators', '0')
    notification('Trakt Account Authorization Reset', 3000)

def trakt_get_hidden_items(list_type):
    return call_trakt("users/hidden/{0}".format(list_type))

def trakt_watched_unwatched(action, media, media_id, season=None, episode=None):
    url = "sync/history" if action == 'mark_as_watched' else "sync/history/remove"
    if media == 'episode': data = {"shows": [{'ids': {'imdb': media_id}, "seasons": [{"number": int(season), "episodes": [{"number": int(episode)}]}]}]}
    elif media == 'movies': data = {"%s" % media: [{'ids': {'tmdb': media_id}}]}
    elif media =='shows': data = {"%s" % media: [{'ids': {'imdb': media_id}}]}
    elif media == 'season': data = {"shows": [{'ids': {'imdb': media_id}, "seasons": [{"number": int(season)}]}]}
    return call_trakt(url, data=data)

def trakt_collection(db_type, page_no, letter, passed_list=[]):
    import ast
    from resources.lib.modules.nav_utils import paginate_list
    from resources.lib.modules.utils import title_key
    limit = 40
    key, action = ('movie', get_trakt_movie_id) if db_type == 'movies' else ('show', get_trakt_tvshow_id)
    if not passed_list:
        data = call_trakt("sync/collection/{0}?extended=full".format(db_type), method='sort_by_headers')
        data = sorted(data, key=lambda k: title_key(k[key]['title']))
        original_list = [{'media_id': action(i), 'title': i[key]['title']} for i in data]
    else: original_list = ast.literal_eval(passed_list)
    paginated_list, total_pages = paginate_list(original_list, page_no, letter, limit)
    return paginated_list, original_list, total_pages, limit

def trakt_watchlist(db_type, page_no, letter, passed_list=[]):
    import ast
    from resources.lib.modules.nav_utils import paginate_list
    from resources.lib.modules.utils import title_key
    limit = 40
    key, action = ('movie', get_trakt_movie_id) if db_type == 'movies' else ('show', get_trakt_tvshow_id)
    if not passed_list:
        data = call_trakt("sync/watchlist/{0}?extended=full".format(db_type), method='sort_by_headers')
        data = sorted(data, key=lambda k: title_key(k[key]['title']))
        original_list = [{'media_id': action(i), 'title': i[key]['title']} for i in data]
    else: original_list = ast.literal_eval(passed_list)
    paginated_list, total_pages = paginate_list(original_list, page_no, letter, limit)
    return paginated_list, original_list, total_pages, limit

def add_to_list(username, slug, data):
    result = call_trakt("/users/{0}/lists/{1}/items".format(username, slug), data = data)
    if result['added']['shows'] > 0 or result['added']['movies'] > 0: notification('Item added to Trakt List', 3000)
    else: notification('Error adding item to Trakt List', 3000)
    return result

def remove_from_list(username, slug, data):
    result = call_trakt("/users/{0}/lists/{1}/items/remove".format(username, slug), data=data)
    if result['deleted']['shows'] > 0 or result['deleted']['movies'] > 0:
        notification('Item removed from Trakt List', 3000)
        xbmc.executebuiltin("Container.Refresh")
    else: notification('Error removing item from Trakt List', 3000)
    return result

def add_to_watchlist(data):
    result = call_trakt("/sync/watchlist", data=data)
    if result['added']['movies'] > 0 or result['added']['shows'] > 0: notification('Item added to Trakt Watchlist', 6000)
    else: notification('Error adding item to Trakt Watchlist', 3000)
    return result

def remove_from_watchlist(data):
    result = call_trakt("/sync/watchlist/remove", data=data)
    if result['deleted']['movies'] > 0 or result['deleted']['shows'] > 0:
        notification('Item removed Trakt Watchlist', 3000)
        xbmc.executebuiltin("Container.Refresh")
    else: notification('Error removing item from Trakt Watchlist', 3000)
    return result

def add_to_collection(data):
    result = call_trakt("/sync/collection", data=data)
    if result['added']['movies'] > 0 or result['added']['episodes'] > 0: notification('Item added to Trakt Collection', 6000)
    else: notification('Error adding item to Trakt Collection', 3000)
    return result

def remove_from_collection(data):
    result = call_trakt("/sync/collection/remove", data=data)
    if result['deleted']['movies'] > 0 or result['deleted']['episodes'] > 0:
        notification('Item removed Trakt Collection', 3000)
        xbmc.executebuiltin("Container.Refresh")
    else: notification('Error removing item from Trakt Collection', 3000)
    return result
    
def trakt_get_next_episodes(include_hidden=False):
    from resources.lib.modules.workers import Thread
    from resources.lib.modules.nav_utils import cache_object
    threads = []
    items = []
    def process(item):
        string = 'trakt_view_history_%s' % str(item["show"]["ids"]["trakt"])
        url = {'path': "shows/%s/progress/watched", "path_insert": item["show"]["ids"]["trakt"], "params": {'extended':'full,noseasons'}, "with_auth": True, "pagination": False}
        response = cache_object(get_trakt, string, url, False, .5)
        if response["last_episode"]:
            last_episode = response["last_episode"]
            last_episode["show"] = item["show"]
            last_episode["show"]["last_watched_at"] = item["last_watched_at"]
            items.append(last_episode)
    url = {'path': "users/me/watched/shows?extended=full%s", "with_auth": True, "pagination": False}
    shows = get_trakt_watched_tv(url)
    hidden_data = trakt_get_hidden_items("progress_watched")
    if include_hidden:
        all_shows = [str(get_trakt_tvshow_id(i)) for i in shows]
        hidden_shows = [str(get_trakt_tvshow_id(i)) for i in hidden_data if i["type"] == "show"]
        return all_shows, hidden_shows
    hidden_shows = [i["show"]["ids"]["trakt"] for i in hidden_data if i["type"] == "show"]
    shows = [i for i in shows if i['show']['ids']['trakt'] not in hidden_shows]
    for item in shows: threads.append(Thread(process, item))
    [i.start() for i in threads]
    [i.join() for i in threads]
    return items

def hide_unhide_trakt_items(action, db_type, media_id, section):
    db_type = 'movies' if db_type in ['movie', 'movies'] else 'shows'
    key = 'tmdb' if db_type == 'movies' else 'imdb'
    url = "users/hidden/{}".format(section) if action == 'hide' else "users/hidden/{}/remove".format(section)
    data = {db_type: [{'ids': {key: media_id}}]}
    result = call_trakt(url, data=data)
    xbmc.sleep(500)
    xbmc.executebuiltin("Container.Refresh")

def hide_recommendations(db_type='', imdb_id=''):
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    db_type = params.get('db_type') if 'db_type' in params else db_type
    imdb_id = params.get('imdb_id') if 'imdb_id' in params else imdb_id
    result = call_trakt("/recommendations/{0}/{1}".format(db_type, imdb_id), method='delete')
    notification('Item hidden from Trakt Recommendations', 3000)
    xbmc.sleep(500)
    xbmc.executebuiltin("Container.Refresh")
    return result

def make_new_trakt_list():
    import urllib
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    mode = params.get('mode')
    list_title = dialog.input("Name New List", type=xbmcgui.INPUT_ALPHANUM)
    if not list_title: return
    list_name = urllib.unquote(list_title)
    data = {'name': list_name, 'privacy': 'private', 'allow_comments': False}
    call_trakt("users/me/lists", data=data)
    notification('{}'.format('Trakt list Created', 3000))
    xbmc.executebuiltin("Container.Refresh")

def delete_trakt_list():
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    user = params.get('user')
    list_slug = params.get('list_slug')
    confirm = dialog.yesno('Are you sure?', 'Continuing will delete this Trakt List')
    if confirm == True:
        url = "users/{0}/lists/{1}".format(user, list_slug)
        call_trakt(url, is_delete=True)
        xbmc.executebuiltin("Container.Refresh")
        notification('List removed from Trakt', 3000)
    else: return

def search_trakt_lists():
    try:
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        mode = params.get('mode')
        page = params.get('new_page') if 'new_page' in params else '1'
        search_title = params.get('search_title') if 'search_title' in params else dialog.input("Search Trakt Lists", type=xbmcgui.INPUT_ALPHANUM)
        if not search_title: return
        lists, pages = call_trakt("search", params={'type': "list", 'query': search_title, 'limit': 25}, pagination= True, page = page)
        for item in lists:
            cm = []
            if "list" in item: list_info = item["list"]
            else: return
            try: description = list_info["description"]
            except: decription = ''
            url_params = {'mode': 'trakt.build_trakt_list', 'user': list_info["username"], 'slug': list_info["ids"]["slug"]}
            url = build_url(url_params)
            display = '[B]' + list_info["name"] + '[/B] - [I]by ' + list_info["username"] + ' - ' + str(list_info["item_count"]) + ' items[/I]'
            listitem = xbmcgui.ListItem(display)
            listitem.setArt({'thumb': os.path.join(icon_directory, "search_trakt_lists.png"), 'fanart': fanart})
            cm.append(("Like this List",'XBMC.RunPlugin(%s?mode=%s&user=%s&list_slug=%s)' \
                % (__url__, 'trakt.trakt_like_a_list', list_info["username"], list_info["ids"]["slug"])))
            cm.append(("Add List to Subscriptions",'XBMC.RunPlugin(%s?mode=%s&user=%s&list_slug=%s)' \
                % (__url__, 'trakt.add_list_to_subscriptions', list_info["username"], list_info["ids"]["slug"])))
            listitem.setInfo('video', {'plot': description})
            listitem.addContextMenuItems(cm, replaceItems=False)
            xbmcplugin.addDirectoryItems(handle=__handle__, items=[(url, listitem, True)])
        if pages > page:
            new_page = int(page) + 1
            add_dir({'mode': mode, 'search_title': search_title, 'new_page': str(new_page),
                'foldername': mode}, 'Next Page >>', iconImage='item_next.png')
    except: pass
    xbmcplugin.setContent(__handle__, 'video')
    xbmcplugin.endOfDirectory(__handle__)
    setView('view.main')

def trakt_add_to_list():
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    tmdb_id = int(params.get('tmdb_id'))
    imdb_id = params.get('imdb_id')
    db_type = params.get('db_type')
    key, media_key, media_id = ('movies', 'tmdb', tmdb_id) if db_type == 'movie' else ('shows', 'imdb', imdb_id)
    selected = get_trakt_list_selection()
    if selected is not None:
        data = {key: [{"ids": {media_key: media_id}}]}
        if selected['user'] == 'Watchlist':
            add_to_watchlist(data)
        elif selected['user'] == 'Collection':
            add_to_collection(data)
        else:
            user = selected['user']
            slug = selected['slug']
            add_to_list(user, slug, data)

def trakt_remove_from_list():
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    tmdb_id = int(params.get('tmdb_id'))
    imdb_id = params.get('imdb_id')
    db_type = params.get('db_type')
    key, media_key, media_id = ('movies', 'tmdb', tmdb_id) if db_type == 'movie' else ('shows', 'imdb', imdb_id)
    selected = get_trakt_list_selection()
    if selected is not None:
        data = {key: [{"ids": {media_key: media_id}}]}
        if selected['user'] == 'Watchlist':
            remove_from_watchlist(data)
        elif selected['user'] == 'Collection':
            remove_from_collection(data)
        else:
            user = selected['user']
            slug = selected['slug']
            remove_from_list(user, slug, data)

def trakt_like_a_list():
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    user = params.get('user')
    list_slug = params.get('list_slug')
    try:
        call_trakt("/users/{0}/lists/{1}/like".format(user, list_slug), method='post')
        notification('List Item Liked', 3000)
    except: notification('{}'.format('Trakt Error Unliking List', 3000))

def trakt_unlike_a_list():
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    user = params.get('user')
    list_slug = params.get('list_slug')
    try:
        call_trakt("/users/{0}/lists/{1}/like".format(user, list_slug), method='delete')
        notification('List Item Unliked', 4500)
        xbmc.executebuiltin("Container.Refresh")
    except: notification('{}'.format('Trakt Error Unliking List', 3000))

def get_trakt_list_selection(list_choice=False):
    my_lists = []
    liked_lists = []
    name = '%s%s'
    [my_lists.append({'name': item["name"], 'display': name % (('[B]PERSONAL:[/B] ' if list_choice else ''), item["name"]), 'user': item["user"]["username"], 'slug': item["ids"]["slug"]}) for item in call_trakt("users/me/lists")]
    my_lists = sorted(my_lists, key=lambda k: k['name'])
    if not list_choice: my_lists.insert(0, {'name': 'Collection', 'display': 'Collection ', 'user': 'Collection', 'slug': 'Collection'})
    if not list_choice: my_lists.insert(0, {'name': 'Watchlist', 'display': 'Watchlist ',  'user': 'Watchlist', 'slug': 'Watchlist'})
    if list_choice:
        [liked_lists.append({'name': item["list"]["name"], 'display': name % ('[B]LIKED:[/B] ', item["list"]["name"]), 'user': item["list"]["user"]["username"], 'slug': item["list"]["ids"]["slug"]}) for item in call_trakt("users/likes/lists", params={'limit': 50}, pagination=True, page='1')[0]]
        liked_lists = sorted(liked_lists, key=lambda k: (k['display']))
        my_lists.extend(liked_lists)
    selection = dialog.select("Select list", [l["display"] for l in my_lists])
    if selection >= 0: return my_lists[selection]
    else: return None

def get_trakt_my_lists():
    try:
        lists = call_trakt("users/me/lists")
        for item in lists:
            cm = []
            url_params = {'mode': 'trakt.build_trakt_list', 'user': item["user"]["username"], 'slug': item["ids"]["slug"]}
            make_new_list_url = {'mode': 'trakt.make_new_trakt_list'}
            delete_list_url = {'mode': 'trakt.delete_trakt_list', 'user': item["user"]["username"], 'list_slug': item["ids"]["slug"]}
            add_to_subscriptions_url = {'mode': 'trakt.add_list_to_subscriptions', 'user': item["user"]["username"], 'list_slug': item["ids"]["slug"]}
            trakt_selection_url = {'mode': 'trakt.add_list_to_menu', 'method': 'add_trakt_external', 'name': item["name"], 'user': item["user"]["username"], 'slug': item["ids"]["slug"]}
            trakt_selection_favourites_url = {'mode': 'trakt.add_list_to_menu', 'method': 'add_trakt_external', 'name': item["name"], 'user': item["user"]["username"], 'slug': item["ids"]["slug"], 'list_name': 'FavouriteList'}
            url = build_url(url_params)
            cm.append(("[B]Make a new Trakt list[/B]",'XBMC.RunPlugin(%s)' % build_url(make_new_list_url)))
            cm.append(("[B]Delete this list[/B]",'XBMC.RunPlugin(%s)' % build_url(delete_list_url)))
            cm.append(("[B]Add this list to Subscriptions[/B]",'XBMC.RunPlugin(%s)' % build_url(add_to_subscriptions_url)))
            cm.append(("[B]Add this list to a Menu[/B]",'XBMC.RunPlugin(%s)' % build_url(trakt_selection_url)))
            listitem = xbmcgui.ListItem(item["name"])
            listitem.setArt({'thumb': my_list_icon, 'fanart': fanart})
            listitem.addContextMenuItems(cm, replaceItems=False)
            xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=True)
            xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    except: pass
    xbmcplugin.endOfDirectory(__handle__)
    setView('view.main')

def get_trakt_liked_lists():
    try:
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        mode = params.get('mode')
        page_no = params.get('new_page') if 'new_page' in params else '1'
        lists, pages = call_trakt("users/likes/lists", params={'limit': 20}, pagination=True, page=page_no)
        for item in lists:
            cm = []
            url_params = {'mode': 'trakt.build_trakt_list', 'user': item["list"]["user"]["username"], 'slug': item["list"]["ids"]["slug"]}
            unlike_list_url = {'mode': 'trakt.trakt_unlike_a_list', 'user': item["list"]["user"]["username"], 'list_slug': item["list"]["ids"]["slug"]}
            add_to_subscriptions_url = {'mode': 'trakt.add_list_to_subscriptions', 'user': item["list"]["user"]["username"], 'list_slug': item["list"]["ids"]["slug"]}
            trakt_selection_url = {'mode': 'trakt.add_list_to_menu', 'method': 'add_trakt_external', 'name': item["list"]["name"], 'user': item["list"]["user"]["username"], 'slug': item["list"]["ids"]["slug"]}
            trakt_selection_favourites_url = {'mode': 'trakt.add_list_to_menu', 'method': 'add_trakt_external', 'name': item["list"]["name"], 'user': item["list"]["user"]["username"], 'slug': item["list"]["ids"]["slug"], 'list_name': 'FavouriteList'}
            url = build_url(url_params)
            listitem = xbmcgui.ListItem(item["list"]["name"])
            listitem.setArt({'thumb': liked_list_icon, 'fanart': fanart})
            cm.append(("[B]Unlike this list[/B]",'XBMC.RunPlugin(%s)' % build_url(unlike_list_url)))
            cm.append(("[B]Add this list to Subscriptions[/B]",'XBMC.RunPlugin(%s)' % build_url(add_to_subscriptions_url)))
            cm.append(("[B]Add this list to a Menu[/B]",'XBMC.RunPlugin(%s)' % build_url(trakt_selection_url)))
            listitem.addContextMenuItems(cm, replaceItems=False)
            xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=True)
            xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        if pages > page_no:
            new_page = int(page_no) + 1
            add_dir({'mode': mode, 'new_page': str(new_page),
                'foldername': mode}, 'Next Page >>', iconImage='item_next.png')
    except: pass
    xbmcplugin.endOfDirectory(__handle__)
    setView('view.main')

def build_trakt_list():
    import ast
    from resources.lib.indexers.movies import Movies
    from resources.lib.indexers.tvshows import TVShows
    from resources.lib.modules.nav_utils import paginate_list
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    user = params.get('user')
    slug = params.get('slug')
    page_no = int(params.get('new_page', 1))
    letter = params.get('new_letter', 'None')
    passed_list = params.get('passed_list', [])
    limit = 40
    cache_to_disc = settings.cache_to_disc()
    try:
        if not passed_list:
            original_list = []
            result = call_trakt("users/{0}/lists/{1}/items?extended=full".format(user, slug), method='sort_by_headers')
            for item in result:
                try:
                    media_type = item['type']
                    key, action = ('movie', get_trakt_movie_id) if media_type == 'movie' else ('show', get_trakt_tvshow_id)
                    original_list.append({'media_type': media_type, 'title': item[key]['title'], 'media_id': action(item)})
                except: pass
        else: original_list = ast.literal_eval(passed_list)
        for item in original_list: content = 'movies' if item['media_type'] == 'movie' else 'tvshows'
        paginated_list, total_pages = paginate_list(original_list, page_no, letter, limit)
        movie_list = [i['media_id'] for i in paginated_list if i['media_type'] == 'movie']
        show_list = [i['media_id'] for i in paginated_list if i['media_type'] == 'show']
        if total_pages > 2: add_dir({'mode': 'build_navigate_to_page', 'current_page': page_no, 'total_pages': total_pages, 'transfer_mode': 'trakt.build_trakt_list', 'passed_list': original_list}, 'Go to Page....', iconImage='item_jump.png')
        if len(movie_list) >= 1: Movies(movie_list).worker()
        if len(show_list) >= 1: TVShows(show_list).worker()
        if len(paginated_list) == limit:
            add_dir({'mode': 'trakt.build_trakt_list', 'passed_list': original_list, 'user': user, 'slug': slug, 'new_page': str(page_no + 1), 'new_letter': letter}, 'Next Page >>', iconImage='item_next.png')
        xbmcplugin.setContent(__handle__, content)
        xbmcplugin.endOfDirectory(__handle__, cacheToDisc=cache_to_disc)
        setView('view.trakt_list', 250)
    except: notification('List Unavailable', 3000)

def sync_watched_trakt_to_furkit(refresh=False):
    try:
        window = xbmcgui.Window(10000)
        if refresh: window.setProperty('furkit_trakt_sync_complete', 'false')
        if window.getProperty('furkit_trakt_sync_complete') == 'true': return
        if settings.watched_indicators() in (0, 2): return
        import os
        from datetime import datetime
        from resources.lib.modules.indicators_bookmarks import clear_trakt_watched_data
        from resources.lib.modules.utils import clean_file_name
        try: from sqlite3 import dbapi2 as database
        except ImportError: from pysqlite2 import dbapi2 as database
        not_home_window = xbmc.getInfoLabel('Container.PluginName')
        processed_trakt_tv = []
        compare_trakt_tv = []
        WATCHED_DB = os.path.join(profile_dir, "watched_status.db")
        settings.check_database(WATCHED_DB)
        dbcon = database.connect(WATCHED_DB)
        dbcur = dbcon.cursor()
        if not_home_window:
            bg_dialog = xbmcgui.DialogProgressBG()
            bg_dialog.create('Trakt & Furk It Watched Status', 'Please Wait')
        for i in ['movie', 'tvshow']: clear_trakt_watched_data(i)
        trakt_watched_movies = trakt_indicators_movies()
        trakt_watched_tv = trakt_indicators_tv()
        process_movies = False
        process_tvshows = False
        dbcur.execute("SELECT media_id FROM watched_status WHERE db_type = ?", ('movie',))
        furkit_watched_movies = dbcur.fetchall()
        furkit_watched_movies = [int(i[0]) for i in furkit_watched_movies]
        compare_trakt_movies = [i[0] for i in trakt_watched_movies]
        process_trakt_movies = trakt_watched_movies
        if not sorted(furkit_watched_movies) == sorted(compare_trakt_movies): process_movies = True
        if not_home_window: bg_dialog.update(50, 'Trakt & Furk It Watched Status', 'Checking Movies Watched Status')
        xbmc.sleep(300)
        dbcur.execute("SELECT media_id, season, episode FROM watched_status WHERE db_type = ?", ('episode',))
        furkit_watched_episodes = dbcur.fetchall()
        furkit_watched_episodes = [(int(i[0]), i[1], i[2]) for i in furkit_watched_episodes]
        for i in trakt_watched_tv:
            for x in i[2]:
                compare_trakt_tv.append((i[0], x[0], x[1]))
                processed_trakt_tv.append((i[0], x[0], x[1], i[3]))
        if not sorted(furkit_watched_episodes) == sorted(compare_trakt_tv): process_tvshows = True
        if not_home_window: bg_dialog.update(100, 'Trakt & Furk It Watched Status', 'Checking Episodes Watched Status')
        xbmc.sleep(300)
        if not process_movies and not process_tvshows and not_home_window:
            bg_dialog.close()
        if process_movies:
            if not_home_window: sleep = float(2000) / float(len(trakt_watched_movies))
            dbcur.execute("DELETE FROM watched_status WHERE db_type=?", ('movie',))
            for count, i in enumerate(process_trakt_movies):
                try:
                    if not_home_window: bg_dialog.update(int(float(count) / float(len(trakt_watched_movies)) * 100), 'Trakt & Furk It Watched Status', 'Syncing Movie Watched Status')
                    last_played = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    dbcur.execute("INSERT OR IGNORE INTO watched_status VALUES (?, ?, ?, ?, ?, ?)", ('movie', str(i[0]), '', '', last_played, clean_file_name(to_utf8(i[1]))))
                    if not_home_window: xbmc.sleep(int(sleep))
                except: pass
        if process_tvshows:
            if not_home_window: sleep = float(2000) / float(len(processed_trakt_tv))
            dbcur.execute("DELETE FROM watched_status WHERE db_type=?", ('episode',))
            for count, i in enumerate(processed_trakt_tv):
                try:
                    if not_home_window: bg_dialog.update(int(float(count) / float(len(processed_trakt_tv)) * 100), 'Trakt & Furk It Watched Status', 'Syncing Episode Watched Status')
                    last_played = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    dbcur.execute("INSERT OR IGNORE INTO watched_status VALUES (?, ?, ?, ?, ?, ?)", ('episode', str(i[0]), i[1], i[2], last_played, clean_file_name(to_utf8(i[3]))))
                    if not_home_window: xbmc.sleep(int(sleep))
                except: pass
        if process_movies or process_tvshows:
            dbcon.commit()
        if not_home_window:
            bg_dialog.close()
            from resources.lib.modules.nav_utils import notification
            notification('Trakt Watched to Furk It Watched Sync Complete', time=4000)
        window.setProperty('furkit_trakt_sync_complete', 'true')
        __addon__.setSetting('trakt_indicators_active', 'true')
        if refresh: xbmc.executebuiltin("Container.Refresh")
    except:
        bg_dialog.close()
        from resources.lib.modules.nav_utils import notification
        notification('Error getting Trakt Watched Info', time=3500)
        pass

# def trakt_get_calendar():
#     return call_trakt("calendars/my/shows".format(type))

def get_trakt_movie_id(item):
    item = item['movie']['ids'] if 'movie' in item else item['ids']
    if item['tmdb']: return item['tmdb']
    from tikimeta.tmdb import tmdbMoviesExternalID
    tmdb_id = None
    if item['imdb']:
        try:
            meta = tmdbMoviesExternalID('imdb_id', item['imdb'])
            tmdb_id = meta['id']
        except: pass
    return tmdb_id

def get_trakt_tvshow_id(item):
    item = item['show']['ids'] if 'show' in item else item['ids']
    if item['tmdb']: return item['tmdb']
    from tikimeta.tmdb import tmdbTVShowsExternalID
    tmdb_id = None
    if item['imdb']:
        try: 
            meta = tmdbTVShowsExternalID('imdb_id', item['imdb'])
            tmdb_id = meta['id']
        except: tmdb_id = None
    if not tmdb_id:
        if item['tvdb']:
            try: 
                meta = tmdbTVShowsExternalID('tvdb_id', item['tvdb'])
                tmdb_id = meta['id']
            except: tmdb_id = None
    return tmdb_id

def trakt_indicators_movies():
    url = {'path': "sync/watched/movies%s", "with_auth": True, "pagination": False}
    return cache_object(process_trakt_watched_movies, 'trakt_indicators_movies', url, False, .5)

def trakt_indicators_tv():
    url = {'path': "users/me/watched/shows?extended=full%s", "with_auth": True, "pagination": False}
    return cache_object(process_trakt_watched_tv, 'trakt_indicators_tv', url, False, .5)

def process_trakt_watched_movies(url):
    result = get_trakt(url)
    for i in result:
        i.update({'tmdb_id': get_trakt_movie_id(i)})
    result = [(i['tmdb_id'], i['movie']['title']) for i in result if i['tmdb_id'] != None]
    return result

def process_trakt_watched_tv(url):
    result = get_trakt_watched_tv(url)
    for i in result:
        i.update({'tmdb_id': get_trakt_tvshow_id(i)})
    result = [(i['tmdb_id'], i['show']['aired_episodes'], sum([[(s['number'], e['number']) for e in s['episodes']] for s in i['seasons']], []), i['show']['title']) for i in result if i['tmdb_id'] != None]
    result = [(int(i[0]), int(i[1]), i[2], i[3]) for i in result]
    return result

def trakt_movies_trending(page_no):
    string = "%s_%s" % ('trakt_movies_trending', page_no)
    url = {'path': "movies/trending/%s", "params": {'limit': 20}, "page": page_no}
    return cache_object(get_trakt, string, url, False)

def trakt_movies_anticipated(page_no):
    string = "%s_%s" % ('trakt_movies_anticipated', page_no)
    url = {'path': "movies/anticipated/%s", "params": {'limit': 20}, "page": page_no}
    return cache_object(get_trakt, string, url, False)

def trakt_movies_top10_boxoffice(page_no):
    string = "%s" % 'trakt_movies_top10_boxoffice'
    url = {'path': "movies/boxoffice/%s", 'pagination': False}
    return cache_object(get_trakt, string, url, False)

def trakt_movies_mosts(period, duration, page_no):
    string = "%s_%s_%s_%s" % ('trakt_movies_mosts', period, duration, page_no)
    url = {'path': "movies/%s/%s", "path_insert": (period, duration), "params": {'limit': 20}, "page": page_no}
    return cache_object(get_trakt, string, url, False)

def trakt_movies_related(imdb_id, page_no):
    string = "%s_%s_%s" % ('trakt_movies_related', imdb_id, page_no)
    url = {'path': "movies/%s/related", "path_insert": imdb_id, "params": {'limit': 40}, "page": page_no}
    return cache_object(get_trakt, string, url, False)

def trakt_recommendations(db_type, limit=40):
    return to_utf8(call_trakt("/recommendations/{0}".format(db_type), params={'limit': limit}))

def trakt_tv_trending(page_no):
    string = "%s_%s" % ('trakt_tv_trending', page_no)
    url = {'path': "shows/trending/%s", "params": {'limit': 20}, "page": page_no}
    return cache_object(get_trakt, string, url, False)

def trakt_tv_anticipated(page_no):
    string = "%s_%s" % ('trakt_tv_anticipated', page_no)
    url = {'path': "shows/anticipated/%s", "params": {'limit': 20}, "page": page_no}
    return cache_object(get_trakt, string, url, False)

def trakt_tv_certifications(certification, page_no):
    string = "%s_%s_%s" % ('trakt_tv_certifications', certification, page_no)
    url = {'path': "shows/collected/all?certifications=%s", "path_insert": certification, "params": {'limit': 20}, "page": page_no}
    return cache_object(get_trakt, string, url, False)

def trakt_tv_mosts(period, duration, page_no):
    string = "%s_%s_%s_%s" % ('trakt_tv_mosts', period, duration, page_no)
    url = {'path': "shows/%s/%s", "path_insert": (period, duration), "params": {'limit': 20}, "page": page_no}
    return cache_object(get_trakt, string, url, False)

def trakt_tv_related(imdb_id, page_no):
    string = "%s_%s_%s" % ('trakt_tv_related', imdb_id, page_no)
    url = {'path': "shows/%s/related", "path_insert": imdb_id, "params": {'limit': 40}, "page": page_no}
    return cache_object(get_trakt, string, url, False)

def get_trakt_watched_tv(url):
    return cache_object(get_trakt, 'trakt_watched_shows', url, False, .5)

def get_trakt(url):
    result = call_trakt(url['path'] % url.get('path_insert', ''), params=url.get('params', {}), data=url.get('data'), is_delete=url.get('is_delete', False), with_auth=url.get('with_auth', False), method=url.get('method'), pagination=url.get('pagination', True), page=url.get('page'))
    return result[0] if url.get('pagination', True) else result
