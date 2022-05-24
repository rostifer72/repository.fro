# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 05-06-2019 by JewBMX in Scrubs.

import re,base64
from tikiscrapers.modules import cleantitle,source_utils,cfscrape


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['watchseries.unblocker.cc']
        self.base_link = 'https://watchseries.unblocker.cc'
        self.search_link = 'https://watchseries.unblocker.cc/episode/%s_s%s_e%s.html'
        self.scraper = cfscrape.create_scraper()


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = cleantitle.geturl(tvshowtitle)
            url = url.replace('-', '_')
            return url
        except:
            return


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url == None: return
            url = self.search_link % (url,season,episode)
            return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            if url == None: return sources
            r = self.scraper.get(url).content
            match = re.compile('cale\.html\?r=(.+?)" class="watchlink" title="(.+?)"').findall(r)
            for url, host in match:
                url  = base64.b64decode(url)
                if url in str(sources): continue
                info = source_utils.check_url(url)
                quality = source_utils.check_url(url)
                valid, host = source_utils.is_host_valid(host, hostDict)
                if host in str(sources): continue
                if valid:
                    sources.append({'source': host, 'quality': quality, 'language': 'en', 'info': info, 'url': url, 'direct': False, 'debridonly': False}) 
        except Exception:
            return
        return sources


    def resolve(self, url):
        return url

