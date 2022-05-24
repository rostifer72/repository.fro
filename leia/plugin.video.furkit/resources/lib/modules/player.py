# -*- coding: utf-8 -*-
import xbmc, xbmcplugin, xbmcgui
import sys
import urllib
import json
from urlparse import parse_qsl
from resources.lib.modules.indicators_bookmarks import detect_bookmark, erase_bookmark
from resources.lib.modules.nav_utils import hide_busy_dialog, close_all_dialog
from resources.lib.modules.utils import sec2time
import settings
# from resources.lib.modules.utils import logger

window = xbmcgui.Window(10000)

class FurkitPlayer(xbmc.Player):
    def __init__ (self):
        xbmc.Player.__init__(self)
        self.info = None
        self.delete_playcount = True
        self.set_resume = settings.set_resume()
        self.set_watched = settings.set_watched()
        self.set_nextep = settings.set_nextep()

    def run(self, url=None):
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        rootname = params.get('rootname', '')
        try:
            if rootname == 'nill':
                url = urllib.unquote(params.get("url"))
                self.play(url)
                return
            url = url if url else params.get("url") if 'url' in params else None
            url = urllib.unquote(url)
            if not url: return
            self.meta = json.loads(window.getProperty('furkit_media_meta'))
            self.MetaFromNextep = self.meta
            rootname = self.meta['rootname'] if 'rootname' in self.meta else ''
            bookmark = self.bookmarkChoice()
            self.meta.update({'url': url, 'bookmark': bookmark})
            listitem = xbmcgui.ListItem(path=url)
            try:
                listitem.setProperty('StartPercent', str(self.meta.get('bookmark')))
                listitem.setArt({'poster': self.meta.get('poster'), 'fanart': self.meta.get('fanart'),
                                'banner': self.meta.get('banner'), 'clearlogo': self.meta.get('clearlogo'),
                                'landscape': self.meta.get('landscape')})
                if self.meta['vid_type'] == 'movie':
                    listitem.setInfo(
                        'video', {'mediatype': 'movie', 'trailer': str(self.meta['trailer']),
                        'title': self.meta['title'], 'size': '0', 'duration': self.meta['duration'],
                        'plot': self.meta['plot'], 'rating': self.meta['rating'], 'premiered': self.meta['premiered'],
                        'studio': self.meta['studio'],'year': self.meta['year'], 'genre': self.meta['genre'],
                        'tagline': self.meta['tagline'], 'code': self.meta['imdb_id'], 'imdbnumber': self.meta['imdb_id'],
                        'director': self.meta['director'], 'writer': self.meta['writer'], 'votes': self.meta['votes']})
                elif self.meta['vid_type'] == 'episode':
                    listitem.setInfo(
                        'video', {'mediatype': 'episode', 'trailer': str(self.meta['trailer']), 'title': self.meta['ep_name'],
                        'tvshowtitle': self.meta['title'], 'size': '0', 'plot': self.meta['plot'], 'year': self.meta['year'],
                        'premiered': self.meta['premiered'], 'genre': self.meta['genre'], 'season': int(self.meta['season']),
                        'episode': int(self.meta['episode']), 'duration': str(self.meta['duration']), 'rating': self.meta['rating']})
            except: pass
            self.play(url, listitem)
            self.monitor()
        except: return

    def bookmarkChoice(self):
        season = self.meta.get('season', '')
        episode = self.meta.get('episode', '')
        if season == 0: season = ''
        if episode == 0: episode = ''
        bookmark = 0
        try: resume_point, curr_time = detect_bookmark(self.meta['vid_type'], self.meta['media_id'], season, episode)
        except: resume_point = 0
        if resume_point > 0:
            percent = resume_point
            raw_time = float(curr_time)
            time = sec2time(raw_time, n_msec=0)
            bookmark = self.getResumeStatus(time, percent, bookmark, self.meta.get('from_library', None))
            if bookmark == 0: erase_bookmark(self.meta['vid_type'], self.meta['media_id'], season, episode)
        return bookmark

    def getResumeStatus(self, time, percent, bookmark, from_library):
        dialog = xbmcgui.Dialog()
        resume_type = settings.resume_type(from_library)
        xbmc.sleep(600)
        choice = dialog.contextmenu(['Resume from [B]%s[/B]' % time, 'Start from Beginning']) if resume_type == "Context Menu" else dialog.yesno('Resume Point Detected', 'Resume from [B]%s?[/B]' % time, '', '', 'Yes', 'No') if resume_type == "Yes No Dialog" else 0
        return percent if choice == 0 else bookmark

    def monitor(self):
        self.library_setting = 'library' if 'from_library' in self.meta else None
        self.autoplay_next_episode = True if self.meta['vid_type'] == 'episode' and settings.autoplay_next_episode(self.library_setting) else False
        while not self.isPlayingVideo():
            xbmc.sleep(100)
        while self.isPlayingVideo():
            try:
                self.total_time = self.getTotalTime()
                self.curr_time = self.getTime()
                xbmc.sleep(100)
                if self.autoplay_next_episode and round(float(self.curr_time/self.total_time*100),1) >= self.set_nextep and not self.info:
                    self.nextEpisode()
            except: pass
        self.mediaWatchedMarker()

    def nextEpisode(self):
        from resources.lib.modules.next_episode import next_episode_from_playback
        self.info = next_episode_from_playback(self.meta, from_library=self.library_setting)
        if self.info and not 'pass' in self.info:
            self.delete_playcount = False
            xbmc.executebuiltin("RunPlugin({0})".format(self.info['url']))
            self.getMetaFromNextep()
        else: pass

    def mediaWatchedMarker(self):
        try:
            if self.delete_playcount: window.clearProperty('playcount')
            resume_point = round(float(self.curr_time/self.total_time*100),1)
            if self.set_resume < resume_point < self.set_watched:
                from resources.lib.modules.indicators_bookmarks import set_bookmark
                set_bookmark(self.meta['vid_type'], self.meta['media_id'], self.curr_time, self.total_time, self.meta.get('season', ''), self.meta.get('episode', ''))
            elif resume_point > self.set_watched:
                from resources.lib.modules.nav_utils import build_url
                if self.meta['vid_type'] == 'movie':
                    watched_params = {"mode": "mark_movie_as_watched_unwatched", "action": 'mark_as_watched',
                    "media_id": self.meta['media_id'], "title": self.meta['title'], "year": self.meta['year']}
                else:
                    watched_params = {"mode": "mark_episode_as_watched_unwatched", "action": "mark_as_watched",
                    "season": self.MetaFromNextep['season'], "episode": self.MetaFromNextep['episode'], "media_id": self.MetaFromNextep['media_id'],
                    "title": self.MetaFromNextep['title'], "year": self.MetaFromNextep['year'], "imdb_id": self.MetaFromNextep['imdb_id']}
                xbmc.executebuiltin("RunPlugin(%s)" % build_url(watched_params))
            else: pass
        except: pass

    def getMetaFromNextep(self):
        try:
            self.MetaFromNextep = json.loads(window.getProperty('furkit_previous_meta_from_nextep'))
            window.clearProperty('furkit_previous_meta_from_nextep')
        except: pass
        return self.MetaFromNextep

    def onAVStarted(self):
        close_all_dialog()

    def onPlayBackStarted(self):
        close_all_dialog()

    def playAudioAlbum(self, t_files=None, name=None, from_seperate=False):
        import os
        import xbmcaddon
        from resources.lib.modules.utils import clean_file_name, batch_replace, to_utf8
        from resources.lib.modules.nav_utils import setView
        __addon_id__ = 'plugin.video.furkit'
        __addon__ = xbmcaddon.Addon(id=__addon_id__)
        __handle__ = int(sys.argv[1])
        addon_dir = xbmc.translatePath(__addon__.getAddonInfo('path'))
        icon_directory = settings.get_theme()
        default_furk_icon = os.path.join(icon_directory, 'furk.png')
        formats = ('.3gp', ''), ('.aac', ''), ('.flac', ''), ('.m4a', ''), ('.mp3', ''), \
        ('.ogg', ''), ('.raw', ''), ('.wav', ''), ('.wma', ''), ('.webm', ''), ('.ra', ''), ('.rm', '')
        FURK_FILES_VIEW  = settings.SETTING_FURK_FILES_VIEW
        params = dict(parse_qsl(sys.argv[2].replace('?','')))
        furk_files_list = []
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        playlist.clear()
        if from_seperate: t_files = [i for i in t_files if clean_file_name(i['path']) == params.get('item_path')]
        for item in t_files:
            try:
                name = item['path'] if not name else name
                if not 'audio' in item['ct']: continue
                url = item['url_dl']
                track_name = clean_file_name(batch_replace(to_utf8(item['name']), formats))
                listitem = xbmcgui.ListItem(track_name)
                listitem.setThumbnailImage(default_furk_icon)
                listitem.setInfo(type='music',infoLabels={'title': track_name, 'size': int(item['size']), 'album': clean_file_name(batch_replace(to_utf8(name), formats)),'duration': item['length']})
                listitem.setProperty('mimetype', 'audio/mpeg')
                playlist.add(url, listitem)
                if from_seperate: furk_files_list.append((url, listitem, False))
            except: pass
        self.play(playlist)
        if from_seperate:
            xbmcplugin.addDirectoryItems(__handle__, furk_files_list, len(furk_files_list))
            setView(FURK_FILES_VIEW)
            xbmcplugin.endOfDirectory(__handle__)





