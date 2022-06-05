import sys
import xbmcaddon
import requests, json
import time, datetime
from resources.lib.modules import furkitcache
from resources.lib.modules.utils import to_utf8
# from resources.lib.modules.utils import logger

__addon__ = xbmcaddon.Addon(id='plugin.video.furkit')
_cache = furkitcache.FurkItCache()

class FurkAPI:
    def __init__(self):
        self.base_link = 'https://www.furk.net'
        self.login_link = "/api/login/login?login=%s&pwd=%s"
        self.file_get_video_link = "/api/file/get?api_key=%s&type=video"
        self.file_get_audio_link = "/api/file/get?api_key=%s&type=audio"
        self.file_link_link = "/api/file/link?api_key=%s&id=%s"
        self.file_unlink_link = "/api/file/unlink?api_key=%s&id=%s"
        self.file_protect_link = "/api/file/protect?api_key=%s&id=%s&is_protected=%s"
        self.add_uncached_link = "/api/dl/add?api_key=%s&info_hash=%s"
        self.active_dl_link = "/api/dl/get?api_key=%s&dl_status=active"
        self.failed_dl_link = "/api/dl/get?api_key=%s&dl_status=failed"
        self.remove_dl_link = "/api/dl/unlink?api_key=%s&id=%s"
        self.account_info_link = "/api/account/info?api_key=%s"
        self.search_link = "/api/plugins/metasearch?api_key=%s&q=%s&cached=all" \
                                "&match=%s&moderated=%s%s&sort=relevance&type=video&offset=0&limit=%s"
        self.search_direct_link = "/api/plugins/metasearch?api_key=%s&q=%s&cached=all" \
                                "&sort=cached&type=video&offset=0&limit=%s"
        self.tfile_link = "/api/file/get?api_key=%s&t_files=1&id=%s"
        self.user_name = __addon__.getSetting('furk_login')
        self.user_pass = __addon__.getSetting('furk_password')
        self.furk_limit = __addon__.getSetting('furk.limit')
        self.furk_limit_direct = __addon__.getSetting('furk.limit.direct')
        self.mod_level = __addon__.getSetting('furk.mod.level').lower()

    def get_api(self):
        try:
            if not self.user_name or not self.user_pass:
                __addon__.setSetting('furk_api_key', '')
            api_key = __addon__.getSetting('furk_api_key')
            if not api_key:
                if not self.user_name or not self.user_pass:
                    return
                else:
                    link = (self.base_link + self.login_link % (self.user_name, self.user_pass))
                    s = requests.Session()
                    p = s.post(link)
                    p = json.loads(p.text)
                    if p['status'] == 'ok':
                        api_key = p['api_key']
                        __addon__.setSetting('furk_api_key', api_key)
                    else:
                        pass
            return api_key
        except: pass

    def search(self, query):
        try:
            api_key = self.get_api()
            if not api_key: return
            search_in = '' if '@files' in query else '&attrs=name'
            link = (self.base_link + self.search_link \
                % (api_key, query, 'extended', self.mod_level, search_in, self.furk_limit))
            cache = _cache.get("furkit_%s_%s" % ('FURK_SEARCH', query))
            if cache:
                files = cache
            else:
                p = self._get(link)
                if p['status'] != 'ok':
                    return
                files = p['files']
                _cache.set("furkit_%s_%s" % ('FURK_SEARCH', query), files,
                    expiration=datetime.timedelta(hours=2))
            return files
        except: return

    def direct_search(self, query):
        try:
            api_key = self.get_api()
            if not api_key: return
            link = (self.base_link + self.search_direct_link % (api_key, query, self.furk_limit_direct))
            cache = _cache.get("furkit_%s_%s" % ('FURK_SEARCH_DIRECT', query))
            if cache:
                files = cache
            else:
                p = self._get(link)
                if p['status'] != 'ok':
                    return
                files = p['files']
                _cache.set("furkit_%s_%s" % ('FURK_SEARCH_DIRECT', query), files,
                    expiration=datetime.timedelta(hours=2))
            return files
        except: return

    def t_files(self, file_id):
        try:
            cache = _cache.get("furkit_%s_%s" % ('FURK_T_FILE', file_id))
            if cache:
                t_files = cache
            else:
                api_key = self.get_api()
                link = (self.base_link + self.tfile_link % (api_key, file_id))
                p = self._get(link)
                if p['status'] != 'ok' or p['found_files'] != '1': return
                t_files = p['files']
                t_files = (t_files[0])['t_files']
                _cache.set("furkit_%s_%s" % ('FURK_T_FILE', file_id), t_files,
                    expiration=datetime.timedelta(hours=2))
            return t_files
        except: return

    def file_get_video(self):
        try:
            api_key = self.get_api()
            link = (self.base_link + self.file_get_video_link % (api_key))
            p = self._get(link)
            files = p['files']
            return files
        except: return

    def file_get_audio(self):
        try:
            api_key = self.get_api()
            link = (self.base_link + self.file_get_audio_link % (api_key))
            p = self._get(link)
            files = p['files']
            return files
        except: return

    def file_get_active(self):
        try:
            api_key = self.get_api()
            link = (self.base_link + self.active_dl_link % (api_key))
            p = self._get(link)
            files = p['torrents']
            return files
        except: return

    def file_get_failed(self):
        try:
            api_key = self.get_api()
            link = (self.base_link + self.failed_dl_link % (api_key))
            p = self._get(link)
            files = p['torrents']
            return files
        except: return

    def file_link(self, item_id):
        try:
            api_key = self.get_api()
            link = (self.base_link + self.file_link_link % (api_key, item_id))
            return self._get(link)
        except: return

    def file_unlink(self, item_id):
        try:
            api_key = self.get_api()
            link = (self.base_link + self.file_unlink_link % (api_key, item_id))
            return self._get(link)
        except: return

    def download_unlink(self, item_id):
        try:
            api_key = self.get_api()
            link = (self.base_link + self.remove_dl_link % (api_key, item_id))
            return self._get(link)
        except: return

    def file_protect(self, item_id, is_protected):
        try:
            api_key = self.get_api()
            link = (self.base_link + self.file_protect_link % (api_key, item_id, is_protected))
            return self._get(link)
        except: return

    def add_uncached(self, item_id):
        try:
            api_key = self.get_api()
            link = (self.base_link + self.add_uncached_link % (api_key, item_id))
            return self._get(link)
        except: return

    def account_info(self):
        try:
            api_key = self.get_api()
            link = (self.base_link + self.account_info_link % (api_key))
            return self._get(link)
        except: return

    def _get(self, link):
        s = requests.Session()
        p = s.get(link)
        return to_utf8(json.loads(p.text))
