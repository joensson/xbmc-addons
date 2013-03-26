# -*- coding: utf-8 -*-

import os
import sys
import re
import urllib
import urllib2
import htmllib
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import base64
import time
import base64
import string
import tempfile
import subprocess as sp
import webbrowser
import urlparse
import zipfile
import xml.etree.ElementTree as ET
import mechanize
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup, UnicodeDammit
from xml.dom.minidom import parseString
global thisPlugin
global XBMCPROFILE
global RESOURCE_FOLDER
global ROOT_FOLDER
#global tvDb

try:
    from sqlite3 import dbapi2 as sqlite
    xbmc.log("Loading sqlite3 as DB engine")
except:
    from pysqlite2 import dbapi2 as sqlite
    xbmc.log("Loading pysqlite2 as DB engine")

thisPlugin = int(sys.argv[1])
__settings__ = xbmcaddon.Addon(id='plugin.video.hbonordic')
__language__ = __settings__.getLocalizedString
ROOT_FOLDER = __settings__.getAddonInfo('path')
XBMCPROFILE = xbmc.translatePath('special://profile')
RESOURCE_FOLDER = os.path.join(unicode(ROOT_FOLDER,'utf-8'), 'resources')
RESOURCE_FOLDER2 = os.path.join(ROOT_FOLDER, 'resources')
LIB_FOLDER = os.path.join(RESOURCE_FOLDER2, 'lib')
HBOPLAYER_PATH = os.path.join(LIB_FOLDER, 'HboLauncher.exe')
AUTOHOTKEY_PATH = os.path.join(LIB_FOLDER, 'MceRemoteHandler.exe')
SETTINGS_PLATFORM = __settings__.getSetting("PLATFORM")
SETTINGS_USERNAME = __settings__.getSetting("Username")
SETTINGS_PASSWORD = __settings__.getSetting("Password")
SETTINGS_USETVDB =(__settings__.getSetting("UseTvdb").lower() == "true")
SETTINGS_COUNTRY = __settings__.getSetting("Country")
PLATFORM_WIN=1
PLATFORM_LINUX=2
PLAFORM_MAC=3

class Link(object):
    def __init__(self, type=None, name=None, cmd=None, url=None):
        self.type = type
        self.name = name
        self.cmd = cmd
        self.url = url
        
class Season(object):
    def __init__(self, season=None, url=None):
        self.season = season
        self.url = url

class TvSeries(object):
    def __init__(self, season=None, episode=None, episodeTitle=None,filename=None, name=None, overview=None,firstaired=None):
        self.season = season
        self.episode = episode
        self.episodeTitle = episodeTitle
        self.name = name
        self.filename=filename
        self.overview = overview
        self.firstaired=firstaired

class EpisodeInfo(object):
    def __init__(self, imageUrl=None, synopsis=None):
        self.imageUrl = imageUrl
        self.synopsis = synopsis

class Movie(object):
    def __init__(self, title=None, url=None,imageUrl=None):
        self.title = title
        self.url = url
        self.imageUrl=imageUrl
        
def RemoveFile(path):
    try:
        if(os.path.exists(path)):
            os.remove(path)
    except OSError:
        pass

def EscapeXml(value):
    string =str(value)
    
    # "   &quot;
# '   &apos;
# <   &lt;
# >   &gt;
# &   &amp;
    #string = string.replace('\"','&quot;')
    string = string.replace('&','&amp;')
    #string = string.replace('"','&quot;')
    string = string.replace('\'','&apos;')
    # string = string.replace('<','&lt;')
    # string = string.replace('>','&gt;')
    return string

def DownloadFile(url,path):
    result=urllib2.urlopen(url)
    localFile = open(path, 'wb')
    localFile.write(result.read())
    localFile.close()
    # u = urllib2.urlopen(url)
    # localFile = open(path, 'w')
    # localFile.write(u.read())
    # localFile.close()

def GetSeasonBannerURL(season):
    xbmc.log("GetSeasonBannerURL")
    zip_dir = xbmc.translatePath('special://profile/addon_data/plugin.video.hbonordic/tmp/')
    data_path = os.path.join(zip_dir, "banners.xml")
    xbmc.log("Data_path: " + data_path)
    
    xml = open(unicode(data_path,'utf-8'), 'r').read()
    
    xbmc.log("Parse tree")
    tree = ET.parse(unicode(data_path,'utf-8'))
    xbmc.log("Tree getroot")
    root = tree.getroot()
    xbmc.log("Find all banners")
    banners = root.findall("Banner")
    
    for banner in banners:
        if(banner.find("BannerType").text =="season"):
            if(banner.find("Season").text ==str(season)):
                url = urlparse.urljoin("http://thetvdb.com/banners/",str(banner.find("BannerPath").text).strip())
                xbmc.log("URL: " + url)
                return url
            
    xbmc.log("No banner url was found!")
    return ""
    
def GetFanArtBannerURL():
    xbmc.log("GetFanArtBannerURL")
    zip_dir = xbmc.translatePath('special://profile/addon_data/plugin.video.hbonordic/tmp/')
    data_path = os.path.join(zip_dir, "banners.xml")
    xbmc.log("Data_path: " + data_path)
    
    xml = open(unicode(data_path,'utf-8'), 'r').read()
    
    xbmc.log("Parse tree")
    tree = ET.parse(unicode(data_path,'utf-8'))
    xbmc.log("Tree getroot")
    root = tree.getroot()
    xbmc.log("Find all banners")
    banners = root.findall("Banner")
    
    for banner in banners:
        if(banner.find("BannerType").text =="fanart"):
            url = urlparse.urljoin("http://thetvdb.com/banners/",str(banner.find("BannerPath").text).strip())
            xbmc.log("URL: " + url)
            return url
            
    xbmc.log("No banner url was found!")
    return ""
    
def GetSeries(seriesID):
    url = "http://thetvdb.com/api/5736416B121F48D5/series/"+seriesID+"/all/sv.zip"
    #dir = os.path.dirname(__file__)
    zip_dir = xbmc.translatePath('special://profile/addon_data/plugin.video.hbonordic/tmp')
    zip_path = os.path.join( zip_dir, 'all.zip')
    #zip_url = "file:" + urllib.pathname2url(zip_path)
    
    xbmc.log("Zip_dir: " + zip_dir)
    xbmc.log("Zip_path: " + zip_path)
    #xbmc.log("Zip_url: " + zip_url)
    
    if not os.path.exists(unicode(zip_dir,'utf-8')):
        xbmc.log("Path does not exist, create folder")
        os.makedirs(unicode(zip_dir,'utf-8'))

    RemoveFile(unicode(zip_path,'utf-8'))
    
    xbmc.log("Remove old files before extracting new ones...")
    for the_file in os.listdir(unicode(zip_dir,'utf-8')):
        file_path = os.path.join(unicode(zip_dir,'utf-8'), the_file)
        #xbmc.log("Remove file: " + file_path)
        RemoveFile(file_path)
    
    xbmc.log("Download data from TheTvDb")
    #result = urllib.urlretrieve(url, "all.zip")
    DownloadFile(url,unicode(zip_path,'utf-8'))
    #xbmc.log("Result: " + result)
    
    #extract_path = os.path.join(dir, "resources" + os.sep + "tvdb")
    data_path = os.path.join(zip_dir, "sv.xml")
    
    #xbmc.log("Open zip-file: " + zip_path)
    zip = zipfile.ZipFile(unicode(zip_path,'utf-8'))
    xbmc.log("Extract zip-file")
    zip.extractall(unicode(zip_dir,'utf-8'))
    
    xbmc.log("Open xml-file")
    xml = open(unicode(data_path,'utf-8'), 'r').read()
    
    xbmc.log("Parse tree")
    tree = ET.parse(unicode(data_path,'utf-8'))
    xbmc.log("Tree getroot")
    root = tree.getroot()
    xbmc.log("Find all episodes")
    episodes = root.findall("Episode")
    
    series=[]
    xbmc.log("Find all series")
    seriesObj = root.findall("Series")
    xbmc.log("Get Series name")
    seriesName = seriesObj[0].find("SeriesName").text

    xbmc.log("Add episodes to collection")
    for episode in episodes:
        series.append(TvSeries(episode.find("SeasonNumber").text,episode.find("EpisodeNumber").text,episode.find("EpisodeName").text,episode.find("filename").text,seriesName,episode.find("Overview").text,episode.find("FirstAired").text))
    
    xbmc.log("All episodes added to collection")
    return series

def GetEpisodeName(seasonNo,episodeNo,episodes):
    for episode in episodes:
        if(str(episode.season)==str(seasonNo) and str(episode.episode)==str(episodeNo)):
            if (episode.episodeTitle==None):
                return ""
            else:
                return str(episode.episodeTitle)

def GetEpisodeFirstAired(seasonNo,episodeNo,episodes):
    for episode in episodes:
        if(str(episode.season)==str(seasonNo) and str(episode.episode)==str(episodeNo)):
            if (episode.firstaired==None):
                return ""
            else:
                return str(episode.firstaired)
                
def GetEpisodeOverview(seasonNo,episodeNo,episodes):
    for episode in episodes:
        if(str(episode.season)==str(seasonNo) and str(episode.episode)==str(episodeNo)):
            if (episode.overview==None):
                return ""
            else:
                return unicode(episode.overview).encode("utf-8")
                
def GetEpisodeThumbnail(seasonNo,episodeNo,episodes):
    for episode in episodes:
        if(str(episode.season)==str(seasonNo) and str(episode.episode)==str(episodeNo)):
            if (episode.episodeTitle==None):
                return ""
            else:
                return str(episode.filename)

def GetSeriesID(seriesName):
    seriesName = seriesName.strip()
    url ="http://thetvdb.com/api/GetSeries.php?seriesname="+urllib.quote_plus(seriesName)+"&language=sv"
    xbmc.log("TvDb GetSeriesID URL: " +url)
    result=urllib2.urlopen(url)
    xml = result.read()
    xml = xml.replace("\n","")
    xml = EscapeXml(xml)
    
    xbmc.log("TheTvDb GetSeriesID XML: " + xml)
    root = ET.fromstring(xml)
    #root = tree.getroot()
    xbmc.log("Find Series in XML")
    series = root.findall("Series")
    
    xbmc.log("Check if series is None")
    if(series==None):
        xbmc.log("Returning None")
        return None
    
    xbmc.log("Check if series is zero")
    if(len(series)<1):
        xbmc.log("Returning None")
        return None
    
    xbmc.log("The length of series is " + str(len(series)))
    
    xbmc.log("Go through each series")
    for serie in series:
        xbmc.log("SeriesName from xml: " + serie.find('SeriesName').text.lower().encode("utf-8"))
        xbmc.log("SeriesName: " + seriesName.lower())
        seriesName_xml = serie.find('SeriesName').text.encode("utf-8")
        seriesName_xml = FixHtmlString(seriesName_xml)
        seriesName_xml = seriesName_xml.lower()
        seriesName_xml = seriesName_xml.strip()
        xbmc.log("SeriesName XML: " + seriesName_xml)
        seriesId = str(serie.find("seriesid").text)

        if(seriesId == "76399"):
            continue
        elif(seriesId =="71173"):
            continue
        else:
            if(seriesName_xml=="the newsroom (2012)"):
                return seriesId
            if(seriesName_xml=="the office (us)"):
                return seriesId
            if(seriesName_xml=="battlestar galactica (2003)"):
                return seriesId
            if(seriesName_xml=="spartacus: blood and sand"):
                return seriesId
            if(seriesName_xml==seriesName.lower()):
                return seriesId

def CreateDatabase():
    try:
        checkFile = os.path.join(ROOT_FOLDER, 'favorites.db')
        xbmc.log('Path to database: ' + checkFile)
        havefile = os.path.isfile(checkFile)
        xbmc.log("Havefile: " + str(havefile))
        if(not havefile):
            con = sqlite.connect(checkFile)
            with con:
                cur = con.cursor()    
                cur.execute("CREATE TABLE Favorites(Id INTEGER PRIMARY KEY, Title TEXT, Type TEXT, Url TEXT, Poster TEXT, Year INTEGER, Director TEXT, Desc TEXT);")
                cur.execute("CREATE TABLE Version(Version INTEGER);")
                cur.execute("INSERT INTO Version (Version) VALUES(1)")
    except:
        xbmc.log("Could not create database.")
        return None

def UpgradeDatabase():
    xbmc.log("Check for database upgrade")
    version = DatabaseVersion()
    checkFile = DatabasePath()
    havefile = os.path.isfile(checkFile)
    if(havefile):
        con = sqlite.connect(checkFile)
        with con:
            cur = con.cursor()
            if version =="1":
                cur.execute("CREATE TABLE WatchedEpisodes(Id INTEGER PRIMARY KEY, Title TEXT, Season INTEGER, Episode INTEGER);")
                cur.execute("UPDATE Version SET Version = 2")
                xbmc.log("Database was upgraded to version: 2")

def DatabasePath():
    return unicode(os.path.join(ROOT_FOLDER, 'favorites.db'),'utf-8')

# Retrieves the current database version
def DatabaseVersion():
    con = sqlite.connect(DatabasePath())
    with con:
        cur = con.cursor()
        cur.execute("SELECT Version FROM Version")
        rows = cur.fetchall()
        return str(rows[0][0])

# Adds an episode as watched to the database.
def AddWatchedEpisode(title, season, episode):
    path = DatabasePath()
    con = sqlite.connect(path)
    with con:
        cur = con.cursor()
        cur.execute('''INSERT INTO WatchedEpisodes (Title,Season,Episode) VALUES(?,?,?)''', (title,season,episode))

def RemoveWatchedEpisode(title,season,episode):
    path = DatabasePath() #os.path.join(str(ROOT_FOLDER), 'favorites.db')
    con = sqlite.connect(path)
    with con:
        cur = con.cursor()
        cur.execute('''DELETE FROM WatchedEpisodes WHERE Title=? AND Season=? AND Episode=?''',(title,season,episode))
        
def AddFavorite(title,type,url,poster,year,director,desc):
    path = DatabasePath()#os.path.join(str(ROOT_FOLDER), 'favorites.db')
    con = sqlite.connect(path)
    with con:
        cur = con.cursor()
        cur.execute('''INSERT INTO Favorites (Title,Type,Url,Poster,Year,Director,Desc) VALUES(?,?,?,?,?,?,?)''', (title,type,url,poster,year,director,desc))

def RemoveFavorite(id):
    path = DatabasePath() #os.path.join(str(ROOT_FOLDER), 'favorites.db')
    con = sqlite.connect(path)
    with con:
        cur = con.cursor()
        cur.execute("DELETE FROM Favorites WHERE Id="+str(id))

def IsWatchedEpisode(title,season,episode):
    path = DatabasePath()
    con = sqlite.connect(path)
    value=False
    
    with con:
        cur = con.cursor()
        cur.execute('''SELECT * FROM WatchedEpisodes WHERE Title=? AND Season=? AND Episode=?''',(title,season,episode))

        row = cur.fetchone()
        if row is None:
            value=False
        else:
            value=True
    return value

def LoadTvFavorites():
    path = DatabasePath() #os.path.join(str(ROOT_FOLDER), 'favorites.db')
    con = sqlite.connect(path)
    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM Favorites WHERE Type='tv' ORDER BY Title Asc")

        rows = cur.fetchall()

        for row in rows:
            id=str(row[0])
            title = unicode(row[1]).encode('utf-8')
            poster = str(row[4])
            url = str(row[3])
            listItem = xbmcgui.ListItem(title)
            listItem.setThumbnailImage(poster)
            infoLabels = { "Title": title,"tvshowtitle": title }
            listItem.setInfo(type="Video", infoLabels=infoLabels)
            item_url=str(sys.argv[0]) + '?' + "url=" + urllib.quote_plus(url) + "&mode=series&title=" + urllib.quote_plus(title)
            
            cm_url = str(sys.argv[0]) + '?' + "id=" + urllib.quote_plus(id) + "&mode=remove_tv_favorite" + "&title="+urllib.quote_plus(title)
            listItem.addContextMenuItems([(unicode(__language__(4020)).encode('utf-8'), "XBMC.RunPlugin(%s)" % (cm_url),)],replaceItems=True)

            xbmcplugin.addDirectoryItem(thisPlugin,item_url,listItem,isFolder=True)
    xbmc.executebuiltin("Container.SetViewMode(500)")
def ReloadSettings():
    __settings__ = xbmcaddon.Addon(id='plugin.video.hbonordic')
    __language__ = __settings__.getLocalizedString
    SETTINGS_COUNTRY = __settings__.getSetting("Country")
        
def GetLinks(url_Type):
    linksDir = os.path.join(str(RESOURCE_FOLDER), 'links')
    filepath = os.path.join(str(linksDir), GetLinksFilename())
    xbmc.log('GetLinks filepath: ' + filepath)
    file = open(filepath,'r')
    data = file.read()
    file.close()
    
    dom = parseString(data)
    test=dom.getElementsByTagName('Links')
    
    links=[]
    for item in test:
        if item.childNodes[1].childNodes[0].nodeValue==url_Type:
            url = FixHtmlString(str(item.childNodes[7].childNodes[0].nodeValue))
            #name = FixHtmlString(unicode(item.childNodes[3].childNodes[0].nodeValue).encode('utf-8'))
            links.append(Link(item.childNodes[1].childNodes[0].nodeValue,item.childNodes[3].childNodes[0].nodeValue,item.childNodes[5].childNodes[0].nodeValue,url))
    return links

def DoesSeriesExistAtTvDb(series_name):
    try:
        t = tvdb_api.Tvdb(language="sv")
        series =  t[unicode(series_name)]
        xbmc.log('DoesSeriesExistAtTvDb: True')
        return True
    except Exception as ex:
        xbmc.log('DoesSeriesExistAtTvDb: False ' + str(ex) + ' series_name = ' + series_name)
        return False

def CreatePlayerCoreFactory(path):
    xml =""
    xml +="<playercorefactory>"
    xml +="<players>"
    xml +="<player name=\"IE\" type=\"ExternalPlayer\">"
    xml +="<filename>"+str(HBOPLAYER_PATH)+"</filename>"
    xml +="<args>-k \"{1}\"</args>"
    xml +="<hidexbmc>false</hidexbmc>"
    xml +="<hideconsole>false</hideconsole>"
    xml +="<warpcursor>none</warpcursor>"
    xml +="</player>"
    xml +="</players>"
    xml +="<rules action=\"prepend\">"
    xml +="<rule name=\"html\" filetypes=\"html\" player=\"IE\" />"
    xml +="</rules>"
    xml +="</playercorefactory>"
    
    f = open(path,'w+')
    f.write(xml)
    f.close()
    
def checkplayercore():
    xbmc.log('CheckPlayerCore')
    checkFile = os.path.join(str(XBMCPROFILE), 'playercorefactory.xml')
    havefile = os.path.isfile(checkFile)
    xbmc.log('Path to playercorefactory: ' + checkFile)
    if(not havefile):
        #copy file data from addon folder
        xbmc.log('Platform is: ' + os.name)
        if(os.name=='nt'):
            xbmc.log('Create playercorefactory.xml for Windows')
            CreatePlayerCoreFactory(checkFile)
            xbmcgui.Dialog().ok( "HBO Nordic add-on", __language__(4011) ) #You need to restart XBMC before you can use the HBO Nordic add-on.
        else:
            xbmc.log('The platform is not windows, create playercorefactory for other platform')
            fileWithData = os.path.join(str(RESOURCE_FOLDER), 'playercorefactory.xml')
            if not os.path.exists('C:\Program Files (x86)'):
                fileWithData = os.path.join(str(RESOURCE_FOLDER), 'playercorefactory32.xml')
            if not os.path.exists('C:\Program Files'):
                fileWithData = os.path.join(str(RESOURCE_FOLDER), 'playercorefactoryOSX.xml')
                xbmc.log('Create playercorefactoryOSX.xml for Mac OSX')
            data = open(str(fileWithData),'r').read()
            f = open(checkFile,'w+')
            f.write(data)
            f.close()
    
def checkadvsettings():
    checkFile = os.path.join(str(XBMCPROFILE), 'advancedsettings.xml')
    havefile = os.path.isfile(checkFile)
    if(not havefile):
        #copy file from addon folder
        fileWithData = os.path.join(str(RESOURCE_FOLDER), 'advancedsettings.xml')
        data = open(str(fileWithData),'r').read()
        f = open(checkFile,'w+')
        f.write(data)
        f.close()
        
def parameters_string_to_dict(param_string):
    params = {}
    
    if param_string:
        pairs = param_string[1:].split("&")

        for pair in pairs:

            split = pair.split('=')

            if (len(split)) == 2:
                params[split[0]] = split[1]
    
    return params

def GetLinksFilename():
    if SETTINGS_COUNTRY=="0":
        return "viaplay_se.xml"
    elif SETTINGS_COUNTRY=="1":
        return "viaplay_dk.xml"
    elif SETTINGS_COUNTRY=="2":
        return "viaplay_no.xml"
    elif SETTINGS_COUNTRY=="3":
        return "viaplay_fi.xml"
        
    return "viaplay_se.xml"
def GetDomain():
    if SETTINGS_COUNTRY=="0":
        return "http://viaplay.se"
    elif SETTINGS_COUNTRY=="1":
        return "http://viaplay.dk"
    elif SETTINGS_COUNTRY=="2":
        return "http://viaplay.no"
    elif SETTINGS_COUNTRY=="3":
        return "http://viaplay.fi"
        
    return "http://viaplay.se"
def LoadTvByAlphabet(url):
    #url = "http://viaplay.se/tv/samtliga/17235/alphabetical"
    page=urllib2.urlopen(url)
    soup = BeautifulSoup(page.read())
    
    alphabet=soup.findAll('ul', attrs={'class' : 'atoz-list'})
    for letter in alphabet:
        for series in letter.findAll('li'):
            if series.contents[1].name=='h4':
                tv_title= FixHtmlString(unicode(series.contents[1].contents[0].string).encode('utf-8'))
                tv_url = urlparse.urljoin(GetDomain() , str(series.contents[1].contents[0].attrs[0][1]))
                #tv_cover_url=GetSeriesCover(tv_url)
                listItem = xbmcgui.ListItem(tv_title)
                #listItem.setThumbnailImage(tv_cover_url)
                infoLabels = { "Title": tv_title,"tvshowtitle": tv_title }
                listItem.setInfo(type="Video", infoLabels=infoLabels)
                item_url=str(sys.argv[0]) + '?' + "url=" + urllib.quote_plus(tv_url) + "&mode=series"
                xbmcplugin.addDirectoryItem(thisPlugin,item_url,listItem,isFolder=True)
    xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmc.executebuiltin("Container.SetViewMode(50)")
def LoadMoviesByAlphabet(url):
    #url = "http://viaplay.se/tv/samtliga/17235/alphabetical"
    page=urllib2.urlopen(url)
    soup = BeautifulSoup(page.read())
    
    alphabet=soup.findAll('ul', attrs={'class' : 'atoz-list'})
    for letter in alphabet:
        for series in letter.findAll('li'):
            if series.contents[1].name=='h4':
                movie_title= FixHtmlString(unicode(series.contents[1].contents[0].string).encode('utf-8'))
                movie_url = urlparse.urljoin(GetDomain() , str(series.contents[1].contents[0].attrs[0][1]))
                movie_genre = unicode(series.contents[3].string).encode('utf-8')
                #tv_cover_url=GetSeriesCover(tv_url)
                listItem = xbmcgui.ListItem(movie_title)
                #listItem.setThumbnailImage(tv_cover_url)
                infoLabels = { "Title": movie_title + GetHDTag('',movie_genre,'') }
                listItem.setInfo(type="Video", infoLabels=infoLabels)
                item_url=str(sys.argv[0]) + '?' + "url=" + urllib.quote_plus(movie_url) + "&mode=play"
                xbmcplugin.addDirectoryItem(thisPlugin,item_url,listItem,isFolder=False)
    xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmc.executebuiltin("Container.SetViewMode(50)")
def GetSeriesCover(url):
    page=urllib2.urlopen(url)
    soup = BeautifulSoup(page.read())

    section=soup.findAll('div', attrs={'class' : 'content'})
    return Get_PosterUrl(str(section[0].contents[1].contents[1]))
#Loads a specific view which contains only mixed episodes from different series.
def LoadEpisodesView(url):
    try:
        page=urllib2.urlopen(url)
        soup = BeautifulSoup(page.read())

        items=soup.findAll('ul', attrs={'class' : 'media-list tv clearfix'})
        for item in items:
            for series in item.findAll('li'):
                tv_url = urlparse.urljoin(GetDomain() , str(series.contents[1].attrs[2][1]))
                xbmc.log('Episode url: ' + tv_url)
                tv_title = unicode(series.contents[7].contents[1].contents[1].attrs[1][1]).encode('utf-8')
                tv_image = Get_PosterUrl(str(series.contents[1].contents[1]))
                tv_season = int(GetSeason(series.contents[1].attrs[2][1]))
                tv_episode = int(GetEpisode(series.contents[1].attrs[2][1]))
                tv_synopsis = FixHtmlString(unicode(str(series.contents[7].contents[9].string)).encode('utf-8'))
                listItem = xbmcgui.ListItem(tv_title)
                listItem.setThumbnailImage(tv_image)
                infoLabels = { "Title": tv_title,"tvshowtitle": tv_title,"season": tv_season,"episode": tv_episode,"plotoutline": tv_synopsis,"plot": tv_synopsis}
                listItem.setInfo(type="Video", infoLabels=infoLabels)
                item_url=str(sys.argv[0]) + '?' + "url=" + urllib.quote_plus(tv_url) + "&mode=play"
                xbmcplugin.addDirectoryItem(thisPlugin,item_url,listItem)
        xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
        xbmcplugin.setContent(thisPlugin, 'episodes')
        xbmc.executebuiltin("Container.SetViewMode(504)")
    except Exception as ex:
        xbmc.log("Error in LoadEpisodesView")
        xbmc.log("LoadEpisodesView, URL: " + url)
        #xbmc.log("Error: " + ex)
def TestTvDb():
    t = tvdb_api.Tvdb()
    episode = t['My Name Is Earl'][1][3] # get season 1, episode 3 of show
    xbmc.log("Episodename: " + episode['episodename']) # Print episode name

def GetSource(url):
    page=urllib2.urlopen(url)
    return page.read()
    # mech = mechanize.Browser()
    # mech.set_handle_robots(False)
    # mech.open("http://hbonordic.se/c/portal/login")

    # mech.select_form(nr=0)
    # mech["_58_login"] = SETTINGS_USERNAME
    # mech["_58_password"] = SETTINGS_PASSWORD

    # mech.submit()

    # mech.open(url)
    # html = mech.response().get_data()
    # return html

def Get_SeasonNumber(value):
    list=value.split("&bull;")
    list2 = str(list[1]).split(" ")
    return str(list2[2])

def Get_EpisodeImageUrl(value):
    xbmc.log("Get_EpisodeImageUrl = " + value)
    list=value.split("\"")
    return str(list[3])
    
def GetEpisodeInfoHbo(html):
    #xbmc.log("GetEpisodeInfoHbo URL = " + url)
    #html = GetSource(url)
    soup = BeautifulSoup(html)
    #<div class="js-hbo_video_poster_container relative clip_container" style="height: auto;">
    items=soup.findAll('div', attrs={'class' : 'js-hbo_video_poster_container relative clip_container'})
    
    imgUrl = Get_EpisodeImageUrl(str(items[0].contents[3]))
    
    items = soup.findAll('p', attrs={'class' : 'js-clip fs14 lh1_6 margin_v_1 text_gray'})
    synopsis = str(items[0].contents[0]).strip().decode("utf-8")
    
    return EpisodeInfo(imgUrl,synopsis)

def GetEpisodesInfo(url):
    mech = mechanize.Browser()
    mech.set_handle_robots(False)
    mech.open("http://hbonordic.se/c/portal/login")

    mech.select_form(nr=0)
    mech["_58_login"] = SETTINGS_USERNAME
    mech["_58_password"] = SETTINGS_PASSWORD

    mech.submit()

    mech.open(url) #"http://hbonordic.se/web/hbo/series/all"
    html = mech.response().get_data()

    soup = BeautifulSoup(html)
    items=soup.findAll('ul', attrs={'class' : 'margin_bottom_4 show_list border_list_parent max_width margin_h_auto'})

    episodes=[]

    for item in items: 
        for episode in item.findAll("li"): 
            episode_url = "http://hbonordic.se"  + str(episode.contents[1].contents[1].attrs[1][1]).strip()
            
            mech.open(episode_url) 
            episode_html = mech.response().get_data()
            data = GetEpisodeInfoHbo(episode_html)
            episodes.append(data)

    return episodes

def GetAllMoviesHbo():
    html = GetSource("http://hbonordic.se/movies/-/-/genre/action")
    soup = BeautifulSoup(html)
    items=soup.findAll('', attrs={'class' : 'index_view wrapper units_relative u0_3_4 padding_1'})
    movies=[]
    
    for item in items:
        for movie in item.findAll('div',attrs={'class' : 'thumbnail_item unit padding_1' }): 
            movie_title = str(movie.contents[1].contents[3].contents[1].contents[0])
            movie_url_title = str(movie.contents[1].attrMap[u'href'])
            url = urlparse.urljoin("http://hbonordic.com",movie_url_title)
            movie_cover_url = Get_PosterUrl(str(movie.contents[1].contents[1].contents[3]))
            movies.append(Movie(movie_title,url,movie_cover_url))
            
    return movies

def LoadSeasonsHbo(url,title):
    html = GetSource(url)
    soup = BeautifulSoup(html)
    data=soup.findAll('li', attrs={'class' : 'left relative'})
    items = data[0].contents[3].findAll('li')
    fanArtUrl=""
    
    if(SETTINGS_USETVDB):
        id=GetSeriesID(title)
        
        if(id!=None):
            xbmc.log("ID is not None")
            xbmc.log("TheTvDb Series ID: "+id)
            GetSeries(id)
            fanArtUrl = GetFanArtBannerURL()

    for item in items: 
        season_no = Get_SeasonNumber(unicode(item.contents[0].contents[0]).encode('utf-8'))
        season_url = urlparse.urljoin("http://hbonordic.se",str(item.contents[0].attrs[1][1]).strip())
        
        if(id=="148581"):
            #If the series is Strike Back then handle the fact that season one is actually season two and season two is season three...
            xbmc.log("Handle seasons for series Strike Back!")
            season_no=str(int(season_no)+1)

        listItem = xbmcgui.ListItem("Säsong " + str(season_no))
        
        if(SETTINGS_USETVDB):
            if(id!=None):
                seasonPosterUrl = GetSeasonBannerURL(season_no)
                listItem.setThumbnailImage(seasonPosterUrl)
                listItem.setProperty("Fanart_Image", fanArtUrl)

        #infoLabels = { "Title": title,"tvshowtitle": title }
        #listItem.setInfo(type="Video", infoLabels=infoLabels)
        item_url=str(sys.argv[0]) + '?' + "url=" + urllib.quote_plus(season_url) + "&mode=series_episodes&seasonno=" + season_no +"&title="+urllib.quote_plus(title)
        
        #cm_url = str(sys.argv[0]) + '?' + "id=" + urllib.quote_plus(id) + "&mode=remove_tv_favorite" + "&title="+urllib.quote_plus(title)
        #listItem.addContextMenuItems([(unicode(__language__(4020)).encode('utf-8'), "XBMC.RunPlugin(%s)" % (cm_url),)],replaceItems=True)

        xbmcplugin.addDirectoryItem(thisPlugin,item_url,listItem,isFolder=True)
    #xbmc.executebuiltin("Container.SetViewMode(500)")
    xbmc.executebuiltin("Container.SetViewMode(50)")

def GetEpisodesHbo(url,showname,season):
    xbmc.log("GetEpisodesHbo URL: " + url)
    html = GetSource(url)
    soup = BeautifulSoup(html)
    items=soup.findAll('ul', attrs={'class' : 'margin_bottom_4 show_list border_list_parent max_width margin_h_auto'})
    xbmc.log("GetEpisodesHBO, Season: " + str(season))
    fanArtUrl=""
    
    if(SETTINGS_USETVDB):
        id=GetSeriesID(showname)
        
        if(id!=None):
            xbmc.log("ID is not None")
            xbmc.log("TheTvDb Series ID: "+id)
            episodes=GetSeries(id)
            fanArtUrl = GetFanArtBannerURL()
        else:
            xbmc.log("ID is None")
            episodes=None
    else:
        episodes=None
    
    for item in items: 
        for episode in item.findAll("li"): 
            episode_no = str(episode.contents[1].contents[1].contents[1].contents[0]).strip()
            episode_url = urlparse.urljoin("http://hbonordic.com/", str(episode.contents[1].contents[1].attrs[1][1]).strip())
            episode_title = unicode(str(episode.contents[1].contents[1].contents[3].contents[0]).strip()).encode("utf-8")
            
            firstAired=""
            #info = GetEpisodeInfoHbo(episode_url)
            episode_name = episode_no + ". " + episode_title
            listItem = xbmcgui.ListItem( episode_title)
            
            if IsWatchedEpisode(showname,season,episode_no):
                overlay=xbmcgui.ICON_OVERLAY_WATCHED
                playcount=1
            else:
                overlay=xbmcgui.ICON_OVERLAY_UNWATCHED
                playcount=0
                
            episode_Overview=""
            episode_image=""
                
            if(episodes!=None):
                episode_Overview=GetEpisodeOverview(season,episode_no,episodes)
                firstAired = GetEpisodeFirstAired(season,episode_no,episodes)
                #if(episode_Name!=None):
                    #episode_title = episode_title + " - " + episode_Name
                episode_thumbnail = GetEpisodeThumbnail(season,episode_no,episodes)
                #xbmc.log("Value from GetEpisodeThumbnail: " + episode_thumbnail)
                if(episode_thumbnail!=None):
                    if(episode_thumbnail!="None"):
                        episode_image= urlparse.urljoin("http://thetvdb.com/banners/",episode_thumbnail)
                else:
                    episode_image=""
            
            if(episode_image==""):
                episode_image = linksDir = os.path.join(RESOURCE_FOLDER, 'missing.jpg')
            
            #xbmc.log("LoadEpisodesHbo, episode_image: " + episode_image)
            
            listItem.setThumbnailImage(episode_image)
            listItem.setProperty("Fanart_Image", fanArtUrl)
            infoLabels = { "Title": episode_name,"tvshowtitle": showname,"season": int(season),"episode": int(episode_no),"plotoutline": episode_Overview,"plot": episode_Overview,"overlay":overlay,"playcount":playcount,"premiered":firstAired}
            listItem.setInfo(type="Video", infoLabels=infoLabels)
            item_url=str(sys.argv[0]) + '?' + "url=" + urllib.quote_plus(episode_url) + "&mode=play&season=" + urllib.quote_plus(str(season)) +"&episode="+ urllib.quote_plus(str(episode_no)) + "&title="+urllib.quote_plus(showname)
            
            cm_url_remove = str(sys.argv[0]) + '?' + "season=" + urllib.quote_plus(str(season)) +"&episode="+ urllib.quote_plus(str(episode_no)) +"&mode=remove_watched_episode" + "&title="+urllib.quote_plus(showname)
            cm_url_add = str(sys.argv[0]) + '?' + "season=" + urllib.quote_plus(str(season)) +"&episode="+ urllib.quote_plus(str(episode_no)) +"&mode=add_watched_episode" + "&title="+urllib.quote_plus(showname)
            listItem.addContextMenuItems([("Markera som visad", "XBMC.RunPlugin(%s)" % (cm_url_add),),("Markera som inte visad", "XBMC.RunPlugin(%s)" % (cm_url_remove),)],replaceItems=True)
            
            xbmcplugin.addDirectoryItem(thisPlugin,item_url,listItem)
            xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.setContent(thisPlugin, 'episodes')
    xbmc.executebuiltin("Container.SetViewMode(504)")

def GetSeriesHbo():
    html = GetSource("http://hbonordic.se/web/hbo/series/all")
    soup = BeautifulSoup(html)
    
    items=soup.findAll('div', attrs={'class' : 'index_view wrapper units_relative u0_3_4 padding_1'})
    
    for item in items: 
        for series in item.findAll('div', attrs={'class' : 'thumbnail_item unit padding_1'}): #<div class="thumbnail_item unit padding_1"
            tv_url = urlparse.urljoin("http://hbonordic.se/" , str(series.contents[1].attrs[1][1]))
            tv_title = unicode(series.contents[1].contents[3].contents[1].contents[0]).encode('utf-8')
            tv_image = Get_PosterUrl(str(series.contents[1].contents[1].contents[3]))
            listItem = xbmcgui.ListItem(tv_title)
            listItem.setThumbnailImage(tv_image)
            infoLabels = { "Title": tv_title,"tvshowtitle": tv_title }
            listItem.setInfo(type="Video", infoLabels=infoLabels)
            item_url=str(sys.argv[0]) + '?' + "url=" + urllib.quote_plus(tv_url) + "&mode=serieshbo&title=" + urllib.quote_plus(tv_title)
            #cm_url = str(sys.argv[0]) + '?' + "title=" + urllib.quote_plus(tv_title) + "&mode=add_tv_favorite" + "&url="+urllib.quote_plus(tv_url) +"&poster=" + urllib.quote_plus(tv_image)
            #menu_title = unicode(__language__(4019)).encode('utf-8')
            #listItem.addContextMenuItems([(menu_title, "XBMC.RunPlugin(%s)" % (cm_url),)],replaceItems=True)
            
            xbmcplugin.addDirectoryItem(thisPlugin,item_url,listItem,isFolder=True)
    xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    #xbmcplugin.setContent(thisPlugin, 'tvshows')
    xbmc.executebuiltin("Container.SetViewMode(500)")

def GetRecommendedMoviesHbo():
    html = GetSource("http://hbonordic.se/web/hbo/movies")
    soup = BeautifulSoup(html)
    #<div class="js-hbo_video_container hbo_video_container relative clip_container">
    items=soup.findAll('div', attrs={'class' : 'js-hbo_video_container hbo_video_container relative clip_container'})
    
    movies=[]
    for item in items: 
        movie_title = str(item.contents[1].contents[5].contents[1].contents[0])
        movie_url_title = movie_title.lower().replace(" ","-")
        xbmc.log("GetRecommendedMoviesHbo, movie url title: " + movie_url_title)
        url = urlparse.urljoin("http://hbonordic.com/movies/-/-/",movie_url_title)
        xbmc.log("GetRecommendedMoviesHbo, url: " + url)
        movie_cover_url = Get_EpisodeImageUrl(str(item.contents[1].contents[3]))
        movies.append(Movie(movie_title,url,movie_cover_url))
    
    return movies
    
def LoadMovieGenresHbo():
    html = GetSource("http://hbonordic.se/web/hbo/movies")
    soup = BeautifulSoup(html)
    
    items=soup.findAll('ul', attrs={'class' : 'dropdown bg_black hide absolute z_100 align_left'})
    
    for item in items: 
        for genre in item.findAll("li"): 
            genre_name = str(genre.contents[0].contents[0])
            genre_url = urlparse.urljoin("http://hbonordic.com",str(genre.contents[0].attrs[0][1]))
            url=str(sys.argv[0]) + '?' + "mode=show_movies_hbo&url="+urllib.quote_plus(genre_url)
            AddListItem(genre_name,url,True)

def LoadMovieViewHbo(movies):

    # listing = []
    # page=urllib2.urlopen(url)
    # soup = BeautifulSoup(page.read())
    # movies=soup.findAll('ul', attrs={'class' : 'media-list movies clearfix'})
    for movie in movies:
        
        # movie_genre = str(tmp.contents[7].contents[3].contents[0].string).replace('/',',')
        # try:
            # movie_year = int(tmp.contents[7].contents[5].contents[1].string)
        # except:
            # movie_year=0
        # movie_actors = str(tmp.contents[7].contents[9].string).replace('Skådespelare: ','').split(',')
        # movie_director = str(tmp.contents[7].contents[11].string).replace('Regissör: ','')
        # movie_url=urlparse.urljoin(GetDomain(),str(tmp.contents[1].attrs[2][1]))
        # genre = tmp.contents[3].contents[1].contents[1]
        # pushHD=tmp.contents[3].contents[7]
        # if(IsHD(movie_url,genre,pushHD)):
            # overlay=xbmcgui.ICON_OVERLAY_HD
        # else:
            # overlay=xbmcgui.ICON_OVERLAY_NONE
        
        title = str(movie.title).decode("utf-8")
        listItem = xbmcgui.ListItem(title)
        #if(str(movie.imageUrl).startswith("http://")):
        poster = movie.imageUrl
        xbmc.log("Movie poster url: " + poster)
        #else:
        #   poster = Get_EpisodeImageUrl(movie.imageUrl)

        #xbmc.log('Poster: ' + poster)
        listItem.setThumbnailImage(poster)
        #listItem.setLabel2(GetHDTag(movie_url,genre,pushHD))
        #description =FixHtmlString(tmp.contents[7].contents[7].string).decode("utf-8")
        infoLabels = { "Title": title,"Genre": "","Year": "","Director": "","Cast": "","Plot": "",'videoresolution':'','overlay':"" }
        listItem.setInfo(type="Video", infoLabels=infoLabels)
        url=str(sys.argv[0]) + '?' + "url=" + urllib.quote_plus(movie.url) + "&mode=play"
        xbmcplugin.addDirectoryItem(thisPlugin,url,listItem)
        xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
        #print eachmovie['href']+","+eachmovie.string  tmp.contents[1].contents[1]
        #listing.append(unicode(tmp.contents[1].contents[3].string).encode("utf-8"))
    #xbmcplugin.setContent(thisPlugin, 'movies')
    #xbmc.executebuiltin("Container.SetViewMode(508)")
    xbmc.executebuiltin("Container.SetViewMode(500)")
    
def LoadTvSeries(url):
    #url="http://viaplay.se/tv"
    page=urllib2.urlopen(url)
    soup = BeautifulSoup(page.read())
    #DoesSeriesExistAtTvDb('Fringe')
    #show = tvDb["Fringe"]
    #xbmc.log("Epsiode name: " + show[1][1])
    
    items=soup.findAll('ul', attrs={'class' : 'media-list tv clearfix'})
    for item in items:
        for series in item.findAll('li'):
            tv_url = urlparse.urljoin(GetDomain(), str(series.contents[1].attrs[2][1])) #GetDomain() + '/' + str(series.contents[1].attrs[2][1])
            tv_title = unicode(series.contents[7].contents[1].contents[1].attrs[1][1]).encode('utf-8')
            tv_image = Get_PosterUrl(str(series.contents[1].contents[1]))
            listItem = xbmcgui.ListItem(tv_title)
            listItem.setThumbnailImage(tv_image)
            infoLabels = { "Title": tv_title,"tvshowtitle": tv_title }
            listItem.setInfo(type="Video", infoLabels=infoLabels)
            item_url=str(sys.argv[0]) + '?' + "url=" + urllib.quote_plus(tv_url) + "&mode=series&title=" + urllib.quote_plus(tv_title)
            cm_url = str(sys.argv[0]) + '?' + "title=" + urllib.quote_plus(tv_title) + "&mode=add_tv_favorite" + "&url="+urllib.quote_plus(tv_url) +"&poster=" + urllib.quote_plus(tv_image)
            menu_title = unicode(__language__(4019)).encode('utf-8')
            listItem.addContextMenuItems([(menu_title, "XBMC.RunPlugin(%s)" % (cm_url),)],replaceItems=True)
            
            xbmcplugin.addDirectoryItem(thisPlugin,item_url,listItem,isFolder=True)
    xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    #xbmcplugin.setContent(thisPlugin, 'tvshows')
    xbmc.executebuiltin("Container.SetViewMode(500)")
def GetShowData(name):
    db = tvdb_api.Tvdb(cache = True,language="sv",apikey="5736416B121F48D5") #,apikey="5736416B121F48D5"
    #db = tvDb(cache = True,language='sv')
    xbmc.log("Tvdb type:" + str(type(db)))
    return db[name]

def LoadEpisodes_(url,seriesName):
    try:
        xbmc.log("LoadEpisoded URL: " + url)
        page=urllib2.urlopen(url)
        soup = BeautifulSoup(page.read())
        fanart = soup.findAll('div',attrs={'class':'content'})
        url_fan_art= Get_FanArtUrl(str(fanart[0].contents[1].contents[1]))
        seasons=soup.findAll('div', attrs={'class' : 'media-wrapper seasons'})
        
        if(SETTINGS_USETVDB):
            id=GetSeriesID(seriesName)
            
            if(id!=None):
                xbmc.log("ID is not None")
                xbmc.log("TheTvDb Series ID: "+id)
                episodes=GetSeries(id)
            else:
                xbmc.log("ID is None")
                episodes=None
        else:
            episodes=None
        
        for season in seasons:
            for episode in season.findAll('li'):
                episode_url =  urlparse.urljoin(GetDomain() , str(episode.contents[1].attrs[2][1]))
                xbmc.log('Episode url: ' + episode_url)
                test = episode.contents[1].contents[3].contents[0]
                try:
                    title = str(episode.contents[1].contents[3].contents[0]).encode('utf-8')
                except UnicodeDecodeError:
                    title = str(episode.contents[1].contents[3].contents[0]).decode('utf-8')
                else:
                    title = episode.contents[1].contents[3].contents[0]
                episode_image = Get_PosterUrl(str(episode.contents[1].contents[1]))
                try:
                    episode_season = int(GetSeason(episode.contents[1].attrs[2][1]))
                except:
                    episode_season=1
                try:
                    episode_no = int(GetEpisode(episode_url))
                except:
                    episode_no=1
                
                url_title = GetTitleFromUrl(str(episode.contents[1].attrs[2][1]))
                if IsWatchedEpisode(url_title,episode_season,episode_no):
                    overlay=xbmcgui.ICON_OVERLAY_WATCHED
                    playcount=1
                else:
                    overlay=xbmcgui.ICON_OVERLAY_UNWATCHED
                    playcount=0
            
                episode_synopsis = FixHtmlString(unicode(str(episode.contents[7].contents[9].string)).encode('utf-8'))
                episode_title = unicode(__language__(4024)).encode('utf-8') + str(episode_season) + " " + unicode(__language__(4025)).encode('utf-8') + str(episode_no)#title
                
                if(episodes!=None):
                    episode_Name=GetEpisodeName(episode_season,episode_no,episodes)
                    if(episode_Name!=None):
                        episode_title = episode_title + " - " + episode_Name
                    episode_thumbnail = GetEpisodeThumbnail(episode_season,episode_no,episodes)
                    if(episode_thumbnail!=None):
                        episode_image="http://thetvdb.com/banners/"+episode_thumbnail
                
                listItem = xbmcgui.ListItem(title)
                listItem.setThumbnailImage(episode_image)
                listItem.setProperty("Fanart_Image", url_fan_art)
                infoLabels = { "Title": episode_title,"tvshowtitle": title,"season": episode_season,"episode": episode_no,"plotoutline": episode_synopsis,"plot": episode_synopsis,"overlay":overlay,"playcount":playcount}
                listItem.setInfo(type="Video", infoLabels=infoLabels)
                item_url=str(sys.argv[0]) + '?' + "url=" + urllib.quote_plus(episode_url) + "&mode=play"
                
                cm_url_remove = str(sys.argv[0]) + '?' + "season=" + urllib.quote_plus(str(episode_season)) +"&episode="+ urllib.quote_plus(str(episode_no)) +"&mode=remove_watched_episode" + "&title="+urllib.quote_plus(url_title)
                cm_url_add = str(sys.argv[0]) + '?' + "season=" + urllib.quote_plus(str(episode_season)) +"&episode="+ urllib.quote_plus(str(episode_no)) +"&mode=add_watched_episode" + "&title="+urllib.quote_plus(url_title)
                listItem.addContextMenuItems([("Markera som visad", "XBMC.RunPlugin(%s)" % (cm_url_add),),("Markera som inte visad", "XBMC.RunPlugin(%s)" % (cm_url_remove),)],replaceItems=True)
                
                xbmcplugin.addDirectoryItem(thisPlugin,item_url,listItem)
                xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
        xbmcplugin.setContent(thisPlugin, 'episodes')
        xbmc.executebuiltin("Container.SetViewMode(504)")
    except Exception as ex:
        raise ex
        xbmc.log("Error in LoadEpisodes")
        xbmc.log("LoadEpisodes, URL: " + url)

def Get_FanArtUrl(value):
    list=value.split("\"")
    return str(list[3])

def GetTitleFromUrl(value):
    list=value.split("/")
    return str(list[2])
    
def GetSeason(value):
    list=value.split("/")
    for item in list:
        if item.find("season-") >-1:
            season = str(item).replace("season-","")
            return season

def GetEpisode(value):
    list=value.split("/")
    for item in list:
        if item.find("episode-") >-1:
            episode = str(item).replace("episode-","")
            if episode.find("-") > -1:
                episode=episode[:1]
            return episode

def LoadLiveSports(url):
    page=urllib2.urlopen(url)
    soup = BeautifulSoup(page.read())
    sports=soup.findAll('ul', attrs={'class' : 'media-list sport clearfix'})
    for sport in sports:
        for item in sport.findAll('li'):
            sport_url = urlparse.urljoin(GetDomain() , str(item.contents[7].contents[1].contents[1].attrs[2][1]))
            sport_title = FixHtmlString(unicode(item.contents[1].contents[3].string).encode("utf-8"))
            sport_image = Get_PosterUrl(str(item.contents[1].contents[1]))
            sport_hd = str(item.contents[3].contents[7].string)
            sport_genre=unicode(item.contents[7].contents[3].contents[0].string).encode("utf-8")
            sport_starttime = str(item.contents[7].contents[7].contents[1].string)
            sport_startdate = Get_DateTime(str(item.contents[7].contents[1].contents[1].attrs[1][1]))
            sport_desc = FixHtmlString(unicode(item.contents[7].contents[9].string).encode("utf-8"))
            if(IsHD("",sport_hd,"")):
                overlay=xbmcgui.ICON_OVERLAY_HD
            else:
                overlay=xbmcgui.ICON_OVERLAY_NONE
            sport_title = sport_title + " (" + sport_startdate + ")"
            listItem = xbmcgui.ListItem(sport_title)
            listItem.setThumbnailImage(sport_image)
            listItem.setLabel2(sport_startdate)
            infoLabels = { "Title": sport_title,"Genre": sport_genre,"Year": 0,"Director": "","Cast": "","Plot": sport_desc,'Date': Get_Date(sport_startdate),'overlay':overlay }
            listItem.setInfo(type="Video", infoLabels=infoLabels)
            cmd_url=str(sys.argv[0]) + '?' + "url=" + urllib.quote_plus(sport_url) + "&mode=play"
            xbmcplugin.addDirectoryItem(thisPlugin,cmd_url,listItem)
            xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_DATE )
            xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_TITLE )
    #xbmcplugin.setContent(thisPlugin, 'movies')
    xbmc.executebuiltin("Container.SetViewMode(500)")
    xbmc.executebuiltin("Container.SetSortMethod(3)")

def Get_DateTime(value):
    list=value.split(" ")
    return str(list[0]+ " " + list[1])

def Get_Date(value):
    list=value.split(" ")
    return str(list[0])

def LoadLiveSportScheduleGetDays(url):
    page=urllib2.urlopen(url)
    soup = BeautifulSoup(page.read())
    schedule = soup.findAll(lambda tag: tag.name == "section" and tag.attrs)
    for item in schedule:
        if(str(item.attrs[0][1]).startswith('day')):
            id = str(item.attrs[0][1])
            day = unicode(item.contents[1].contents[0]).encode("utf-8")
            date = str(item.contents[1].contents[1].contents[0]).strip()
            url =str(sys.argv[0]) + '?' + "mode=sport_schedule_day&url="+urllib.quote_plus(url)+"&id=" +urllib.quote_plus(id)
            AddListItem(day +" " + date,url,True)
    xbmc.executebuiltin("Container.SetViewMode(50)")

def LoadLiveSportScheduleForSpecificDay(url,id):
    #xbmc.log('----------------- START ----------------')
    #xbmc.log('Url: ' + url + ' id: ' + id)
    page=urllib2.urlopen(url)
    #xbmc.log('Call: urllib2.urlopen')
    soup = BeautifulSoup(page.read())
    #xbmc.log('BeautifulSoup')
    schedule = soup.find("section", {"id": id})
    #schedule = soup.findAll(lambda tag: tag.name == "section")
    #xbmc.log('soup.find')
    events = schedule.findAll('li')
    #xbmc.log('soup.findAll')
    # for item in schedule:
        # if(str(item.attrs[0][1])==id):
    for event in events:
        #xbmc.log('Event')
        event_time = str(event.contents[1].contents[0])
        #xbmc.log('Event_time: ' + event_time)
        event_url = urlparse.urljoin(GetDomain() , str(event.contents[3].contents[1].attrs[1][1]))
        #xbmc.log('Event_url: ' + event_url)
        event_title = str(event.contents[3].contents[1].contents[1].contents[0]).replace("\n","").replace("\t","").strip()
        #xbmc.log('Event_title: ' + event_title)
        event_genre = str(event.contents[3].contents[3].contents[1].contents[1].contents[0]).replace("\n","").replace("\t","").strip()
        #xbmc.log('Event_genre: ' + event_genre)
        title = event_time + " " + event_title + " (" + event_genre +")"
        #xbmc.log('title: '+title)
        listItem = xbmcgui.ListItem(title)
        #xbmc.log('xbmcgui.listitem')
        #listItem.setLabel2(sport_startdate)
        #infoLabels = { "Title": title,"Genre": event_genre}
        #xbmc.log('Infolabels')
        #listItem.setInfo(type="Video", infoLabels=infoLabels)
        xbmc.log('setinfo')
        cmd_url=str(sys.argv[0]) + '?' + "url=" + urllib.quote_plus(event_url) + "&mode=play"
        #xbmc.log('cmd_url')
        xbmcplugin.addDirectoryItem(thisPlugin,cmd_url,listItem)
        #xbmc.log('addDirectoryItem')
        #xbmc.log('----------------- End ----------------')
    #soup.decompose
    #xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_DATE )
    #xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_TITLE )

def LoadMovieView(url):
    #url="http://viaplay.se/film/samtliga/250/most_popular"
    #url="http://viaplay.se/film/hd-filmer/8704"
    listing = []
    page=urllib2.urlopen(url)
    soup = BeautifulSoup(page.read())
    movies=soup.findAll('ul', attrs={'class' : 'media-list movies clearfix'})
    for eachmovie in movies:
        for tmp in eachmovie.findAll('li'):
            movie_genre = str(tmp.contents[7].contents[3].contents[0].string).replace('/',',')
            try:
                movie_year = int(tmp.contents[7].contents[5].contents[1].string)
            except:
                movie_year=0
            movie_actors = str(tmp.contents[7].contents[9].string).replace('Skådespelare: ','').split(',')
            movie_director = str(tmp.contents[7].contents[11].string).replace('Regissör: ','')
            movie_url=urlparse.urljoin(GetDomain(),str(tmp.contents[1].attrs[2][1]))
            genre = tmp.contents[3].contents[1].contents[1]
            pushHD=tmp.contents[3].contents[7]
            if(IsHD(movie_url,genre,pushHD)):
                overlay=xbmcgui.ICON_OVERLAY_HD
            else:
                overlay=xbmcgui.ICON_OVERLAY_NONE
            
            title = unicode(tmp.contents[7].contents[1].contents[1].attrs[1][1]).encode("utf-8") + GetHDTag(movie_url,genre,pushHD)
            listItem = xbmcgui.ListItem(title)
            poster = Get_PosterUrl(str(tmp.contents[1].contents[1]))
            #xbmc.log('Poster: ' + poster)
            listItem.setThumbnailImage(poster)
            listItem.setLabel2(GetHDTag(movie_url,genre,pushHD))
            description =FixHtmlString(tmp.contents[7].contents[7].string).decode("utf-8")
            infoLabels = { "Title": title,"Genre": movie_genre,"Year": movie_year,"Director": movie_director,"Cast": movie_actors,"Plot": description,'videoresolution':'','overlay':overlay }
            listItem.setInfo(type="Video", infoLabels=infoLabels)
            url=str(sys.argv[0]) + '?' + "url=" + urllib.quote_plus(movie_url) + "&mode=play"
            xbmcplugin.addDirectoryItem(thisPlugin,url,listItem)
            xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
            #print eachmovie['href']+","+eachmovie.string  tmp.contents[1].contents[1]
            #listing.append(unicode(tmp.contents[1].contents[3].string).encode("utf-8"))
    xbmcplugin.setContent(thisPlugin, 'movies')
    xbmc.executebuiltin("Container.SetViewMode(508)")
def FixHtmlString(value):
    string =str(value)
    string = string.replace('&aring;','å')
    string = string.replace('&auml;','ä')
    string = string.replace('&ouml;','ö')
    string = string.replace('&Aring;','Å')
    string = string.replace('&Auml;','Ä')
    string = string.replace('&Ouml;','Ö')
    string = string.replace('&hellip;','...')
    string = string.replace('&quot;','\"')
    string = string.replace('&amp;','&')
    string = string.replace('&oslash;','ø')
    string = string.replace('&Oslash;','Ø')
    string = string.replace('&aelig;','æ')
    string = string.replace('&AElig;','Æ')
    string = string.replace('&Eacute;','É')
    string = string.replace('&eacute;','é')
    return string
def unescape(s):
    p = htmllib.HTMLParser(None)
    p.save_bgn()
    p.feed(s)
    return p.save_end()
def GetHDTag(url,genre,pushHD):
    if str(url).find('hd-filmer') > -1:
        return ' (HD)'
    elif str(genre).find('HD-film') > -1:
        return ' (HD)'
    elif str(pushHD).find('push hd') > -1:
        return ' (HD)'
    else:
        return ''
def IsHD(url,genre,pushHD):
    if str(url).find('hd-filmer') > -1:
        return True
    elif str(genre).find('HD-film') > -1:
        return True
    elif str(pushHD).find('push hd') > -1:
        return True
    else:
        return False
def Get_PosterUrl(value):
    list=value.split("\"")
    return str(list[5])

def CreateHtmlFile(url):
    tmpdir=tempfile.gettempdir()
    path = os.path.join(tmpdir, "play.html")
    f = open(path, "w")
    content = '<html><head><title>Startar Viaplay</title><meta http-equiv=\"REFRESH\" content=\"0;url='+ url +'\"> </head><body bgcolor=\"black\"><p>Startar Viaplay...</p></body></html>'
    f.write(content)
    f.close()
    
    return path
    
def SearchForTV(url):
    keyboard = xbmc.Keyboard('')
    keyboard.setHeading('Sök efter serie, skådespelare eller regissör...')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        text = keyboard.getText()
        text = text.replace(' ','+')
        search_url = url + text
        xbmc.log('Search url = ' + search_url)
        LoadEpisodesView(search_url)
def SearchForMovie(url):
    keyboard = xbmc.Keyboard('')
    keyboard.setHeading('Sök efter titel på film, skådespelare eller regissör...')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        text = keyboard.getText()
        text = text.replace(' ','+')
        search_url = url + text
        xbmc.log('Search url = ' + search_url)
        LoadMovieView(search_url)
def LoadSeasons(url):
    page=urllib2.urlopen(url)
    soup = BeautifulSoup(page.read())
    seasons=soup.findAll('div', attrs={'class' : 'media-wrapper seasons'})
    for season in seasons:
        season_Name = unicode(season.contents[1].contents[0]).encode('utf-8')
        #xbmcgui.Dialog().ok( "LoadSeasons",season_Name)
        url=str(sys.argv[0]) + '?' + "mode=viewtvseason&url="+urllib.quote_plus(url)
        AddListItem(season_Name,url,True)
    xbmcplugin.setContent(thisPlugin, 'files')
    xbmc.executebuiltin("Container.SetViewMode(51)")
    
def SetupMovieMenu():

    url=str(sys.argv[0]) + '?' + "mode=movies_all&url="
    AddListItem("Alla",url,True) #Film
    
    # url=str(sys.argv[0]) + '?' + "mode=movies_a_to_z&url="
    # AddListItem("A-Z",url,True) #Film
    
    # url=str(sys.argv[0]) + '?' + "mode=movies_genre&url="
    # AddListItem("Genre",url,True) #Film
    
    url=str(sys.argv[0]) + '?' + "mode=movies_recommended&url="
    AddListItem("Rekommenderat",url,True) #Film
    
    xbmc.executebuiltin("Container.SetViewMode(50)")
    
def SetupMainMenu():
    url=str(sys.argv[0]) + '?' + "mode=movies&url="
    AddListItem("Filmer",url,True) #Film
    
    url=str(sys.argv[0]) + '?' + "mode=tv&url="
    AddListItem("Serier",url,True) #TV
    
    url=str(sys.argv[0]) + '?' + "mode=settings&url="
    AddListItem("Inställningar",url,False) #Inställningar
    
    xbmc.executebuiltin("Container.SetViewMode(50)")
    
def AddListItem(title,url,isFolder):
    listItem = xbmcgui.ListItem(title)
    xbmcplugin.addDirectoryItem(thisPlugin,url,listItem,isFolder=isFolder)
    #xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_LABEL )

def PlayUrl(url):
    xbmc.log("PlayUrl: " + url)
    #xbmc.log('Platform is: ' + os.name)
    #xbmc.log("Hbolauncher path: " + HBOPLAYER_PATH)
    
    if(os.name=='nt'):
        xbmc.log("Launching MceRemoteControl")
        root = os.path.join(ROOT_FOLDER,"resources","lib") #xbmc.translatePath(os.path.join('special://home','plugin.video.hbonordic','resources','lib'))
        path1 = os.path.join(root,"MceRemoteHandler.exe")
        path2 = os.path.join(root,"HboLauncher.exe")
        path3 = os.path.join(root,"url.txt")
        xbmc.log("PalyUrl path: " + path1)
        xbmc.log("Def filesys Encoding: " + sys.getfilesystemencoding())
        
        #test = str(AUTOHOTKEY_PATH)
        #sp.Popen([str(path).decode(sys.stdout.encoding)])
        #xbmc.log("Python IO Encoding: " + os.environ['PYTHONIOENCODING'])
        #os.environ['PYTHONIOENCODING']='utf-8'
        #sp.call([path.encode('mbcs')])
        os.startfile(unicode(path1,'utf-8'))
        #os.system(str(AUTOHOTKEY_PATH).encode(sys.getfilesystemencoding()))
        xbmc.log("Launching Hbolauncher")
        
        txt_file = open(unicode(path3,'utf-8'),"w")
        txt_file.write(url)
        txt_file.close()
        
        os.startfile(unicode(path2,'utf-8'))
        #p=sp.Popen([HBOPLAYER_PATH, "-k",url])
        #p.wait()
    else:
        if(sys.platform=='darwin'):
            PlaybackInSafariOSx(url, SETTINGS_USERNAME, SETTINGS_PASSWORD)
        else:
            xbmc.log("Launching Webbrowser")
            webbrowser.open(url)
            
def PlaybackInSafariOSx(url, user, password):
    """
    Depends on osascript (AppleScript) and the free cliclick binary (http://www.bluem.net/en/mac/cliclick/)
    osascript must be able to load the script hbo_nordic_safari.scpt.
    
    The AppleScript is written specifically for Safari - but most of the interesting bits is javascript that Safari
    is asked to execute in order to calculate screen coordinates for buttons etc.
    
    The script is located in resources/lib along with the cliclick binary
    """
    if(sys.platform != 'darwin'):
        xbmc.log("Not running on darwin platform - aborting. PlaybackInSafariOSx can only be run on OSx since it depends on AppleScript ~ osascript")
        return 

    lib = os.path.join(ROOT_FOLDER,"resources","lib")
    
    xbmc.log("Launching Safari using AppleScript and starting maximized playback")
    script = 'hbo_nordic_safari.scpt'
    
    #cliclick binary is expected to be executable, and for some reason XBMC removes the executable permission for the binary when installing from zip
    cliclick_binary = os.path.join(lib, 'cliclick')
    try:
        os.chmod(cliclick_binary, 0755)
    except Exception, e:
        xbmc.log("Failed changing permissions on {0} {1}".format(cliclick_binary, e.strerror))
 
    try:
        hboProc = sp.Popen(['nohup','osascript', os.path.join(lib, script), url, user, password], stdout = sp.PIPE, stderr = sp.STDOUT)
        stdout = hboProc.communicate()[0] ##output is written to nohup.out
        

#        while True:
#            line = hboProc.stdout.readline()
#            code = hboProc.poll()
#           
#            if line == '':
#                if code != None:
#                    break
#            else:
#                xbmc.log("hbo_nordic_safari.scpt: {0}".format(line))
#                continue
#        if hboProc.returncode != 0:
#            xbmc.log("Script failed, see previous log statements for troubleshooting")
#        else:
        xbmc.log("Done executing hbo_nordic_safari.scpt")
    except OSError, e:
        # Ignore, but log the error
        if (e.strerror == "No child processes"):
            xbmc.log("TODO: 'No child processes' happens in subprocess (and popen2) modules in Python 2.6 - patch or upgrade Python to get rid of it - [Errno: {0} - {1}]".format(e.errno, e.strerror))
            pass
        else:
            raise e
    



def GetXbmcVersion():
    #rev_re = re.compile(' r(\d+)') 
    #xbmc_rev = int(rev_re.search(xbmc.getInfoLabel( "System.BuildVersion" )).group(1))
    return xbmc.getInfoLabel( "System.BuildVersion" )

def CheckForUpdate():
    xbmc.log("Checking For update...")
    currentVersion= xbmcaddon.Addon().getAddonInfo('version')
    xbmc.log("Current version is: " + currentVersion)
    page=urllib2.urlopen("http://www.dsd.se/viaplay/latestversion.txt")
    newVersion=page.read()
    xbmc.log("New version is: "+newVersion)
    if(newVersion > currentVersion):
        xbmcgui.Dialog().ok("Viaplay add-on", "There's a new version available." + newVersion)
    else:
        xbmcgui.Dialog().ok("Viaplay add-on", "You are currently running the latest version.")
        
params = parameters_string_to_dict(sys.argv[2])
mode = params.get("mode", None)
url = urllib.unquote_plus(params.get("url",  ""))
title = urllib.unquote_plus(params.get("title",  ""))
id = urllib.unquote_plus(params.get("id",  ""))
poster = urllib.unquote_plus(params.get("poster",  ""))
season = urllib.unquote_plus(params.get("season",  ""))
episode  = urllib.unquote_plus(params.get("episode",  ""))
seasonno=params.get("seasonno",  0)

if not sys.argv[2] or not mode: 
    SetupMainMenu()
    CreateDatabase()
    UpgradeDatabase()
    xbmc.log("Database Version: " + DatabaseVersion())
    #Check if username and password are set, if not then notify user
    if(len(SETTINGS_USERNAME)==0):
        xbmc.executebuiltin('xbmc.Notification('+unicode(__language__(4009)).encode('utf-8')+','+unicode(__language__(4010)).encode('utf-8')+',8000)')
        
elif mode=="view_sports":
    LoadLiveSports(url)
elif mode=="checkupdate":
    CheckForUpdate()
elif mode=="favorites_tv":
    LoadTvFavorites()
elif mode=="add_tv_favorite":
    AddFavorite(str(title).decode('utf-8'),"tv",url,poster,0,"","")
    xbmc.executebuiltin("xbmc.Notification(Information,"+ unicode(__language__(4022)).encode('utf-8') +",4000)")
elif mode=="remove_tv_favorite":
    dialog = xbmcgui.Dialog()
    ret = dialog.yesno('HBO Nordic',unicode(__language__(4021)).encode('utf-8') +" '"+ title +"'?") #Do you want to remove favorite
    if ret:
        RemoveFavorite(id)
        xbmc.executebuiltin("Container.Refresh")
elif mode=="remove_watched_episode":
    RemoveWatchedEpisode(title,season,episode)
    xbmc.executebuiltin("Container.Refresh")
elif mode=="add_watched_episode":
    AddWatchedEpisode(title,season,episode)
    xbmc.executebuiltin("Container.Refresh")
elif mode=="view_sport_schedule":
    LoadLiveSportScheduleGetDays(url)
elif mode =="sport_schedule_day":
    tmp_url = urlparse.urljoin(GetDomain() ,"/sport")
    xbmc.log("Before, LoadLiveSportScheduleForSpecificDay, url: " + tmp_url + " id: " +id)
    LoadLiveSportScheduleForSpecificDay(tmp_url,id)
    xbmc.log('Finished')
elif mode=="series_episodes":
    GetEpisodesHbo(url,title,seasonno)
    xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
elif mode=="serieshbo":
    LoadSeasonsHbo(url,title)
    xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
elif mode=='search_movie':
    SearchForMovie(url)
elif mode=='search_tv':
    SearchForTV(url)
elif mode=='movies_genre':
    LoadMovieGenresHbo()
elif mode=='view_movie_alphabet':
    LoadMoviesByAlphabet(url)
elif mode=='view_tv_episodes':
    LoadEpisodesView(url)
elif mode=='series':
    #LoadSeasons(url)
    #showData=GetShowData('Lost')
    #xbmc.log("TV-Series title: " + title)
    LoadEpisodes(url,title)
elif mode=='viewtv':
    LoadTvSeries(url)
elif mode=='tv':
    #SetupTvMenu()
    GetSeriesHbo()
    xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
elif mode=="movies_recommended":
    movies = GetRecommendedMoviesHbo()
    LoadMovieViewHbo(movies);
elif mode=="movies_all":
    movies = GetAllMoviesHbo()
    LoadMovieViewHbo(movies);
elif mode=='movies':
    SetupMovieMenu()
    xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
elif mode=='view':
    LoadMovieView(url)
elif mode=='categoriestv':
    SetupCategoriesTV()
elif mode=='settings':
    __settings__.openSettings()
    ReloadSettings()
elif mode=='categories':
    SetupCategories()
elif mode == 'play':
    #path=CreateHtmlFile(url)
    #webplayer = xbmc.Player()
    #webplayer.play(path)
    if season <> "":
        AddWatchedEpisode(title,season,episode)
        xbmc.executebuiltin("Container.Refresh")

    xbmc.log("Play URL: " + url)
    PlayUrl(url)
    #xbmcgui.Dialog().ok( "Play", url )
#xbmcplugin.addSortMethod( thisPlugin, sortMethod=xbmcplugin.SORT_METHOD_LABEL )
xbmcplugin.endOfDirectory(thisPlugin)