
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import sys, os
import json
import urllib
import time
from operator import itemgetter
from resources.lib.modules.workers import Thread
from resources.lib.sources.local_library import LocalLibrarySource
from resources.lib.modules.utils import clean_file_name, to_utf8
from resources.lib.indexers.furk import t_file_browser, seas_ep_query_list, add_uncached_file
from resources.lib.modules.nav_utils import build_url, setView, close_all_dialog, \
                                            show_busy_dialog, hide_busy_dialog
from resources.lib.modules import settings
import tikimeta
# from resources.lib.modules.utils import logger

__handle__ = int(sys.argv[1])
window = xbmcgui.Window(10000)
dialog = xbmcgui.Dialog()
default_furk_icon = os.path.join(settings.get_theme(), 'furk.png')

class Sources:
    def __init__(self):
        self.providers = []
        self.sources = []
        self.starting_providers = []
        self.threads = []

    def playback_prep(self, vid_type, tmdb_id, query, tvshowtitle=None, season=None, episode=None, ep_name=None, plot=None, meta=None, from_library=False, background='false'):
        self.from_library = from_library
        self.not_widget = xbmc.getInfoLabel('Container.PluginName')
        self.action = 'XBMC.Container.Update(%s)' if self.not_widget else 'XBMC.RunPlugin(%s)'
        self.use_dialog = True if self.from_library or not self.not_widget else settings.use_dialog()
        self.origin = 'context' if self.from_library else None
        self.autoplay = settings.auto_play(self.origin)
        self.prefer_hevc = settings.prefer_hevc(self.origin)
        self.check_library = settings.check_library()
        self.include_prerelease_results = settings.include_prerelease_results(self.origin)
        self.include_uncached_results = settings.include_uncached_results()
        self.meta = json.loads(meta) if meta else tikimeta.movie_meta('tmdb_id', tmdb_id) if vid_type == "movie" else tikimeta.tvshow_meta('tmdb_id', tmdb_id)
        self.vid_type = vid_type
        self.tmdb_id = tmdb_id
        self.season = int(season) if season else ''
        self.episode = int(episode) if episode else ''
        display_name = clean_file_name(urllib.unquote(query)) if vid_type == 'movie' else '%s - %dx%.2d' % (self.meta['title'], self.season, self.episode)
        if from_library: self.meta.update({'plot': plot, 'from_library': from_library, 'ep_name': ep_name})
        self.meta.update({'query': query, 'vid_type': self.vid_type, 'media_id': self.tmdb_id,
            'rootname': display_name, 'tvshowtitle': self.meta['title'], 'season': self.season,
            'episode': self.episode, 'background': background})
        self.search_info = self._search_info()
        self._clear_sources()
        window.setProperty('furkit_media_meta', json.dumps(self.meta))
        self.get_sources()

    def get_sources(self):
        self.active_scrapers = settings.active_scrapers()
        return self._collect_results()

    def _collect_results(self):
        background = True if self.meta.get('background', 'false') == 'true' else False
        if 'local' in self.active_scrapers:
            if self.check_library or self.autoplay:
                if self._check_library_before_search():
                    window.setProperty('furkit_search_results', json.dumps(self.sources))
                    return xbmc.executebuiltin(self.action % build_url({'mode': 'play_display_results', 'use_dialog': self.use_dialog, 'from_library': self.from_library}))
            else: self.providers.append(('local', LocalLibrarySource()))
        if 'furk' in self.active_scrapers:
            from resources.lib.sources.furk import FurkSource
            self.providers.append(('furk', FurkSource()))
        if 'easynews' in self.active_scrapers:
            from resources.lib.sources.easynews import EasyNewsSource
            self.providers.append(('easynews', EasyNewsSource()))
        if 'external' in self.active_scrapers:
            from resources.lib.sources.external import ExternalSource
            self.providers.append(('external', ExternalSource()))
        for i in range(len(self.providers)):
            self.threads.append(Thread(self._activate_providers, self.providers[i][1]))
            self.starting_providers.append((self.threads[i].getName(), self.providers[i][0]))
        [i.start() for i in self.threads]
        if 'external' in self.active_scrapers or background:
            [i.join() for i in self.threads]
        else:
            self._internal_scrapers_dialog()
        return self._filter_results(self.sources)

    def _activate_providers(self, function):
        sources = function.results(self.search_info)
        self.sources.extend(sources)

    def _internal_scrapers_dialog(self):
        hide_busy_dialog()
        total_providers = len(self.starting_providers)
        progressHeading = int(xbmcaddon.Addon(id='plugin.video.furkit').getSetting('progress.heading'))
        progressDialog = xbmcgui.DialogProgress()
        progressTitle = '%s' % (self.meta.get('rootname')) if progressHeading == 1 else 'Internal Scrapers'
        progressDialog.create(progressTitle, '')
        progressDialog.update(0)
        total_format = '[COLOR %s][B]%s[/B][/COLOR]'
        for i in range(0, 120):
            try:
                if xbmc.abortRequested == True: return sys.exit()
                try:
                    if progressDialog.iscanceled():
                        break
                except Exception:
                    pass
                alive_threads = [x.getName() for x in self.threads if x.is_alive() is True]
                remaining_providers = [x[1] for x in self.starting_providers if x[0] in alive_threads]
                source_4k_label = total_format % ('blue', len([e for e in self.sources if e['quality'] == '4K' and  not 'uncached' in e]))
                source_1080_label = total_format % ('blue', len([e for e in self.sources if e['quality']  == '1080p' and  not 'uncached' in e]))
                source_720_label = total_format % ('blue', len([e for e in self.sources if e['quality'] == '720p' and  not 'uncached' in e]))
                source_sd_label = total_format % ('blue', len([e for e in self.sources if e['quality'] in ['SD', 'SCR', 'CAM', 'TELE'] and not 'uncached' in e]))
                source_total_label = total_format % ('blue', len([e for e in self.sources if e['quality'] in ['4K', '1080p', '720p', 'SD', 'SCR', 'CAM', 'TELE'] and not 'uncached' in e]))
                try:
                    line1 = ('[COLOR=blue][B]Int:[/B][/COLOR] 4K: %s | 1080p: %s | 720p: %s | SD: %s | Total: %s') % (source_4k_label, source_1080_label, source_720_label, source_sd_label, source_total_label)
                    line2 = 'Remaining providers: %s' % ', '.join(remaining_providers).upper()
                    percent = int(float(total_providers - len(remaining_providers)) / total_providers * 100)
                    progressDialog.update(max(1, percent), line1, line2, '')
                except: pass
                time.sleep(0.5)
                if len(alive_threads) == 0: break
            except Exception:
                pass
        try:
            progressDialog.close()
        except Exception:
            pass
        xbmc.sleep(500)

    def _filter_results(self, results):
        cached_results = [i for i in results if not 'uncached' in i]
        self.uncached_results = [i for i in results if 'uncached' in i]
        quality_filter = self._quality_filter()
        include_local_in_filter = settings.include_local_in_filter(self.autoplay)
        results = []
        for item in cached_results:
            if item.get("local") and not include_local_in_filter: results.append(item)
            elif item.get("quality") in quality_filter: results.append(item)
        return self._sort_results(results)

    def _sort_results(self, results):
        sort_tuple = settings.results_sort_order()
        try:
            for item in results:
                item['quality_rank'] = self._get_quality_rank(item.get("quality", "SD"))
                item['name_rank'] = self._get_name_rank(item.get("scrape_provider"))
            results = sorted(results, key=itemgetter(sort_tuple[0], sort_tuple[1], sort_tuple[2]), reverse=True)
        except: pass
        if settings.local_sorted_first():
            results = self._local_first(results)
        return self._return_results(results)

    def _return_results(self, results):
        if self.autoplay:
            return self._filter_autoplay(results)
        if self.include_uncached_results: results += self.uncached_results
        window.setProperty('furkit_search_results', json.dumps(results))
        xbmc.sleep(200)
        hide_busy_dialog()
        return xbmc.executebuiltin(self.action % build_url({'mode': 'play_display_results', 'use_dialog': self.use_dialog, 'from_library': self.from_library}))

    def display_results(self, use_dialog=False, from_library=False):
        def _build_directory(item, item_no):
            try:
                uncached = item.get('uncached', False)
                external = item.get('external', False)
                mode = 'furk.add_uncached_file' if uncached else 'play_file'
                url = build_url({'mode': mode, 'title': item.get('title'), 'name': item.get('name'), 'id': item.get("id"), 'from_library': from_library, 'source': json.dumps([item])})
                cm = []
                if external: display_name = item.get("label")
                else: display_name = item.get("display_name")
                display = '%02d | %s' % (item_no+1, display_name)
                listitem = xbmcgui.ListItem(display)
                listitem.setArt({'poster': meta['poster'], 'fanart': meta['fanart'], 'thumb': meta['poster']})
                playback_params = {'mode': 'playback_menu', 'from_results': True}
                cm.append(("[B]Options[/B]",'XBMC.RunPlugin(%s)' % build_url(playback_params)))
                if not uncached:
                    if item['scrape_provider'] == 'furk':
                        add_files_params = {'mode': 'furk.add_to_files', 'name': item.get("name"), 'item_id': item.get("id")}
                        cm.append(("[B]Add to My Files[/B]",'XBMC.RunPlugin(%s)'  % build_url(add_files_params)))
                    if 'PACK' in display:
                        down_archive_params = {'mode': 'download_file', 'name': item.get("name"), 'url': item.get("url_dl"), 'db_type': 'archive', 'image': default_furk_icon}
                        cm.append(("[B]Download Archive[/B]",'XBMC.RunPlugin(%s)' % build_url(down_archive_params)))
                    if item['scrape_provider'] != 'local':
                        down_file_params = {'mode': 'download_file', 'name': meta.get('rootname'), 'url': item.get("url_dl"), 'image': meta.get('poster', ''), 'source': json.dumps([item]), 'meta': meta_json}
                        if item['scrape_provider'] == 'furk': down_file_params['archive'] = True
                        cm.append(("[B]Download File[/B]",'XBMC.RunPlugin(%s)' % build_url(down_file_params)))
                listitem.addContextMenuItems(cm)
                if meta['vid_type'] == 'movie': listitem.setInfo('video', {'title': meta.get('title', ''), 'year': meta.get('year', ''), 'plot': meta.get('plot', '')})
                elif meta['vid_type'] == 'episode': listitem.setInfo('video', {'title': meta.get('rootname', ''), 'plot': meta.get('plot', '')})
                item_list.append({'list_item': (url, listitem, True), 'item_no': item_no})
            except: pass
        xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()
        xbmc.PlayList(xbmc.PLAYLIST_MUSIC).clear()
        item_list = []
        threads = []
        auto_play_setting = 'library' if from_library else None
        results = json.loads(window.getProperty('furkit_search_results'))
        meta = json.loads(window.getProperty('furkit_media_meta'))
        meta_json = window.getProperty('furkit_media_meta')
        if meta['vid_type'] == 'episode' and meta.get('background') == 'true':
            from resources.lib.modules.player import FurkitPlayer
            from resources.lib.modules.nav_utils import notification
            notification('%s %s S%02dE%02d' % ('Next Up Autoplay:', meta['title'], meta['season'], meta['episode']), 10000, meta['poster'])
            PLAYER = FurkitPlayer()
            while PLAYER.isPlaying(): xbmc.sleep(100)
        if not results: return dialog.ok('Furk It', 'No Results')
        if results[0].get('play_local', False): return xbmc.executebuiltin('XBMC.RunPlugin(%s)' % build_url({'mode': 'play_auto'}))
        if results[0].get('autoplay', False): return xbmc.executebuiltin('XBMC.RunPlugin(%s)' % build_url({'mode': 'play_auto'}))
        total = len(results)
        if use_dialog:
            hide_busy_dialog()
            close_all_dialog()
            display_list = ['%02d | %s' % (count, i.get("label")) for count, i in enumerate(results, 1)]
            chosen = dialog.select("Furk It Results", display_list)
            if chosen < 0: return
            chosen_result = results[chosen]
            if chosen_result.get('uncached', False):
                return add_uncached_file(chosen_result.get('name'), chosen_result.get('id'))
            url = build_url({'mode': 'play_file', 'title': chosen_result.get('title'), 'id': chosen_result.get("id"), 'use_dialog': use_dialog, 'source': json.dumps([chosen_result])})
            return xbmc.executebuiltin('XBMC.RunPlugin(%s)' % url)
        [threads.append(Thread(_build_directory, results[i], i)) for i in range(total) if i <= total]
        [i.start() for i in threads]
        [i.join() for i in threads]
        item_list = sorted(item_list, key=lambda k: k['item_no'])
        xbmcplugin.addDirectoryItems(__handle__, [i['list_item'] for i in item_list])
        xbmcplugin.setContent(__handle__, 'files')
        xbmcplugin.endOfDirectory(__handle__)
        setView('view.media_results')

    def _search_info(self):
        return {'db_type': self.vid_type, 'title': self.meta.get('title'), 'year': self.meta.get('year'),
        'tmdb_id': self.tmdb_id, 'imdb_id': self.meta.get('imdb_id'), 'season': self.season,
        'episode': self.episode, 'premiered': self.meta.get('premiered'), 'tvdb_id': self.meta.get('tvdb_id'),
        'ep_name': self.meta.get('ep_name')}

    def _filter_autoplay(self, results):
        local_file = [i for i in results if i.get("local")]
        if local_file: results = local_file
        else:
            if self.prefer_hevc:
                hevc_list = [dict(i, **{'hevc':self._get_hevc_status(i.get("display_name", ""))}) for i in results]
                hevc_list = [i for i in hevc_list if i.get("hevc")]
                if hevc_list: results = hevc_list
        results = [dict(i, **{'autoplay':True}) for i in results]
        window.setProperty('furkit_search_results', json.dumps(results))
        return xbmc.executebuiltin(self.action % build_url({'mode': 'play_display_results', 'use_dialog': self.use_dialog, 'from_library': self.from_library}))

    def _check_library_before_search(self):
        self.sources.extend(LocalLibrarySource().results(self.search_info))
        if self.sources:
            if self.autoplay:
                self.sources[0]['play_local'] = True
                return True
            else:
                line = '%s (%s)' % (self.meta['title'], self.meta['year']) if self.vid_type == 'movie' else '%s - %dx%.2d' % (self.meta['title'], int(self.meta['season']), int(self.meta['episode']))
                if xbmcgui.Dialog().yesno("%s found in Kodi Database" % line, "Would you like to play the local file?", '', '', 'Yes', 'No') == 0:
                    self.sources[0]['play_local'] = True
                    return True
                else:
                    self.sources = []
                    return False
        else: pass

    def _quality_filter(self):
        sl = ['results_quality', 'autoplay_quality', 'results_quality_library', 'autoplay_quality_library']
        if not self.from_library: setting = sl[0] if not self.autoplay else sl[1]
        elif self.from_library: setting = sl[2] if not self.autoplay else sl[3]
        quality_filter = settings.quality_filter(setting)
        if self.include_prerelease_results: quality_filter += ['SCR', 'CAM', 'TELE']
        return quality_filter

    def _get_quality_rank(self, quality):
        if quality == '4K': return 6
        if quality == '1080p': return 5
        if quality == '720p': return 4
        if quality == 'SD': return 3
        if quality in ['SCR', 'CAM', 'TELE']: return 2
        return 1

    def _get_name_rank(self, provider):
        if 'local' in provider: return 4
        if 'furk' in provider: return 3
        if 'easynews' in provider: return 2
        return 1

    def _local_first(self, results):
        try:
            local_result = [i for i in results if i['scrape_provider'] == 'local'][0]
            results.remove(local_result)
            results.insert(0, local_result)
        except: pass
        return results

    def _get_hevc_status(self, description):
        if 'HEVC' in description: return True 
        else: return False

    def _clear_sources(self):
        for item in ('local_source_results', 'furk_source_results', 'easynews_source_results',
                    'furkit_media_meta', 'furkit_search_results'):
            window.clearProperty(item)

    def play_file(self, title, source):
        from resources.lib.modules.player import FurkitPlayer
        try:
            next = []
            prev = []
            total = []
            results = json.loads(window.getProperty('furkit_search_results'))
            results = [i for i in results if not i.get('uncached', False)]
            source_index = results.index(json.loads(source)[0])
            for i in range(1, 25):
                try:
                    u = results[i+source_index]
                    if u in total:
                        raise Exception()
                    total.append(u)
                    next.append(u)
                except Exception:
                    break
            for i in range(-25, 0)[::-1]:
                try:
                    u = results[i+source_index]
                    if u in total:
                        raise Exception()
                    total.append(u)
                    prev.append(u)
                except Exception:
                    break
            items = json.loads(source)
            items = [i for i in items+next+prev][:40]
            header = "Furk It"
            header2 = header.upper()
            progressDialog = xbmcgui.DialogProgress()
            progressDialog.create(header, '')
            progressDialog.update(0)
            block = None
            for i in range(len(items)):
                try:
                    try:
                        if progressDialog.iscanceled():
                            break
                        progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['label']), str(' '))
                    except Exception:
                        progressDialog.update(int((100 / float(len(items))) * i), str(header2), str(items[i]['label']))
                    if items[i]['source'] == block:
                        raise Exception()
                    w = Thread(self.resolve_sources, items[i])
                    w.start()
                    offset = 60 * 2 if items[i].get('source') in ['hugefiles.net', 'kingfiles.net', 'openload.io', 'openload.co', 'oload.tv', 'thevideo.me', 'vidup.me', 'streamin.to', 'torba.se'] else 0
                    m = ''
                    for x in range(3600):
                        try:
                            if xbmc.abortRequested is True:
                                return sys.exit()
                            if progressDialog.iscanceled():
                                return progressDialog.close()
                        except Exception:
                            pass
                        k = xbmc.getCondVisibility('Window.IsActive(virtualkeyboard)')
                        if k:
                            m += '1'
                            m = m[-1]
                        if (w.is_alive() is False or x > 30 + offset) and not k:
                            break
                        k = xbmc.getCondVisibility('Window.IsActive(yesnoDialog)')
                        if k:
                            m += '1'
                            m = m[-1]
                        if (w.is_alive() is False or x > 30 + offset) and not k:
                            break
                        time.sleep(0.5)
                    for x in range(30):
                        try:
                            if xbmc.abortRequested is True:
                                return sys.exit()
                            if progressDialog.iscanceled():
                                return progressDialog.close()
                        except Exception:
                            pass
                        if m == '':
                            break
                        if w.is_alive() is False:
                            break
                        time.sleep(0.5)
                    if w.is_alive() is True:
                        block = items[i]['source']
                    if self.url is None:
                        raise Exception()
                    try:
                        progressDialog.close()
                    except Exception:
                        pass
                    xbmc.sleep(200)
                    close_all_dialog()

                    if items[i].get('scrape_provider') == 'furk':
                        auto_resolve = settings.auto_resolve()
                        if auto_resolve == False:
                            if i != 0: auto_resolve = True
                        if auto_resolve:
                            meta = json.loads(window.getProperty('furkit_media_meta'))
                            filtering_list = seas_ep_query_list(meta['season'], meta['episode']) if meta['vid_type'] == 'episode' else ''
                            t_files = t_file_browser(items[i].get("id"), filtering_list)
                            url = t_files[0]['url_dl']
                            self.url = url
                        else:
                            return self.furkTFile(items[i].get("id"))

                    FurkitPlayer().run(self.url)
                    return self.url
                except Exception:
                    pass
            try:
                progressDialog.close()
            except Exception:
                pass
        except Exception:
            pass

    def furkTFile(self, file_id):
        from resources.lib.modules.furk_api import FurkAPI
        from resources.lib.indexers.furk import get_release_quality
        hide_busy_dialog()
        close_all_dialog()
        t_files = FurkAPI().t_files(file_id)
        t_files = [i for i in t_files if 'video' in i['ct'] and 'bitrate' in i]
        meta = json.loads(window.getProperty('furkit_media_meta'))
        from_library = meta.get('from_library', False)
        not_widget = xbmc.getInfoLabel('Container.PluginName')
        use_dialog = True if from_library or not not_widget else settings.use_dialog()
        display_list = []
        if use_dialog:
            display_list = ['%02d | [B]%s[/B] | [B]%.2f GB[/B] | [I]%s[/I]' % \
                            (count, get_release_quality(i['name'], i['url_dl'], t_file='yep')[0],
                            float(i['size'])/1073741824,
                            clean_file_name(i['name']).upper()) for count, i in enumerate(t_files, 1)]
            chosen = dialog.select("Furk It Results", display_list)
            if chosen < 0: return None
            chosen_result = t_files[chosen]
            url_dl = chosen_result['url_dl']
            return xbmc.executebuiltin('XBMC.RunPlugin(%s)' % build_url({'mode': 'media_play', 'url': url_dl}))
        for count, item in enumerate(t_files, 1):
            try:
                cm = []
                url_params = {'mode': 'media_play', 'url': item['url_dl']}
                url = build_url(url_params)
                name = clean_file_name(item['name'])
                video_quality, video_type = get_release_quality(item['name'], item['url_dl'], t_file='yep')
                json_meta = json.dumps(meta)
                display_name = '%02d | [B]%s[/B] | [B]%s[/B] | [B]%.2f GB[/B] | [I]%s[/I]' % (count, video_quality, video_type, float(item['size'])/1073741824, name.upper())
                listitem = xbmcgui.ListItem(display_name)
                listitem.setArt({'poster': meta.get('poster', ''), 'thumb': meta.get('poster', ''), 'fanart': meta.get('fanart', '')})
                playback_params = {'mode': 'playback_menu', 'from_results': True}
                down_file_params = {'mode': 'download_file', 'name': item['name'], 'url': item['url_dl'], 'meta': json_meta}
                cm.append(("[B]Options[/B]",'XBMC.RunPlugin(%s)' % build_url(playback_params)))
                cm.append(("[B]Download File[/B]",'XBMC.RunPlugin(%s)' % build_url(down_file_params)))
                listitem.addContextMenuItems(cm)
                if meta.get('vid_type') == 'movie': listitem.setInfo('video', {'title': meta.get('title', ''), 'year': meta.get('year', ''), 'plot': meta.get('plot', '')})
                else: listitem.setInfo('video', {'title': meta['rootname'], 'plot': meta.get('plot', '')})
                xbmcplugin.addDirectoryItem(__handle__, url, listitem, isFolder=True)
            except: pass
        xbmcplugin.setContent(__handle__, 'files')
        xbmcplugin.endOfDirectory(__handle__)
        setView('view.pack_results')

    def play_auto(self):
        meta = json.loads(window.getProperty('furkit_media_meta'))
        from_library = meta.get('from_library', 'False')
        items = json.loads(window.getProperty('furkit_search_results'))
        items = [i for i in items if not i.get('uncached', False)]
        filter = [i for i in items if i['source'].lower() in ['hugefiles.net', 'kingfiles.net', 'openload.io', 'openload.co', 'oload.tv', 'thevideo.me', 'vidup.me', 'streamin.to', 'torba.se'] and i['debrid'] == '']
        items = [i for i in items if i not in filter]
        items = [i for i in items if ('autoplay' in i and i['autoplay'] is True) or 'autoplay' not in i]
        u = None
        header = "Furk It"
        header2 = header.upper()
        try:
            progressDialog = xbmcgui.DialogProgress()
            progressDialog.create(header, '')
            progressDialog.update(0)
        except Exception:
            pass
        for i in range(len(items)):
            try:
                if progressDialog.iscanceled():
                    break
                progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['label']), str(' '))
            except Exception:
                progressDialog.update(int((100 / float(len(items))) * i), str(header2), str(items[i]['label']))
            try:
                if xbmc.abortRequested is True:
                    return sys.exit()
                if items[i].get('scrape_provider') == 'furk':
                    meta = json.loads(window.getProperty('furkit_media_meta'))
                    filtering_list = seas_ep_query_list(meta['season'], meta['episode']) if meta['vid_type'] == 'episode' else ''
                    t_files = t_file_browser(items[i].get("id"), filtering_list)
                    url = t_files[0]['url_dl']
                    self.url = url
                else:
                    url = self.resolve_sources(items[i])
                if u is None:
                    u = url
                if url is not None:
                    break
            except Exception:
                pass
        try:
            progressDialog.close()
        except Exception:
            pass
        xbmc.executebuiltin("RunPlugin(%s)" % build_url({'mode': 'media_play', 'url': self.url}))
        return u

    def resolve_sources(self, item, info=False):
        try:
            if item['scrape_provider'] == 'furk':
                url = item.get("id")
                self.url = url
                return url
            if item['scrape_provider'] in ('local', 'easynews'):
                url = item['url_dl']
                self.url = url
                return url
            from urlparse import parse_qsl
            from tikiscrapers.modules import client, debrid
            from tikiscrapers import sources
            try:
                import resolveurl
            except Exception:
                pass
            self.sourceDict = sources()
            self.url = None
            u = url = item['url']
            d = item['debrid']
            direct = item['direct']
            local = item.get('local', False)
            provider = item['provider']
            call = [i[1] for i in self.sourceDict if i[0] == provider][0]
            u = url = call.resolve(url)
            if url is None or ('://' not in str(url) and not local and 'magnet:' not in str(url)):
                raise Exception()
            if not local:
                url = url[8:] if url.startswith('stack:') else url
                urls = []
                for part in url.split(' , '):
                    u = part
                    if not d == '':
                        part = debrid.resolver(part, d)
                    elif direct is not True:
                        hmf = resolveurl.HostedMediaFile(url=u, include_disabled=True, include_universal=False)
                        if hmf.valid_url() is True:
                            part = hmf.resolve()
                    urls.append(part)
                url = 'stack://' + ' , '.join(urls) if len(urls) > 1 else urls[0]
            if url is False or url is None:
                raise Exception()
            ext = url.split('?')[0].split('&')[0].split('|')[0].rsplit('.')[-1].replace('/', '').lower()
            if ext == 'rar':
                raise Exception()
            try:
                headers = url.rsplit('|', 1)[1]
            except Exception:
                headers = ''
            headers = urllib.quote_plus(headers).replace('%3D', '=') if ' ' in headers else headers
            headers = dict(parse_qsl(headers))
            if url.startswith('http') and '.m3u8' in url:
                result = client.request(url.split('|')[0], headers=headers, output='geturl', timeout='20')
                if result is None:
                    raise Exception()
            elif url.startswith('http'):
                result = client.request(url.split('|')[0], headers=headers, output='chunk', timeout='20')
                if result is None:
                    raise Exception()
            self.url = url
            return url
        except Exception:
            return
