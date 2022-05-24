# -*- coding: UTF-8 -*-

import pkgutil
import os.path

import xbmc, xbmcaddon, xbmcvfs, xbmcgui

__addon__ = xbmcaddon.Addon(id='script.module.tikiscrapers')

def sources():
    sourceDict = []
    try:
        initializeCheck()
        provider = __addon__.getSetting('module.provider')
        sourceFolder = getScraperFolder(provider)
        sourceFolderLocation = os.path.join(os.path.dirname(__file__), sourceFolder)
        sourceSubFolders = [x[1] for x in os.walk(sourceFolderLocation)][0]
        for i in sourceSubFolders:
            for loader, module_name, is_pkg in pkgutil.walk_packages([os.path.join(sourceFolderLocation, i)]):
                if is_pkg:
                    continue
                try:
                    module = loader.find_module(module_name).load_module(module_name)
                    sourceDict.append((module_name, module.source()))
                except: pass
        return enabledScrapers(sourceDict)
    except:
        return sourceDict

def initializeCheck():
    checkDatabase()
    checkImports()
    enableNewScrapers()

def scrapersStatus(folder='all'):
    providers = scraperNames(folder)
    enabled = [i for i in providers if __addon__.getSetting('provider.' + i) == 'true']
    disabled = [i for i in providers if i not in enabled]
    return enabled, disabled

def enabledScrapers(sourceDict):
    enabledHosts = [i[0] for i in sourceDict if __addon__.getSetting('provider.' + i[0]) == 'true']
    returnedHosts = [i for i in sourceDict if i[0] in enabledHosts]
    return returnedHosts

def scraperNames(folder):
    providerList = []
    provider = __addon__.getSetting('module.provider')
    sourceFolder = getScraperFolder(provider)
    sourceFolderLocation = os.path.join(os.path.dirname(__file__), sourceFolder)
    sourceSubFolders = [x[1] for x in os.walk(sourceFolderLocation)][0]
    if not folder == 'all':
        sourceSubFolders = [i for i in sourceSubFolders if i == folder]
    for i in sourceSubFolders:
        for loader, module_name, is_pkg in pkgutil.walk_packages([os.path.join(sourceFolderLocation, i)]):
            if is_pkg:
                continue
            providerList.append(module_name)
    return providerList

def getScraperFolder(scraper_source):
    sourceSubFolders = [x[1] for x in os.walk(os.path.dirname(__file__))][0]
    try: sourceFolder = [i for i in sourceSubFolders if scraper_source.lower() in i.lower()][0]
    except: setDefault()
    return sourceFolder

def providerSources():
    sourceSubFolders = [x[1] for x in os.walk(os.path.dirname(__file__))][0]
    return getProviderName(sourceSubFolders)

def getProviderName(scraper_folders):
    nameList = []
    for s in scraper_folders:
        try: nameList.append(s.split('_')[1].lower().title())
        except: pass
    return nameList

def checkDatabase():
    dataPath = xbmc.translatePath(__addon__.getAddonInfo('profile'))
    providerDB = os.path.join(dataPath, "providers.db")
    if not xbmcvfs.exists(dataPath): xbmcvfs.mkdirs(dataPath)
    if xbmcvfs.exists(providerDB): return
    try: from sqlite3 import dbapi2 as database
    except: from pysqlite2 import dbapi2 as database
    dbcon = database.connect(providerDB)
    dbcon.execute("""CREATE TABLE IF NOT EXISTS rel_url
                      (source text, imdb_id text, season text, episode text,
                      rel_url text, unique (source, imdb_id, season, episode)) 
                   """)
    dbcon.execute("""CREATE TABLE IF NOT EXISTS rel_src
                      (source text, imdb_id text, season text, episode text,
                      hosts text, added text, unique (source, imdb_id, season, episode)) 
                   """)
    dbcon.close()

def checkImports():
    backupPath = xbmc.translatePath(os.path.join(__addon__.getAddonInfo('profile'), 'scraper_backups' + '/'))
    if not xbmcvfs.exists(backupPath): return
    sourceList = [i.lower() for i in sorted(providerSources()) if not i.lower() == 'tikiscrapers']
    backupDirs = xbmcvfs.listdir(backupPath)[0]
    if len(sourceList) == len(backupDirs): return
    try:
        from tikiscrapers.modules.external_import import ExternalImporter
        backupModules = [i.split('_')[1].lower() for i in backupDirs]
        backupModules = [i for i in backupModules if not i in sourceList]
        for i in backupModules:
            module = 'sources_%s' % i
            path = xbmc.translatePath(os.path.join(__addon__.getAddonInfo('profile'), 'scraper_backups', module + '/'))
            ExternalImporter().importBackup(path, module)
        xbmcgui.Dialog().notification('Tiki Scrapers Updated', 'External Modules Reloaded', __addon__.getAddonInfo('icon'), 5000, False)
        xbmc.sleep(1000)
    except: setDefault()

def enableNewScrapers():
    providers = scraperNames('all')
    newProviders = [i for i in providers if __addon__.getSetting('provider.' + i) == '']
    if len(newProviders) == 0: return
    for i in newProviders: __addon__.setSetting('provider.' + i, 'true')
    xbmcgui.Dialog().notification('Tiki Scrapers', 'New Scrapers Activated', __addon__.getAddonInfo('icon'), 5000, False)
    xbmc.sleep(1000)
    return

def setDefault():
    __addon__.setSetting('module.provider', 'Tikiscrapers')
    sourceFolder = 'sources_tikiscrapers'

def deleteProviderCache():
    try:
        providerDB = os.path.join(xbmc.translatePath(__addon__.getAddonInfo('profile')), "providers.db")
        if not xbmcvfs.exists(providerDB): return
        if not xbmcgui.Dialog().yesno('Are you sure?','Furk It Scrapers will Clear all Provider Results.'):
            return False
        try: from sqlite3 import dbapi2 as database
        except ImportError: from pysqlite2 import dbapi2 as database
        dbcon = database.connect(providerDB)
        dbcur = dbcon.cursor()
        for i in ('rel_url', 'rel_src'):
            dbcur.execute("DELETE FROM %s" % i)
        dbcur.execute("VACUUM")
        dbcon.commit()
        dbcon.close()
        return True
    except:
        return False


