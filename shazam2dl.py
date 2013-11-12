#!/usr/bin/python2.6
# -*- coding: utf-8 -*- 

import urllib
import HTMLParser
import urllib2
import re
import sys
import json
import os
import time
import subprocess
import shazam_api
import smtplib
from os import listdir, remove
from os.path import isfile, join, getsize

if os.path.ismount("/data/musique/files/Musique") == False:
    sys.exit(1)

dl_dir = "/data/musique/files/Musique/"
fb_login = sys.argv[1]
fb_pass = sys.argv[2]

uid_cookie, fat_cookie = shazam_api.get_api_cookie(fb_login, fb_pass)
html_parser = HTMLParser.HTMLParser()
already_dl = [ f for f in listdir(unicode(dl_dir)) if isfile(join(dl_dir,f)) ]
FNULL = open('/dev/null' , 'w')

def add_proper_headers(http_req, accept, referer, cookie = ""):
    http_req.add_header('User-Agent', "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0")
    http_req.add_header('Accept', accept)
    http_req.add_header('Accept-Language', "fr,fr-fr;q=0.8,en-us;q=0.5,en;q=0.3")
    http_req.add_header('Connection', "keep-alive")
    http_req.add_header('Referer', referer)
    if cookie != "":
        http_req.add_header('Cookie', cookie)


def get_shazam_tags(fat_cookie, uid_cookie):
    tags = []
    req = urllib2.Request("http://www.shazam.com/fragment/myshazam?size=large")
    add_proper_headers( req, 
                        accept = "application/json, text/javascript, */*; q=0.01",
                        referer = "http://www.shazam.com/myshazam",
                        cookie = "fat=" + fat_cookie + "; uid=" + uid_cookie + ";"
                      )
    resp = urllib2.urlopen(req)
    content = json.loads(resp.read())['feed'].split('\n')

    i = 0
    for line in content:
        if len(re.findall('tg-title">(.*)<', line)) > 0:
            title = re.findall('url">(.*)</a', content[i])[0]
            artist = re.findall('tg-artist">(.*)<', content[i+1])[0]
            filename = html_parser.unescape(title + '-' + artist + ".mp3")
            if { 'artist' : artist, 'title' : title } not in tags and filename not in already_dl:
                tags += [{ 'artist' : artist, 'title' : title, 'filename' : filename }]
        i += 1
    return tags
    
def get_youtube_links(title, artist):
    links = []
    youtube_search = "http://gdata.youtube.com/feeds/api/videos?q=" + urllib.quote(title + " " + artist) + "&v=2&max-results=4&start-index=1&category=Music&format=5&fields=entry(id,title,link[@rel=%27alternate%27],author(name),yt:statistics,media:group(media:content),media:group(media:thumbnail))&alt=json-in-script&callback=define&key=AI39si6WqJb0Pbzi0lVyf3RMFS0DKg23xVBcBXDwnkzZGEMWP_JKsMQ47-6P8rV4BRkre3YNjhvXuSJ6dWeInyweJ2vmlOBJtw".encode('utf-8')

    req = urllib2.Request(youtube_search)
    add_proper_headers(req, "*/*", "http://www.shazam.com/myshazam")
    resp = urllib2.urlopen(req)
    json_resp = json.loads( resp.readlines()[1][7:-2] )
    for entry in json_resp['feed']['entry']:
        links += [entry['link'][0]['href']]
    return links

def try_dl_mp3_1(youtube_link, filename):
    dl_link = "http://youtubeinmp3.com/fetch/?video=" + youtube_link
    print "Try to download from " + dl_link + " ... "
    req = urllib2.Request(dl_link)
    add_proper_headers( req,
                        accept = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        referer = "http://youtubeinmp3.com/api"
                      )
    resp = urllib2.urlopen(req)
    fd = open(dl_dir + filename, "w")
    fd.write(resp.read())
    fd.flush()
    fd.close()
    filesize = getsize(dl_dir + filename)
    if filesize < 1048576:
        remove(dl_dir + filename)    
        return False
    else:
        return True

def try_dl_mp3_2(youtube_link, filename):
    convert_url = "http://www.vidtomp3.com/cc/conversioncloud.php"
    post_data = { 'mediaurl' : youtube_links }
    post_data = urllib.urlencode(post_data)
    req = urllib2.Request(convert_url)
    add_proper_headers( req,
                        accept = "text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01",
                        referer = "http://www.vidtomp3.com/process.php"
                      )
    resp = urllib2.urlopen(req, post_data)
    server, video_id, key = re.findall('([a-zA-Z0-9]+).vidtomp3.com.*\?videoid=([0-9]+)&key=(.*)"', resp.read())[0]

    status_url = "http://"+server+".vidtomp3.com/api/?videoid="+video_id+"&key=" + key
    req = urllib2.Request(status_url)
    resp = urllib2.urlopen(req)
    dl_url = re.findall('<downloadurl><\!\[CDATA\[(.*)/\]\]></downloadurl>', resp.read())[0]

    dl_url = urllib.unquote(dl_url)
    print "Try to download from " + dl_url + " ... "
    req = urllib2.Request(dl_url)
    resp = urllib2.urlopen(req)

    fd = open(dl_dir + filename, "w")
    fd.write(resp.read())
    fd.flush()
    fd.close()
    filesize = getsize(dl_dir + filename)
    if filesize < 1048576:
        remove(dl_dir + filename)    
        return False
    else:
        return True

def sendemail(artist, titre):
    sender = 'molho.michael@orange.fr'
    receivers = ['michael.molho@gmail.com']

    message =  "From: shazam2dl <shazam2dl@orange.fr>\n"
    message += "To: michael <michael.molho@gmail.com>\n"
    message += "Subject: [shazam2dl] Nouveau morceau telecharge\n\n"
    message += artist + " : " + titre

    try:
        smtpObj = smtplib.SMTP('smtp.orange.fr')
        smtpObj.sendmail(sender, receivers, message)         
    except SMTPException:
        print "Error: unable to send email"
    


tags = get_shazam_tags(fat_cookie, uid_cookie)

for tag in tags:
    dl_result = False
    title = unicode(html_parser.unescape(tag['title'])).encode('utf-8')
    artist = unicode(html_parser.unescape(tag['artist'])).encode('utf-8')

    print "######## " + title + " -- " + artist

    youtube_links = get_youtube_links(title, artist)

    for link in youtube_links:
        dl_result = try_dl_mp3_1( link, tag['filename'] )
        if dl_result == True:
            break

    if dl_result == False:
        for link in youtube_links:
            dl_result = try_dl_mp3_2( link, tag['filename'] )
            if dl_result == True:
                break

    if dl_result == True:
        subprocess.Popen(["/usr/local/bin/eyeD3", "--v1", "-a", artist, "-t", title, dl_dir + tag['filename']], stdout=FNULL, stderr=FNULL)
        subprocess.Popen(["/usr/local/bin/eyeD3", "--v2", "-a", artist, "-t", title, dl_dir + tag['filename']], stdout=FNULL, stderr=FNULL)
        sendemail(artist, title)
    else:
        print "FAILED !!"
