# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 02-24-2019 by JewBMX in Scrubs.

import re,urllib,urlparse
from tikiscrapers.modules import cleantitle,client,control,debrid,source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['eztv.io']
        self.base_link = 'https://eztv.io/'
        self.search_link = '/search/%s'
        self.min_seeders = int(control.setting('torrent.min.seeders'))

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
            url = urllib.urlencode(url)
            return url
        except Exception:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode): 
        try:
            if url == None:
                return
            url = urlparse.parse_qs(url)
            url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
            url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
            url = urllib.urlencode(url)
            return url
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            if url == None: return sources
            if debrid.status() is False: raise Exception()
            if debrid.tor_enabled() is False: raise Exception()

            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

            title = data['tvshowtitle']

            hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode']))
            query = '%s S%02dE%02d' % ( data['tvshowtitle'], int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else '%s %s' % (data['title'], data['year'])
            query = re.sub('(\\\|/| -|:|;|\*|\?|"|<|>|\|)', ' ', query)

            url = self.search_link % (urllib.quote_plus(query).replace('+', '-'))
            url = urlparse.urljoin(self.base_link, url)

            html = client.request(url)
            try:
                results = client.parseDOM(html, 'table', attrs={'class': 'forum_header_border'})
                for result in results:
                    if 'magnet:' in result:
                        results = result
                        break
            except:
                return sources
            rows = re.findall('<tr name="hover" class="forum_header_border">(.+?)</tr>', results, re.DOTALL)
            if rows == None:
                return sources
            for entry in rows:
                try:
                    try:
                        columns = re.findall('<td\s.+?>(.+?)</td>', entry, re.DOTALL)
                        derka = re.findall('href="magnet:(.+?)" class="magnet" title="(.+?)"', columns[2], re.DOTALL)[0]
                        name = derka[1]
                        link = 'magnet:%s' % (str(client.replaceHTMLCodes(derka[0]).split('&tr')[0]))
                        t = name.split(hdlr)[0]
                        if not cleantitle.get(re.sub('(|)', '', t)) == cleantitle.get(title):
                            continue
                    except:
                        continue
                    y = re.findall('[\.|\(|\[|\s](\d{4}|S\d*E\d*|S\d*)[\.|\)|\]|\s]', name)[-1].upper()
                    if not y == hdlr:
                        continue
                    try:
                        seeders = int(re.findall('<font color=".+?">(.+?)</font>', columns[5], re.DOTALL)[0])
                    except:
                        continue
                    if self.min_seeders > seeders:
                        continue
                    quality, info = source_utils.get_release_quality(name, name)
                    try:
                        size = re.findall('((?:\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|MB|MiB))', name)[-1]
                        div = 1 if size.endswith(('GB', 'GiB')) else 1024
                        size = float(re.sub('[^0-9|/.|/,]', '', size)) / div
                        size = '%.2f GB' % size
                        info.append(size)
                    except Exception:
                        pass
                    info = ' | '.join(info)
                    sources.append({'source': 'Torrent', 'quality': quality, 'language': 'en', 'url': link, 'info': info, 'direct': False, 'debridonly': True})
                except:
                    continue
            check = [i for i in sources if not i['quality'] == 'CAM']
            if check:
                sources = check
            return sources
        except:
            return sources

    def resolve(self, url):
        return url
