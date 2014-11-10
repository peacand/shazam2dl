from bs4 import BeautifulSoup
import time

def parse(content):
    final_list = []
    titles_ok = []
    artists_ok = []
    delay_ok = []
    one_day = 60*60*24

    parsed = BeautifulSoup(content)

    dates = parsed.find_all('span', attrs={'class' : 'tl-date'})
    titles = parsed.find_all('h4', attrs={'class':'tl-title'})
    artists = parsed.find_all('h5', attrs={'class':'tl-artist'})

    for date in dates:
        delay_ok += [ int(time.time()) - int(date['data-time'][:-3]) ] 

    for title in titles:
        titles_ok += [title.find('a').text]

    for artist in artists:
        artists_ok += [artist.text]

    final_list = [ (artists_ok[i], titles_ok[i]) for i in xrange(0,len(artists_ok)) if delay_ok[i] < one_day ]

    return final_list




