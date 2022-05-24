# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 05-06-2019 by JewBMX in Scrubs.
# -Update by Tempest (Pulls movies that it would'nt pull)
# -Ghetto Mix of both Ganool123 Scrapers.

import re,urllib,urlparse
from tikiscrapers.modules import client,cleantitle,debrid,source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['ganool.ws', 'ganol.si', 'ganool123.com']
        self.base_link = 'https://www2.ganool123.com'
        self.search_link = '/search/?q=%s'


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'title': title, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if url == None: return sources
            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            q = '%s' % cleantitle.get_gan_url(data['title'])
            hunt = self.base_link + self.search_link % q
            if debrid.status() == True:
                r = client.request(hunt)
                v = re.compile('<a href="(.+?)" class="ml-mask jt" title="(.+?)">\n<span class=".+?">(.+?)</span>').findall(r)
                for url, check, quality in v:
                    t = '%s (%s)' % (data['title'], data['year'])
                    if t not in check: raise Exception()
                    r = client.request(url + '/watch.html')
                    r = re.compile('<a target=".+?" href="(.+?)">').findall(r)
                    for url in r:
                        if 'Download' in url: continue
                        if url in str(sources): continue
                        quality = source_utils.check_url(quality)
                        valid, host = source_utils.is_host_valid(url, hostDict)
                        if valid:
                            sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url, 'direct': False, 'debridonly': True})
            r = client.request(hunt)
            v = re.compile('<a href="(.+?)" class="ml-mask jt" title="(.+?)">\n<span class=".+?">(.+?)</span>').findall(r)
            for url, check, quality in v:
                t = '%s (%s)' % (data['title'], data['year'])
                if t not in check: raise Exception()
                r = client.request(url + '/watch.html')
                url = re.compile('<iframe .+? src="(.+?)"').findall(r)[0]
                if url in str(sources): continue
                quality = source_utils.check_url(quality)
                valid, host = source_utils.is_host_valid(url, hostDict)
                if valid:
                    sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url, 'direct': False, 'debridonly': False})
            return sources
        except:
            return sources


    def resolve(self, url):
        return url

