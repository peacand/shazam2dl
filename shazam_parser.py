from bs4 import BeautifulSoup
import time
import re

def parse(content):
    final_list = []
    titles_ok = []
    artists_ok = []
    delay_ok = []

    parsed = BeautifulSoup(content)

    dates = parsed.find_all('span', attrs={'data-time' : re.compile('[0-9]+')})
    titles = parsed.find_all('p', attrs={'class':'ti__title'})
    artists = parsed.find_all('p', attrs={'class':'ti__artist'})

    for date in dates:
        delay_ok += [ int(time.time()) - int(date['data-time'][:-3]) ] 

    for title in titles:
        titles_ok += [title.find('a').text]

    for artist in artists:
        artists_ok += [artist.text]

    final_list = [ (artists_ok[i], titles_ok[i], delay_ok[i]) for i in xrange(0,len(artists_ok)) ]

    return final_list




