#!/usr/bin/python2.7
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
import shazam_parser
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
import pprint
import shutil
import optparse
from os import listdir, remove
from os.path import isfile, join, getsize


####################
### Global Vars
###################

fb_login = ""
fb_pass = ""
dl_dir = ""


html_parser = HTMLParser.HTMLParser()
pp = pprint.PrettyPrinter(indent=4)
FNULL = open('/dev/null' , 'w')

def normalize_str(elem):
    norm = re.sub(r'/', '-', elem)
    norm = re.sub(r'[/",;]+', '', norm)
    norm = re.sub(r'&', 'and', norm)
    norm = re.sub(r'\(.+\)', '', norm)
    norm = norm.strip()
    if norm[0:3] == "by ":
       norm = norm[3:]
    return norm

def add_proper_headers(http_req, accept, referer, cookie = ""):
    http_req.add_header('User-Agent', "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0")
    http_req.add_header('Accept', accept)
    http_req.add_header('Accept-Language', "fr,fr-fr;q=0.8,en-us;q=0.5,en;q=0.3")
    http_req.add_header('Connection', "keep-alive")
    http_req.add_header('Referer', referer)
    if cookie != "":
        http_req.add_header('Cookie', cookie)


def get_shazam_tags(fat_cookie, uid_cookie):
    my_tags = []
    req = urllib2.Request("http://www.shazam.com/fragment/myshazam?size=large")
    add_proper_headers( req, 
                        accept = "application/json, text/javascript, */*; q=0.01",
                        referer = "http://www.shazam.com/myshazam",
                        cookie = "fat=" + fat_cookie + "; uid=" + uid_cookie + ";"
                      )
    resp = urllib2.urlopen(req)
    json_content = json.loads(resp.read())['feed']
    all_tags = shazam_parser.parse( html_parser.unescape(json_content) )
    

    for tag in all_tags:
            artist = normalize_str(tag[0])
            title = normalize_str(tag[1])
            filename = title + '-' + artist + ".mp3"
            if { 'artist' : artist, 'title' : title } not in my_tags and filename not in already_dl:
                my_tags += [{ 'artist' : artist, 'title' : title, 'filename' : filename }]
    return my_tags
    
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

def download_mp3(youtube_link, filename):
    print '    + Try to download from ' + youtube_link
    try:
        filename_tmp = '.'.join(filename.split('.')[:-1]) + '.%(ext)s'
        subprocess.call(["/usr/bin/youtube-dl", "--quiet", "--extract-audio", '--output='+filename_tmp, '--audio-format=mp3', youtube_link])
        shutil.move(filename, dl_dir + 'to-valid-' + filename )
        return True
    except Exception,e:
        print str(e)
        return False


def send_report(status,to):
    from_addr = "mmobox <shazam2dl@mmobox.fr>"

    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = COMMASPACE.join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = "[shazam2dl] Download Report"

    body = ""
    for song in status:
        body += song['artist'] + ' || ' + song['title'] + '  (' + song['status'] + ')\n'

    msg.attach( MIMEText(body) )

    smtp = smtplib.SMTP("localhost")
    smtp.sendmail(from_addr, to, msg.as_string() )
    smtp.close()
    


####################
## Parse Args
###################

usage = "usage: %prog [options] facebook-login facebook-password target-dir"
parser = optparse.OptionParser(usage=usage)
opt, args = parser.parse_args()

if len(args) != 3:
    parser.print_help()
    sys.exit(1)
else:
    fb_login = args[0]
    fb_pass = args[1]
    dl_dir = args[2]



####################
## MAIN
###################

uid_cookie, fat_cookie = shazam_api.get_api_cookie(fb_login, fb_pass)
already_dl = [ f for f in listdir(unicode(dl_dir)) if isfile(join(dl_dir,f)) ]
tags = get_shazam_tags(fat_cookie, uid_cookie)
status = []

if len(tags) == 0:
    print 'Noting to do ...'
    sys.exit(0)

for tag in tags:
    dl_result = False
    title = unicode(tag['title']).encode('utf-8')
    artist = unicode(tag['artist']).encode('utf-8')

    print "######## " + title + " -- " + artist

    youtube_links = get_youtube_links(title, artist)

    for link in youtube_links:
        dl_result = download_mp3( link, tag['filename'] )
        if dl_result == True:
            print '    + Download succeed !'
            break
        else:
            print '    + Failed ! Try again ...'

    if dl_result == True:
        print '    + Reencoding ...'
        reenc = subprocess.call(["/usr/bin/lame", dl_dir + 'to-valid-' + tag['filename'], dl_dir + tag['filename']], stdout=FNULL, stderr=FNULL)
        os.remove( dl_dir + 'to-valid-' + tag['filename'] )
        print '    + Writing mp3 tags ...'
        eyed3 = subprocess.call(["/usr/local/bin/eyeD3", "-a", artist, "-t", title, dl_dir + tag['filename']], stdout=FNULL, stderr=FNULL)
        eyed3 = subprocess.call(["/usr/local/bin/eyeD3", "--to-v1.1", dl_dir + tag['filename']], stdout=FNULL, stderr=FNULL)
        status += [{'artist' : artist, 'title' : title, 'status' : 'OK'}]
    else:
        status += [{'artist' : artist, 'title' : title, 'status' : '*FAILED*'}]
        print "    + IMPOSSIBLE TO DOWNLOAD !"

print "+ Sending report !"

######################
## SEND REPORT
#####################

send_report(status,["michael.molho@gmail.com"])
