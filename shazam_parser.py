from bs4 import BeautifulSoup

def parse(content):
    final_list = []
    titles_ok = []
    artists_ok = []

    parsed = BeautifulSoup(content)

    titles = parsed.find_all('h4', attrs={'class':'tl-title'})
    artists = parsed.find_all('h5', attrs={'class':'tl-artist'})

    for title in titles:
        titles_ok += [title.find('a').text]

    for artist in artists:
        artists_ok += [artist.text]

    final_list = [(artists_ok[i], titles_ok[i]) for i in xrange(0,len(artists_ok))]

    return final_list




