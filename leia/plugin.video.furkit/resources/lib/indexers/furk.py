import xbmc, xbmcaddon, xbmcplugin, xbmcgui
import sys, os, json
import urllib
from urlparse import parse_qsl
from resources.lib.modules.nav_utils import build_url, setView
from resources.lib.modules.furk_api import FurkAPI
from resources.lib.modules.utils import clean_file_name, to_utf8
from resources.lib.modules import settings
# from resources.lib.modules.utils import logger

__addon_id__ = 'plugin.video.furkit'
__addon__ = xbmcaddon.Addon(id=__addon_id__)
__handle__ = int(sys.argv[1])
addon_dir = xbmc.translatePath(__addon__.getAddonInfo('path'))
icon_directory = settings.get_theme()
dialog = xbmcgui.Dialog()
window = xbmcgui.Window(10000)
default_furk_icon = os.path.join(icon_directory, 'furk.png')
fanart = os.path.join(addon_dir, 'fanart.jpg')

Furk = FurkAPI()

def my_furk_files():
    try:
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        files = eval('Furk.%s()' % params.get('list_type'))
        if params.get('list_type') in ('file_get_active', 'file_get_failed'):
            torrent_status_browser(files) 
        else: furk_file_browser(files, params, display_mode='file_browse')
    except: pass
    xbmcplugin.setContent(__handle__, 'files')
    xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
    setView('view.furk_files')

def torrent_status_browser(files):
    from datetime import timedelta
    from resources.lib.modules import furkitcache
    for count, item in enumerate(files, 1):
        try:
            display = '%02d | %s | [COLOR=grey][I]%s | %sGB | %s %% | SPEED: %s kB/s | (S:%s P:%s)[/I][/COLOR]' % (count, item['name'].replace('magnet:', '').upper(), item['dl_status'].upper(), str(round(float(item['size'])/1048576000, 1)), item['have'], str(round(float(item['speed'])/1024, 1)), item['seeders'], item['peers'])
            url_params = {'mode': 'furk.remove_from_downloads', 'name': item['name'], 'id': item['id']}
            url = build_url(url_params)
            listitem = xbmcgui.ListItem(display)
            xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=True)
        except: pass
    furkitcache.FurkItCache().set('furk_active_downloads', [i['info_hash'] for i in files], expiration=timedelta(hours=1))
    xbmcplugin.setContent(__handle__, 'files')
    xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
    setView('view.furk_files')

def search_furk():
    from resources.lib.modules.history import add_to_search_history
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    default = params.get('suggestion', '')
    search_title = clean_file_name(params.get('query')) if ('query' in params and params.get('query') != 'NA') else None
    if not search_title: search_title = dialog.input('Enter search Term', type=xbmcgui.INPUT_ALPHANUM, defaultt=default)
    if not search_title: return
    try:
        search_name = clean_file_name(urllib.unquote(search_title))
        search_method = 'search' if 'accurate_search' in params else 'direct_search'
        search_setting = 'furk_video_queries' if params.get('db_type') == 'video' else 'furk_audio_queries'
        list_type = 'video' if params.get('db_type') == 'video' else 'audio'
        add_to_search_history(search_name, search_setting)
        files = Furk.direct_search(search_name) if search_method == 'direct_search' else Furk.search(search_name)
        if not files: return dialog.ok('No results', 'No results')
        if not settings.include_uncached_results():
            try: files = [i for i in files if i.get('is_ready', '0') == '1' and i['type'] == list_type]
            except: return dialog.ok('No results', 'No results')
        furk_file_browser(files, params, display_mode='search')
    except: pass
    xbmcplugin.setContent(__handle__, 'files')
    xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
    setView('view.furk_files')

def furk_tfile_video():
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    t_files = [i for i in Furk.t_files(params.get('id')) if 'video' in i['ct'] and 'bitrate' in i]
    try:
        for count, item in enumerate(t_files, 1):
            cm = []
            url_params = {'mode': 'media_play', 'url': item['url_dl'], 'rootname': 'nill'}
            url = build_url(url_params)
            name = clean_file_name(item['name']).upper()
            if 1200 < int(item['height']) > 2100: display_res = '2160p'
            elif 1000 < int(item['height']) < 1200: display_res = '1080p'
            elif 680 < int(item['height']) < 1000: display_res = 'HD'
            else: display_res = 'SD'
            display_name = '%02d | [B]%s[/B] | [B]%.2f GB[/B] | %smbps | [I]%s[/I]' % \
            (count, display_res, float(item['size'])/1073741824, str(round(float(item['bitrate'])/1000, 2)), name)
            listitem = xbmcgui.ListItem(display_name)
            down_file_params = {'mode': 'download_file', 'name': item['name'], 'url': item['url_dl'], 'db_type': 'furk_file', 'image': default_furk_icon}
            cm.append(("[B]Download File[/B]",'XBMC.RunPlugin(%s)' % build_url(down_file_params)))
            listitem.addContextMenuItems(cm)
            listitem.setThumbnailImage(default_furk_icon)
            listitem.setArt({'fanart': fanart})
            listitem.setInfo('video', {'title': display_name, 'size': int(item['size']), 'duration': item['length']})
            listitem.setProperty("IsPlayable", "true")
            xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=True)
        xbmcplugin.setContent(__handle__, 'files')
        xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
        setView('view.furk_files')
    except: pass

def furk_tfile_audio():
    window.clearProperty('furkit_t_files_json')
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    excludes = ['', 'cover', 'covers', 'scan', 'scans', 'playlists']
    t_files = Furk.t_files(params.get('id'))
    item_path_list = sorted(list(set([clean_file_name(i['path']) for i in t_files if clean_file_name(i['path']).lower() not in excludes])))
    if not item_path_list:
        if dialog.yesno("Furk It Music Player", 'Browse Songs or Play Full Album?', '', '', 'Play Now','Browse'):
            return browse_audio_album(t_files, params.get('name'))
        from resources.lib.modules.player import FurkitPlayer
        FurkitPlayer().playAudioAlbum(t_files, params.get('name'))
        return browse_audio_album(t_files, params.get('name'))
    for x in item_path_list:
        url_params = {'mode': 'furk.browse_audio_album', 'item_path': x}
        url = build_url(url_params)
        listitem = xbmcgui.ListItem(x.upper())
        listitem.setThumbnailImage(default_furk_icon)
        listitem.setArt({'fanart': fanart})
        xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=True)
    t_files_json = json.dumps(t_files)
    window.setProperty('furkit_t_files_json', str(t_files_json))
    xbmcplugin.setContent(__handle__, 'files')
    xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
    setView('view.furk_files')

def browse_audio_album(t_files=None, name=None):
    def build_list_object():
        try:
            cm = []
            url_params = {'mode': 'media_play', 'url': item['url_dl'], 'rootname': 'nill'}
            url = build_url(url_params)
            track_name = clean_file_name(batch_replace(to_utf8(item['name']), formats)).upper()
            listitem = xbmcgui.ListItem(track_name)
            down_file_params = {'mode': 'download_file', 'name': item['name'], 'url': item['url_dl'], 'image': default_furk_icon, 'db_type': 'furk_file'}
            cm.append(("[B]Download File[/B]",'XBMC.RunPlugin(%s)' % build_url(down_file_params)))
            listitem.addContextMenuItems(cm)
            listitem.setThumbnailImage(default_furk_icon)
            listitem.setArt({'fanart': fanart})
            listitem.setInfo(type='music',infoLabels={'title': track_name, 'size': int(item['size']), 'album': item['path'], 'duration': item['length']})
            listitem.setProperty("IsPlayable", "true")
            xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=False)
        except: pass
    from resources.lib.modules.utils import batch_replace
    formats = ('.3gp', ''),('.aac', ''),('.flac', ''),('.m4a', ''),('.mp3', ''),('.ogg', ''),('.raw', ''),('.wav', ''),('.wma', ''),('.webm', ''),('.ra', ''),('.rm', '')
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    seperate = False
    if not t_files:
        seperate = True
        t_fs = window.getProperty('furkit_t_files_json')
        t_files = json.loads(t_fs)
    t_files = [i for i in t_files if 'audio' in i['ct']]
    if seperate:
        if dialog.yesno("Furk It Music Player", 'Browse Songs or Play Full Album?', '', '', 'Play Now','Browse'):
            for item in t_files:
                item_path = clean_file_name(item['path'])
                if item_path == params.get('item_path'):
                    build_list_object()
            xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
            setView('view.furk_files')
        else:
            from resources.lib.modules.player import FurkitPlayer
            FurkitPlayer().playAudioAlbum(t_files, from_seperate=True)
    else:
        for item in t_files:
            build_list_object()
        xbmcplugin.setContent(__handle__, 'files')
        xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
        setView('view.furk_files')

def my_furk_audio_favourites():
    from resources.lib.modules.favourites import retrieve_favourites
    results = retrieve_favourites('audio', '', '')
    for item in results:
        try:
            cm = []
            name = item.split('<>')[0]
            item_id = item.split('<>')[1]
            url_dl = item.split('<>')[2]
            size = item.split('<>')[3]
            display_size = str(round(float(size)/1048576000, 1))
            display = '[B]%sGB[/B] | [I]%s[/I]' % (display_size, name)
            url_params = {'mode': 'furk.furk_tfile_audio', 'name': name, 'id': item_id}
            url = build_url(url_params)
            con_remove_favs = {'mode': 'remove_from_favourites', 'db_type': 'audio', 'tmdb_id': item}
            con_download_archive = {'mode': 'download_file', 'name': name, 'url': url_dl, 'image': default_furk_icon, 'db_type': 'archive'}
            cm.append(("[B]Remove from Furk It Favourites[/B]",'XBMC.RunPlugin(%s)' % build_url(con_remove_favs)))
            cm.append(("[B]Download Archive[/B]",'XBMC.RunPlugin(%s)' % build_url(con_download_archive)))
            listitem = xbmcgui.ListItem(display)
            listitem.addContextMenuItems(cm)
            listitem.setThumbnailImage(default_furk_icon)
            listitem.setArt({'fanart': fanart})
            listitem.setInfo(type='video', infoLabels={'title': display, 'size': int(size)})
            xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=True)
        except: pass
    xbmcplugin.setContent(__handle__, 'files')
    xbmcplugin.endOfDirectory(__handle__, cacheToDisc=True)
    setView('view.furk_files')

def furk_file_browser(files, params, display_mode):
    files_num = 'files_num_video' if (params.get('list_type') == 'file_get_video' or params.get('db_type') == 'video') else 'files_num_audio'
    list_type = 'video' if (params.get('list_type') == 'file_get_video' or params.get('db_type') == 'video') else 'music'
    mode = 'furk.furk_tfile_video' if (params.get('list_type') == 'file_get_video' or params.get('db_type') == 'video') else 'furk.furk_tfile_audio'
    for count, item in enumerate(files, 1):
        try:
            uncached = True if not 'url_dl' in item else False
            if uncached:
                active_downloads = get_active_downloads()
                mode = 'furk.add_uncached_file'
                if item['info_hash'] in active_downloads:
                    info = '%02d | [COLOR=green][B][ACTIVE][/B][/COLOR] |' % count
                else:
                    info = '%02d | [COLOR=red][B][UNCACHED][/B][/COLOR] |' % count
            name = clean_file_name(item['name']).upper()
            item_id = item['id'] if not uncached else item['info_hash']
            url_dl = item['url_dl'] if not uncached else item['info_hash']
            size = item['size']
            if not uncached:
                is_protected = item.get('is_protected')
                display_size = str(round(float(size)/1048576000, 1))
                info_unprotected = '[B] %s GB | %s files | [/B]' % (display_size, item[files_num])
                info_protected = '[COLOR=green]%s[/COLOR]' % info_unprotected
                info_search = '%02d | [B]%s GB[/B] | [B]%s files[/B] |' % (count, display_size, item[files_num])
                info = info_search if display_mode == 'search' else info_protected if is_protected == '1' else info_unprotected if is_protected == '0' else None
            display = '%s [I] %s [/I]' % (info, name)
            url_params = {'mode': mode, 'name': name, 'id': item_id}
            url = build_url(url_params)
            cm = []
            if not uncached:
                con_add_favs = {'mode': 'add_to_favourites_audio', 'name': name, '_id': item_id, 'url_dl': url_dl, 'size': size}
                con_download_archive = {'mode': 'download_file', 'name': item.get("name"), 'url': url_dl, 'db_type': 'archive', 'image': default_furk_icon}
                con_remove_files = {'mode': 'furk.remove_from_files', 'name': name, 'item_id': item_id}
                con_protect_files = {'mode': 'furk.myfiles_protect_unprotect', 'action': 'protect', 'name': name, 'item_id': item_id}
                con_unprotect_files = {'mode': 'furk.myfiles_protect_unprotect', 'action': 'unprotect', 'name': name, 'item_id': item_id}
                con_add_to_files = {'mode': 'furk.add_to_files', 'name': name, 'item_id': item_id}
                if params.get('db_type') == 'audio': cm.append(("[B]Add to Furk It Favourites[/B]",'XBMC.RunPlugin(%s)' % build_url(con_add_favs)))
                if display_mode == 'search': cm.append(("[B]Add to My Files[/B]",'XBMC.RunPlugin(%s)' % build_url(con_add_to_files)))
                cm.append(("[B]Download Archive[/B]",'XBMC.RunPlugin(%s)' % build_url(con_download_archive)))
                cm.append(("[B]Remove from My Files[/B]",'XBMC.RunPlugin(%s)' % build_url(con_remove_files)))
                if is_protected == '0': cm.append(("[B]Protect File[/B]",'XBMC.RunPlugin(%s)' % build_url(con_protect_files)))
                if is_protected == '1': cm.append(("[B]Unprotect File[/B]",'XBMC.RunPlugin(%s)' % build_url(con_unprotect_files)))
            listitem = xbmcgui.ListItem(display)
            listitem.addContextMenuItems(cm)
            listitem.setArt({'thumb': default_furk_icon, 'fanart': fanart})
            listitem.setInfo(type=list_type, infoLabels={'title': display, 'size': int(size)})
            xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=True)
        except: pass

def t_file_browser(item_id, filtering_list=None, source=None):
    origin = settings.define_origin(source)
    t_files = [i for i in Furk.t_files(item_id) if 'video' in i['ct']]
    if settings.auto_play(origin) or settings.auto_resolve(origin):
        name, url_dl, size = filter_furk_tlist(t_files, filtering_list)
        return [{'name': name, 'url_dl': url_dl, 'size': size}]
    return [{'name': i['name'].upper(), 'display_name': '[B]%02d | %s | %s | %.2f GB' % (c, get_release_quality(i['name'], i['url_dl'], t_file='yep')[0], get_release_quality(i['name'], i['url_dl'], t_file='yep')[1], float(i['size'])/1073741824), 'url_dl': i['url_dl'], 'size': i['size']} for c, i in enumerate(t_files, 1)]

def filter_furk_tlist(t_files, filtering_list=None):
    t_files = [i for i in t_files if 'video' in i['ct'] and any(x in i['name'].lower() for x in filtering_list) and not any(x in i['name'].lower() for x in ['furk320', 'sample'])][0] if filtering_list else [i for i in t_files if 'is_largest' in i][0]
    return t_files['name'], t_files['url_dl'], t_files['size']

def seas_ep_query_list(season, episode):
    return ['s%02de%02d' % (int(season), int(episode)), '%dx%02d' % (int(season), int(episode)),
            '%02dx%02d' % (int(season), int(episode))]

def get_release_quality(release_name, release_link=None, t_file=None):
    import re
    if release_name is None: return
    try: release_name = release_name
    except: pass
    try:
        vid_quality = None
        release_name = release_name.upper()
        fmt = re.sub('(.+)(\.|\(|\[|\s)(\d{4}|S\d*E\d*|S\d*)(\.|\)|\]|\s)', '', release_name)
        fmt = re.split('\.|\(|\)|\[|\]|\s|-', fmt)
        fmt = [i.lower() for i in fmt]
        if any(i in ['dvdscr', 'r5', 'r6'] for i in fmt): vid_quality = 'SCR'
        elif any(i in ['camrip', 'tsrip', 'hdcam', 'hd-cam', 'hdts', 'dvdcam', 'dvdts', 'cam', 'telesync', 'ts'] for i in fmt): vid_quality = 'CAM'
        elif any(i in ['tc', 'hdtc', 'telecine', 'tc720p', 'tc720', 'hdtc'] for i in fmt): vid_quality = 'TELE'
        elif '2160p' in fmt: vid_quality = '2160p'
        elif '1080p' in fmt: vid_quality = '1080p'
        elif '720p' in fmt: vid_quality = '720p'
        elif 'brrip' in fmt: vid_quality = '720p'
        if not vid_quality:
            if release_link:
                release_link = release_link.lower()
                try: release_link = release_link
                except: pass
                if any(i in ['dvdscr', 'r5', 'r6'] for i in release_link): vid_quality = 'SCR'
                elif any(i in ['camrip', 'tsrip', 'hdcam', 'hdts', 'dvdcam', 'dvdts', 'cam', 'telesync', 'ts'] for i in release_link): vid_quality = 'CAM'
                elif any(i in ['tc', 'hdtc', 'telecine', 'tc720p', 'tc720', 'hdtc'] for i in release_link): vid_quality = 'TELE'
                elif '2160' in release_link: vid_quality = '4K'
                elif '1080' in release_link: vid_quality = '1080p'
                elif '720' in release_link: vid_quality = '720p'
                elif '.hd' in release_link: vid_quality = 'SD'
                else: vid_quality = 'SD'
            else: vid_quality = 'SD'
        if not t_file:
            return vid_quality
        else:
            vid_type = 'H264'
            if any(i in ['hevc', 'h265', 'x265'] for i in fmt): vid_type = 'HEVC'
            return vid_quality, vid_type
    except:
        if not t_file:
            return 'SD'
        else:
            return 'SD', 'x264'

def add_to_files(name='', item_id=''):
    from resources.lib.modules.nav_utils import notification
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    name = params.get('name') if 'name' in params else name
    item_id = params.get('item_id') if 'item_id' in params else item_id
    resp = dialog.yesno('Are you sure?', "Add\n[B]%s[/B]\nto My Furk Files?" % name)
    if resp:
        response = Furk.file_link(item_id)
        if response['status'] == 'ok':
            notification('{}'.format('Item added to My Furk Files'), 3500)
        else:
            notification('{}'.format('Error - [B][I]%s[/I][/B]' % response['status']), 3500)
        return (None, None)
        dialog.close()
    else: return

def remove_from_files(name='', item_id=''):
    from resources.lib.modules.nav_utils import notification
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    name = params.get('name')
    item_id = params.get('item_id')
    resp = dialog.yesno('Are you sure?', "Remove [B][I]%s[/I][/B]  from My Furk Files?" % name)
    if resp:
        response = Furk.file_unlink(item_id)
        if response['status'] == 'ok':
            notification('{}'.format('Item removed from My Furk Files'), 3500)
            xbmc.executebuiltin("Container.Refresh")
        else:
            notification('{}'.format('Error - [B][I]%s[/I][/B]' % response['status']), 3500)
        return (None, None)
        dialog.close()
    else: return

def remove_from_downloads(name='', item_id=''):
    from resources.lib.modules.nav_utils import notification
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    name = params.get('name', name)
    item_id = params.get('id', item_id)
    resp = dialog.yesno('Furk It', "[B][I]%s[/I][/B]" % name, "", "Remove from My Furk Downloads?")
    if resp:
        response = Furk.download_unlink(item_id)
        if response['status'] == 'ok':
            from datetime import timedelta
            from resources.lib.modules import furkitcache
            furkitcache.FurkItCache().set('furk_active_downloads', None, expiration=timedelta(hours=1))
            dialog.ok('Furk It', '[COLOR=green][B]SUCCESS.[/B][/COLOR]', '[B][I]%s[/I][/B]' % name, 'Torrent removed')
        else:
            dialog.ok('Furk It', '[COLOR=red][B]FAIL.[/B][/COLOR]', '[B][I]%s[/I][/B]' % name, 'Error removing torrent')
        return (None, None)
        dialog.close()
    else: return

def get_active_downloads():
    from datetime import timedelta
    from resources.lib.modules import furkitcache
    _cache = furkitcache.FurkItCache()
    cache = _cache.get('furk_active_downloads')
    if cache != None: result = cache
    else:
        active_downloads = Furk.file_get_active()
        result = [i['info_hash'] for i in active_downloads]
        _cache.set('furk_active_downloads', result, expiration=timedelta(hours=1))
    return result

def myfiles_protect_unprotect(name='', item_id='', action=''):
    from resources.lib.modules.nav_utils import notification
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    name = params.get('name') if 'name' in params else name
    item_id = params.get('item_id') if 'item_id' in params else item_id
    action = params.get('action') if 'action' in params else action
    is_protected = '1' if action == 'protect' else '0'
    line1 = 'File added to Protected List' if action == 'protect' else 'File removed from Protected List'
    try:
        response = Furk.file_protect(item_id, is_protected)
        if response['status'] == 'ok':
            xbmc.executebuiltin("Container.Refresh")
            notification(line1, time=7000)
    except: return

def add_uncached_file(name=None, item_id=None):
    params = dict(parse_qsl(sys.argv[2].replace('?','')))
    name = params.get('name', name)
    item_id = params.get('id', item_id)
    if not dialog.yesno("Furk It", '[B][I]%s[/I][/B]' % name, '', 'Add this uncached torrent to your Furk Files?', 'No','Yes'):
        return
    try:
        response = Furk.add_uncached(item_id)
        if response['status'] == 'ok':
            from datetime import timedelta
            from resources.lib.modules import furkitcache
            furkitcache.FurkItCache().set('furk_active_downloads', None, expiration=timedelta(hours=1))
            dialog.ok('Furk It', '[COLOR=green][B]SUCCESS.[/B][/COLOR]', '[B][I]%s[/I][/B]' % name, 'Torrent added')
        elif response['status'] == 'error':
            dialog.ok('Furk It', '[COLOR=red][B]FAIL.[/B][/COLOR]', '[B][I]%s[/I][/B]' % name, 'Error adding torrent')
        return
    except: return

def account_info():
    from resources.lib.modules.utils import regex_from_to
    try:
        accinfo = Furk.account_info()
        account_type = accinfo['premium']['name']
        month_time_left = float(accinfo['premium']['bw_month_time_left'])/60/60/24
        try: total_time_left = float(accinfo['premium']['time_left'])/60/60/24
        except: total_time_left = ''
        try: bw_used_month = float(accinfo['premium']['bw_used_month'])/1073741824
        except: bw_used_month = ''
        try: bw_limit_month = float(accinfo['premium']['bw_limit_month'])/1073741824
        except: bw_limit_month = ''
        try: is_not_last_month = accinfo['premium']['is_not_last_month']
        except: is_not_last_month = ''
        try: renewal_date = accinfo['premium']['to_dt']
        except: renewal_date = ''
        try: rem_bw_limit_month = bw_limit_month - bw_used_month
        except: rem_bw_limit_month = ''
        if account_type == 'LIFETIME':
            remaining_text = 'You have [B]{0}[/B] days left in your current month. You have used [B]{1}GB[/B] of your data allowance, and have [B]{2}GB[/B] remaining.'.format(round(month_time_left, 2), round(bw_used_month, 2), round(rem_bw_limit_month, 2))
            return dialog.ok('Account Type: {0} - {1}GB per month '.format(account_type, round(bw_limit_month, 0)),remaining_text)
        if is_not_last_month == '1':
            remaining_text = 'You have [B]{0}[/B] days left in your current subscription. Your subscription resets on [B]{1}[/B]'.format(round(total_time_left, 2), renewal_date)
        else: 
            remaining_text = 'You will need to [B]renew[/B] your subscription in [B]{0}[/B] days. Date of renewal is [B]{1}[/B]'.format(round(total_time_left, 2), renewal_date)
        return dialog.ok('Account Type: {0} - {1}GB per month '.format(account_type, round(bw_limit_month, 0)),
            'You have [B]{0}[/B] days remaining for your current month, and have [B]{1}GB[/B] of data remaining. {2}.'.format(round(month_time_left, 2), round(rem_bw_limit_month, 2), remaining_text))
    except: pass

