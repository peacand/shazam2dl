#!/usr/bin/python2.7
# -*- coding: utf-8 -*- 

import urllib
import HTMLParser
import urllib2
import re
import sys
import json
import os
import cookielib

global cookies 
global user_id
global access_token
html_parser = HTMLParser.HTMLParser()

class MyHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        global cookies
        global user_id
        global access_token
       
        if "https://www.facebook.com/dialog/oauth?redirect_uri=" in headers['Location']:
            formated_cookies = ';'.join( [cookie.name+"="+cookie.value for cookie in cookies if cookie.name in ['datr', 'c_user', 'csm', 'fr', 'lu', 's', 'xs']] )
            redirect_url = headers['Location']

            redirect_req = urllib2.Request(redirect_url)
            add_proper_headers(redirect_req, "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "www.google.fr", formated_cookies )
            resp = urllib2.urlopen(redirect_req)

            access_token = re.findall('access_token=(.*)&expires_in', resp.read())[0]
            user_id = re.findall('c_user=([0-9]+);', formated_cookies)[0]
            return resp
        return urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
            



cookies = cookielib.CookieJar()
handlers = [urllib2.HTTPHandler(), urllib2.HTTPSHandler(), urllib2.HTTPCookieProcessor(cookies), MyHTTPRedirectHandler]
opener = urllib2.build_opener(*handlers)
urllib2.install_opener(opener)



def add_proper_headers(http_req, accept, referer="", cookie = ""):
    http_req.add_header('User-Agent', "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0")
    http_req.add_header('Accept', accept)
    http_req.add_header('Accept-Language', "fr,fr-fr;q=0.8,en-us;q=0.5,en;q=0.3")
    http_req.add_header('Connection', "keep-alive")
    if referer != "":
        http_req.add_header('Referer', referer)
    if cookie != "":
        http_req.add_header('Cookie', cookie)


def get_post_params():
    login_get = "https://www.facebook.com/login.php?skip_api_login=1&api_key=210827375150&signed_next=1&next=https%3A%2F%2Fwww.facebook.com%2Fdialog%2Foauth%3Fredirect_uri%3Dhttp%253A%252F%252Fstatic.ak.facebook.com%252Fconnect%252Fxd_arbiter%252FwTH8U0osOYl.js%253Fversion%253D40%2523cb%253Df3c228e9a4706b2%2526domain%253Dwww.shazam.com%2526origin%253Dhttp%25253A%25252F%25252Fwww.shazam.com%25252Ff2034f83cb7b1b6%2526relation%253Dopener%2526frame%253Df3ea495ebf74802%26display%3Dpopup%26scope%3Demail%252Cpublish_actions%26response_type%3Dtoken%252Csigned_request%26domain%3Dwww.shazam.com%26client_id%3D210827375150%26ret%3Dlogin%26sdk%3Djoey&cancel_uri=http%3A%2F%2Fstatic.ak.facebook.com%2Fconnect%2Fxd_arbiter%2FwTH8U0osOYl.js%3Fversion%3D40%23cb%3Df3c228e9a4706b2%26domain%3Dwww.shazam.com%26origin%3Dhttp%253A%252F%252Fwww.shazam.com%252Ff2034f83cb7b1b6%26relation%3Dopener%26frame%3Df3ea495ebf74802%26error%3Daccess_denied%26error_code%3D200%26error_description%3DPermissions%2Berror%26error_reason%3Duser_denied%26e2e%3D%257B%257D&display=popup"

    resp = urllib2.urlopen(login_get)
    resp_content = resp.read()
    formated_cookies = ';'.join([cookie.name+"="+cookie.value for cookie in cookies])
    param_lsd = re.findall('name="lsd" value="(.*)" autocomplete="off" />', resp_content)[0]
    param_lgnrnd = re.findall('name="lgnrnd" value="(.*)" /><input type', resp_content)[0]
    #param_next = re.findall('name="next" value="(.*)"', resp_content)[0]
    login_post_url = html_parser.unescape("https://www.facebook.com/" + re.findall('action="/(login.php\?login_attempt=1.*)" method="post"', resp_content)[0])
    #return login_post_url, formated_cookies, param_lsd, param_lgnrnd, param_next
    return login_post_url, formated_cookies, param_lsd, param_lgnrnd


def get_api_cookie(login, password):
    global cookies
    global user_id
    global access_token

    #login_post_url, formated_cookies, param_lsd, param_lgnrnd, param_next = get_post_params()
    login_post_url, formated_cookies, param_lsd, param_lgnrnd = get_post_params()

    post_data = { 'lsd':param_lsd,
                  'api_key':'210827375150',
                  'display':'popup',
                  'enable_profile_selector':'',
                  'legacy_return':'1',
                  #'next' : html_parser.unescape(param_next), 
                  'profile_selector_ids':'',
                  'skip_api_login':'1',
                  'signed_next':'1',
                  'trynum':'1',
                  'timezone':'',
                  'lgnrnd':param_lgnrnd,
                  'lgnjs':'n',
                  'email':login,
                  'pass':password,
                  'default_persistent':'0',
                  'login':'Connexion' }

    post_data = urllib.urlencode(post_data)
    req = urllib2.Request(login_post_url)
    add_proper_headers(req, "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", cookie=formated_cookies )
    resp = urllib2.urlopen(req, post_data)
    return user_id, access_token


