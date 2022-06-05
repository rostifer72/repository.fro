# -*- coding: utf-8 -*-
import xbmc, xbmcaddon
import os
import datetime
import json
import random
import re
import sys
import time
import urllib
import urlparse
from tikiscrapers.modules import cleantitle, control, debrid, source_utils, workers
# from resources.lib.modules.utils import logger
try:
    from sqlite3 import dbapi2 as database
except Exception:
    from pysqlite2 import dbapi2 as database
try:
    import resolveurl
except Exception:
    pass

__furkit__ = xbmcaddon.Addon(id='plugin.video.furkit')
__external__ = xbmcaddon.Addon(id='script.module.tikiscrapers')

class ExternalSource:
    def __init__(self):
        self.exportSettings()
        self.getConstants()
        self.scrape_provider = 'external'
        self.sources = []

    def results(self, info):
        results = self.getSources((info['title'] if info['db_type'] == 'movie' else info['ep_name']),
                            info['year'], info['imdb_id'], info['tvdb_id'], info['season'], info['episode'],
                            (info['title'] if info['db_type'] == 'episode' else None), info['premiered'])
        return results

    def getSources(self, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered, quality='HD', timeout=30):
        meta = json.loads(control.window.getProperty('furkit_media_meta'))
        background = True if meta.get('background', 'false') == 'true' else False
        content = 'movie' if tvshowtitle is None else 'episode'
        if not background:
            progressDialog = control.progressDialog
            if content == 'movie':
                progressTitle = '%s (%s)' % (title, year) if self.progressHeading == 1 else self.moduleProvider
            else:
                progressTitle = '%s - %dx%02d' % (tvshowtitle, season, episode) if self.progressHeading == 1 else self.moduleProvider
            progressDialog.create(progressTitle, '')
            progressDialog.update(0)
        sourceDict = self.sourceDict
        if not background: progressDialog.update(0, 'Preparing sources')
        if content == 'movie':
            sourceDict = [(i[0], i[1], getattr(i[1], 'movie', None)) for i in sourceDict]
        else:
            sourceDict = [(i[0], i[1], getattr(i[1], 'tvshow', None)) for i in sourceDict]
        sourceDict = [(i[0], i[1]) for i in sourceDict if not i[2] is None]
        try:
            sourceDict = [(i[0], i[1], control.setting('provider.' + i[0])) for i in sourceDict]
        except Exception:
            sourceDict = [(i[0], i[1], 'true') for i in sourceDict]
        sourceDict = [(i[0], i[1]) for i in sourceDict if not i[2] == 'false']

        sourceDict = [(i[0], i[1], i[1].priority) for i in sourceDict]

        random.shuffle(sourceDict)
        sourceDict = sorted(sourceDict, key=lambda i: i[2])
        threads = []
        if content == 'movie':
            title = cleantitle.normalize(title)
            for i in sourceDict:
                threads.append(workers.Thread(self.getMovieSource, title, title, [], year, imdb, i[0], i[1]))
        else:
            tvshowtitle = cleantitle.normalize(tvshowtitle)
            for i in sourceDict:
                threads.append(workers.Thread(self.getEpisodeSource, title, year, imdb, tvdb, season,
                                              episode, tvshowtitle, tvshowtitle, [], premiered, i[0], i[1]))
        s = [i[0] + (i[1],) for i in zip(sourceDict, threads)]
        s = [(i[3].getName(), i[0], i[2]) for i in s]
        mainsourceDict = [i[0] for i in s if i[2] == 0]
        sourcelabelDict = dict([(i[0], i[1].upper()) for i in s])
        [i.start() for i in threads]
        string1 = 'Time elapsed: %s seconds'
        string2 = '%s seconds'
        string3 = 'Remaining providers: %s'
        string4 = 'Total'
        string5 = 'Waiting for'
        string6 = '[COLOR=blue][B]Int[/B][/COLOR]'
        string7 = '[COLOR=lime][B]Ext[/B][/COLOR]'
        try: timeout = int(__furkit__.getSetting('scrapers.timeout.1'))
        except Exception: pass
        line1 = line2 = line3 = ""
        pre_emp =  __furkit__.getSetting('preemptive.termination')
        pre_emp_limit = __furkit__.getSetting('preemptive.limit')
        source_4k = 0
        source_1080 = 0
        source_720 = 0
        source_sd = 0
        total = 0
        total_format = '[COLOR %s][B]%s[/B][/COLOR]'
        pdiag_format = ' 4K: %s | 1080p: %s | 720p: %s | SD: %s | %s: %s'.split('|')
        # pdiag2_format = ' Library: %s | Furk: %s | Easynews: %s | %s: %s'.split('|')
        # pdiag_bg_format = '4K:%s(%s)|1080p:%s(%s)|720p:%s(%s)|SD:%s(%s)|T:%s(%s)'.split('|')
        if background:
            for i in range(0, timeout + 2):
                time.sleep(1)
        else:
            for i in range(0, 4 * timeout):
                if str(pre_emp) == 'true':
                    if total >= int(pre_emp_limit): break
                try:
                    if xbmc.abortRequested == True: return sys.exit()
                    try:
                        if progressDialog.iscanceled():
                            break
                    except Exception:
                        pass
                    self.internalResults()
                    if len(self.sources) > 0:
                        source_4k = len([e for e in self.sources if e['quality'] == '4K'])
                        source_1080 = len([e for e in self.sources if e['quality'] in ['1440p', '1080p']])
                        source_720 = len([e for e in self.sources if e['quality'] in ['720p', 'HD']])
                        source_sd = len([e for e in self.sources if e['quality'] == 'SD'])
                        total = source_4k + source_1080 + source_720 + source_sd

                    internalSource_4k_label = total_format % ('blue', self.internalSources4K)
                    internalSource_1080_label = total_format % ('blue', self.internalSources1080p)
                    internalSource_720_label = total_format % ('blue', self.internalSources720p)
                    internalSource_sd_label = total_format % ('blue', self.internalSourcesSD)
                    internalSource_total_label = total_format % ('blue', self.internalSourcesTotal)
                    source_4k_label = total_format % ('lime', source_4k)
                    source_1080_label = total_format % ('lime', source_1080)
                    source_720_label = total_format % ('lime', source_720)
                    source_sd_label = total_format % ('lime', source_sd)
                    source_total_label = total_format % ('lime', total)

                    if (i / 2) < timeout:
                        try:
                            mainleft = [sourcelabelDict[x.getName()] for x in threads if x.is_alive() is
                                        True and x.getName() in mainsourceDict]
                            info = [sourcelabelDict[x.getName()] for x in threads if x.is_alive() is True]
                            if i >= timeout and len(mainleft) == 0 and len(self.sources) >= 100 * len(info):
                                break  # improve responsiveness
                            line1 = ('%s:' + '|'.join(pdiag_format)) % (string6, internalSource_4k_label, internalSource_1080_label,
                                                                  internalSource_720_label, internalSource_sd_label, str(string4), internalSource_total_label)
                            line2 = ('%s:' + '|'.join(pdiag_format)) % (string7, source_4k_label, source_1080_label,
                                                                  source_720_label, source_sd_label, str(string4), source_total_label)
                            if len(info) > 6:
                                line3 = string3 % (str(len(info)))
                            elif len(info) > 0:
                                line3 = string3 % (', '.join(info))
                            else:
                                break
                            percent = int(100 * float(i) / (2 * timeout) + 0.5)
                            progressDialog.update(max(1, percent), line1, line2, line3)
                        except:
                            pass
                    else:
                        try:
                            mainleft = [sourcelabelDict[x.getName()] for x in threads if x.is_alive() is
                                        True and x.getName() in mainsourceDict]
                            info = mainleft
                            if len(info) > 6:
                                line3 = 'Waiting for: %s' % (str(len(info)))
                            elif len(info) > 0:
                                line3 = 'Waiting for: %s' % (', '.join(info))
                            else:
                                break
                            percent = int(100 * float(i) / (2 * timeout) + 0.5) % 100
                            progressDialog.update(max(1, percent), line1, line2, line3)
                        except Exception:
                            break
                    time.sleep(0.5)
                except Exception:
                    pass
            try:
                progressDialog.close()
            except Exception:
                pass
        self.sourcesFilter()
        self.sourcesLabels()
        return self.sources

    def getMovieSource(self, title, localtitle, aliases, year, imdb, source, call):
        try:
            dbcon = database.connect(self.providerDatabase)
            dbcur = dbcon.cursor()
        except Exception:
            pass
        if imdb == '0':
            try:
                dbcur.execute(
                    "DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" %
                    (source, imdb, '', ''))
                dbcur.execute(
                    "DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" %
                    (source, imdb, '', ''))
                dbcon.commit()
            except Exception:
                pass
        try:
            sources = []
            dbcur.execute(
                "SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" %
                (source, imdb, '', ''))
            match = dbcur.fetchone()
            t1 = int(re.sub('[^0-9]', '', str(match[5])))
            t2 = int(datetime.datetime.now().strftime("%Y%m%d%H%M"))
            update = abs(t2 - t1) > 60
            if update is False:
                sources = eval(match[4].encode('utf-8'))
                return self.sources.extend(sources)
        except Exception:
            pass
        try:
            url = None
            dbcur.execute(
                "SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" %
                (source, imdb, '', ''))
            url = dbcur.fetchone()
            url = eval(url[4].encode('utf-8'))
        except Exception:
            pass
        try:
            if url is None:
                url = call.movie(imdb, title, localtitle, aliases, year)
            if url is None:
                raise Exception()
            dbcur.execute(
                "DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" %
                (source, imdb, '', ''))
            dbcur.execute("INSERT INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, '', '', repr(url)))
            dbcon.commit()
        except Exception:
            pass
        try:
            sources = []
            sources = call.sources(url, self.hostDict, self.hostprDict)
            if sources is None or sources == []:
                raise Exception()
            sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
            sources = self.sourcesUpdate(source, sources)
            self.sources.extend(sources)
            dbcur.execute(
                "DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" %
                (source, imdb, '', ''))
            dbcur.execute("INSERT INTO rel_src Values (?, ?, ?, ?, ?, ?)", (source, imdb, '',
                                                                            '', repr(sources), datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            dbcon.commit()
        except Exception:
            pass

    def getEpisodeSource(self, title, year, imdb, tvdb, season, episode, tvshowtitle, localtvshowtitle, aliases, premiered, source, call):
        try:
            dbcon = database.connect(self.providerDatabase)
            dbcur = dbcon.cursor()
        except Exception:
            pass
        try:
            sources = []
            dbcur.execute(
                "SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" %
                (source, imdb, season, episode))
            match = dbcur.fetchone()
            t1 = int(re.sub('[^0-9]', '', str(match[5])))
            t2 = int(datetime.datetime.now().strftime("%Y%m%d%H%M"))
            update = abs(t2 - t1) > 60
            if update is False:
                sources = eval(match[4].encode('utf-8'))
                return self.sources.extend(sources)
        except Exception:
            pass
        try:
            url = None
            dbcur.execute(
                "SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" %
                (source, imdb, '', ''))
            url = dbcur.fetchone()
            url = eval(url[4].encode('utf-8'))
        except Exception:
            pass
        try:
            if url is None:
                url = call.tvshow(imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year)
            if url is None:
                raise Exception()
            dbcur.execute(
                "DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" %
                (source, imdb, '', ''))
            dbcur.execute("INSERT INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, '', '', repr(url)))
            dbcon.commit()
        except Exception:
            pass
        try:
            ep_url = None
            dbcur.execute(
                "SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" %
                (source, imdb, season, episode))
            ep_url = dbcur.fetchone()
            ep_url = eval(ep_url[4].encode('utf-8'))
        except Exception:
            pass
        try:
            if url is None:
                raise Exception()
            if ep_url is None:
                ep_url = call.episode(url, imdb, tvdb, title, premiered, season, episode)
            if ep_url is None:
                raise Exception()
            dbcur.execute(
                "DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" %
                (source, imdb, season, episode))
            dbcur.execute("INSERT INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, season, episode, repr(ep_url)))
            dbcon.commit()
        except Exception:
            pass
        try:
            sources = []
            sources = call.sources(ep_url, self.hostDict, self.hostprDict)
            if sources is None or sources == []:
                raise Exception()
            sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
            sources = self.sourcesUpdate(source, sources)
            self.sources.extend(sources)
            dbcur.execute(
                "DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" %
                (source, imdb, season, episode))
            dbcur.execute("INSERT INTO rel_src Values (?, ?, ?, ?, ?, ?)", (source, imdb, season,
                                                                            episode, repr(sources), datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            dbcon.commit()
        except Exception:
            pass

    def sourcesFilter(self):
        removeDuplicates = __furkit__.getSetting('remove.duplicates')
        if removeDuplicates == '': removeDuplicates = 'false'
        sortProvider = __furkit__.getSetting('hosts.sort.provider')
        if sortProvider == '': sortProvider = 'false'
        debridOnly = __furkit__.getSetting('debrid.only')
        if debridOnly == '':  debridOnly = 'false'
        torrentEnabled = __furkit__.getSetting('torrent.enabled')
        if torrentEnabled == '':  torrentEnabled = 'false'
        sortTorrentTop = __furkit__.getSetting('torrent.sort.them.up')
        if sortTorrentTop == '': sortTorrentTop = 'false'
        captcha = __furkit__.getSetting('hosts.captcha')
        if captcha == '': captcha = 'true'
        if removeDuplicates == 'true':
            self.sources = list(self.sourcesRemoveDuplicates(self.sources))
        if sortProvider == 'true':
            self.sources = sorted(self.sources, key=lambda k: k['provider'])
        else:
            random.shuffle(self.sources)
        filter = []
        for d in debrid.debrid_resolvers:
            valid_hoster = set([i['source'] for i in self.sources])
            valid_hoster = [i for i in valid_hoster if d.valid_url('', i)]
            if sortTorrentTop == 'true':
                filter += [dict(i.items() + [('debrid', d.name)]) for i in self.sources if 'magnet:' in str(i['url'])]
                filter += [dict(i.items() + [('debrid', d.name)]) for i in self.sources if i['source'] in valid_hoster and 'magnet:' not in str(i['url'])]
            else:
                filter += [dict(i.items() + [('debrid', d.name)]) for i in self.sources if i['source'] in valid_hoster or 'magnet:' in str(i['url'])]
        if debridOnly == 'false' or debrid.status() is False:
            filter += [i for i in self.sources if not i['source'].lower() in self.hostprDict and i['debridonly'] is False]
        self.sources = filter
        if not captcha == 'true':
            filter = [i for i in self.sources if i['source'].lower() in self.hostcapDict and 'debrid' not in i]
            self.sources = [i for i in self.sources if i not in filter]
        filter = [i for i in self.sources if i['source'].lower() in self.hostblockDict and 'debrid' not in i]
        self.sources = [i for i in self.sources if i not in filter]
        if not torrentEnabled == 'true':
            self.sources = [i for i in self.sources if i['source'].lower() != 'torrent']
        self.sources = self.sources[:2500]

    def sourcesLabels(self):
        def _processLabels(item):
            if extraInfo == 'true':
                t = source_utils.getFileType(item['url'])
            else:
                t = None
            u = item['url']
            p = item['provider']
            q = item['quality']
            s = item['source']
            s = s.rsplit('.', 1)[0]
            try:
                f = (' | '.join(['[I]%s [/I]' % info.strip() for info in item['info'].split('|')]))
            except Exception:
                f = ''
            try:
                d = item['debrid']
            except Exception:
                d = item['debrid'] = ''
            if d.lower() == 'real-debrid':
                d = 'RD'
            elif d.lower() == 'premiumize.me':
                d = 'PM'
            if q in ['4K', '1080p', '720p']:
                label = '[B]EXTERNAL[/B] | [I][B]%s[/B][/I]  | ' % q
            else:
                label = '[B]EXTERNAL[/B] | [I]SD[/I]  | '
            if not d == '':
                label += '[B]%s | %s[/B] | ' % (d, p)
            else:
                label += '[B]%s[/B] | ' % (p)
            if t:
                label += '%s | %s | [I]%s[/I]' % (s, f, t)
            else:
                label += '%s | %s' % (s, f)
            label = label.replace('| 0 |', '|').replace(' | [I]0 [/I]', '')
            label = re.sub('\[I\]\s+\[/I\]', ' ', label)
            label = re.sub('\|\s+\|', '|', label)
            label = re.sub('\|(?:\s+|)$', '', label)
            if d:
                if 'torrent' in s.lower():
                    if not torrentHighlight == 'nocolor':
                        item['label'] = ('[COLOR %s]' % (torrentHighlight)) + label.upper() + '[/COLOR]'
                    else:
                        item['label'] = label.upper()
                else:
                    if not premiumHighlight == 'nocolor':
                        item['label'] = ('[COLOR %s]' % (premiumHighlight)) + label.upper() + '[/COLOR]'
                    else:
                        item['label'] = label.upper()
            else:
                item['label'] = label.upper()
        threads = []
        extraInfo = __furkit__.getSetting('results.show_filenames')
        premiumHighlight = __furkit__.getSetting('prem.identify')
        if premiumHighlight == '': premiumHighlight = 'blue'
        torrentHighlight = __furkit__.getSetting('torrent.identify')
        if torrentHighlight == '': torrentHighlight = 'magenta'
        for i in self.sources: threads.append(workers.Thread(_processLabels, i))
        [i.start() for i in threads]
        [i.join() for i in threads]
        self.sources = [i for i in self.sources if 'label' in i]
        return self.sources

    def sourcesUpdate(self, source, sources):
        for i in sources:
            i.update({'provider': source, 'external': True, 'size': 0, 'scrape_provider': self.scrape_provider, 'url': i['url']})
            if 'checkquality' in i and i['checkquality'] is True:
                if not i['source'].lower() in self.hosthqDict and i['quality'] not in ['SD', 'SCR', 'CAM']:
                    i.update({'quality': 'SD'})
            q = i['quality']
            if q == 'HD':
                i.update({'quality': '720p'})
            if q == '1440p':
                i.update({'quality': '1080p'})
        return sources

    def sourcesRemoveDuplicates(self, sources):
        uniqueURLs = set()
        for source in sources:
            try:
                if source['url'] not in uniqueURLs:
                    uniqueURLs.add(source['url'])
                    yield source
                else:
                    pass
            except:
                yield source

    def getConstants(self):
        from tikiscrapers import sources
        self.providerDatabase = os.path.join(xbmc.translatePath(__external__.getAddonInfo('profile')), "providers.db")
        self.sourceDict = sources()
        self.moduleProvider = __external__.getSetting('module.provider')
        try:
            self.hostDict = resolveurl.relevant_resolvers(order_matters=True)
            self.hostDict = [i.domains for i in self.hostDict if '*' not in i.domains]
            self.hostDict = [i.lower() for i in reduce(lambda x, y: x+y, self.hostDict)]
            self.hostDict = [x for y, x in enumerate(self.hostDict) if x not in self.hostDict[:y]]
        except Exception:
            self.hostDict = []
        self.hostprDict = ['1fichier.com', 'oboom.com', 'rapidgator.net', 'rg.to', 'uploaded.net',
                           'uploaded.to', 'ul.to', 'filefactory.com', 'nitroflare.com', 'turbobit.net', 'uploadrocket.net']
        self.hostcapDict = ['kingfiles.net', 'openload.io', 'openload.co', 'oload.tv', 'thevideo.me',
                            'vidup.me', 'streamin.to', 'torba.se', 'openload']
        self.hosthqDict = ['gvideo', 'google.com', 'openload.io', 'openload.co', 'oload.tv', 'thevideo.me', 'rapidvideo.com',
                           'raptu.com', 'filez.tv', 'uptobox.com', 'uptostream.com', 'xvidstage.com', 'streamango.com']
        self.hostblockDict = []
        self.furk_enabled = __furkit__.getSetting('provider.furk')
        self.easynews_enabled = __furkit__.getSetting('provider.easynews')
        self.local_enabled = __furkit__.getSetting('provider.local')
        self.progressHeading = int(__furkit__.getSetting('progress.heading'))
        self.furk_sources, self.furk_sources_4K, self.furk_sources_1080p, self.furk_sources_720p, self.furk_sources_SD = (0 for _ in range(5))
        self.easynews_sources, self.easynews_sources_4K, self.easynews_sources_1080p, self.easynews_sources_720p, self.easynews_sources_SD = (0 for _ in range(5))
        self.local_sources, self.local_sources_4K, self.local_sources_1080p, self.local_sources_720p, self.local_sources_SD = (0 for _ in range(5))
        self.internalSourcesTotal, self.internalSources4K, self.internalSources1080p, self.internalSources720p, self.internalSourcesSD = (0 for _ in range(5))

    def internalResults(self):
        if self.local_enabled == 'true' and not self.local_sources:
            try: local_sources = json.loads(control.window.getProperty('local_source_results'))
            except: local_sources = []
            if local_sources:
                self.local_sources = len(local_sources)
                self.local_sources_4K = len([i for i in local_sources if i['quality'] == '4K'])
                self.local_sources_1080p = len([i for i in local_sources if i['quality'] == '1080p'])
                self.local_sources_720p = len([i for i in local_sources if i['quality'] == '720p'])
                self.local_sources_SD = len([i for i in local_sources if i['quality'] in ['SD', 'SCR', 'CAM', 'TELE']])
        if self.furk_enabled == 'true' and not self.furk_sources:
            try: furk_sources = json.loads(control.window.getProperty('furk_source_results'))
            except: furk_sources = []
            if furk_sources:
                self.furk_sources = len(furk_sources)
                self.furk_sources_4K = len([i for i in furk_sources if i['quality'] == '4K'])
                self.furk_sources_1080p = len([i for i in furk_sources if i['quality'] == '1080p'])
                self.furk_sources_720p = len([i for i in furk_sources if i['quality'] == '720p'])
                self.furk_sources_SD = len([i for i in furk_sources if i['quality'] in ['SD', 'SCR', 'CAM', 'TELE']])
        if self.easynews_enabled == 'true' and not self.easynews_sources:
            try: easynews_sources = json.loads(control.window.getProperty('easynews_source_results'))
            except: easynews_sources = []
            if easynews_sources:
                self.easynews_sources = len(easynews_sources)
                self.easynews_sources_4K = len([i for i in easynews_sources if i['quality'] == '4K'])
                self.easynews_sources_1080p = len([i for i in easynews_sources if i['quality'] == '1080p'])
                self.easynews_sources_720p = len([i for i in easynews_sources if i['quality'] == '720p'])
                self.easynews_sources_SD = len([i for i in easynews_sources if i['quality'] in ['SD', 'SCR', 'CAM', 'TELE']])
        self.internalSources4K = self.local_sources_4K + self.furk_sources_4K + self.easynews_sources_4K
        self.internalSources1080p = self.local_sources_1080p + self.furk_sources_1080p + self.easynews_sources_1080p
        self.internalSources720p = self.local_sources_720p + self.furk_sources_720p + self.easynews_sources_720p
        self.internalSourcesSD = self.local_sources_SD + self.furk_sources_SD + self.easynews_sources_SD
        self.internalSourcesTotal = self.internalSources4K + self.internalSources1080p + self.internalSources720p + self.internalSourcesSD

    def exportSettings(self):
        try:
            __external__.setSetting('torrent.min.seeders', __furkit__.getSetting('torrent.min.seeders'))
            __external__.setSetting('torrent.enabled', __furkit__.getSetting('torrent.enabled'))
        except: pass
