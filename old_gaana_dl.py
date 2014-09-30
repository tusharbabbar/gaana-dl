import requests, re, sys, os
import argparse
from bs4 import BeautifulSoup

class GaanaDownloader():
    def __init__(self):
        self.urls = {
            'search' : 'http://gaana.com/search/songs/{query}',
            'get_token' : 'http://gaana.com//streamprovider/get_stream_data_v1.php',
            'search_album' : 'http://gaana.com/search/albums/{query}',
            'search_artist' : 'http://gaana.com/search/artists/{query}',
            'album' : 'http://gaana.com/album/{name}',
            'artist' : 'http://gaana.com/artist/{name}'}

    def _get_url_contents(self, url):
        url = url.replace(' ','%20')
        response = requests.get(url, proxies = proxies)
        if response.status_code == 200:
            return response
        else:
            raise BadHTTPCodeError(response.status_code)

    def get_search_song(self, query, dir_name):
        url = self.urls['search'].format(query = query)
        response = self.get_url_contents(url)
        soup = BeautifulSoup(response.content)
        songs = soup.find_all('div',{'id':re.compile('_item_row_')})
        if songs:
            for song in songs:
                _id = song['id'].split('_')[-1]
                track_name = song.ul.text.strip().split('\n')[0]
                track_name = track_name.replace(' ','-')
                #print _id
                if self.download_track(_id, track_name, dir_name):
                    break;
                #for song in songs:
                    #track, ablum, artist = song.ul.text.strip().split('/n')[0:3]
                    #print song.ul.text.strip().split('/n')[0:3]
                    ###print track, album, artist
        else:
            print 'No song found'

    def get_songs_from_url(self, name, _type):
        import os
        url = self.urls[_type].format(name = name)
        response = self.get_url_contents(url)
        soup = BeautifulSoup(response.content)
        songs = soup.find_all('div',{'id':re.compile('_item_row_')})
        print 'making dir'
        os.system('mkdir %s'%name)
        if songs:
            for song in songs:
                _id = song['id'].split('_')[-1]
                track_name = song.ul.text.strip().split('\n')[0]
                track_name = track_name.replace(' ','-')
                if self.download_track(_id, track_name, name):
                    continue
                self.get_search_song(track_name, name)
                #print _id
                #if self.download_track(_id, track_name):
                    #pass
                ##for song in songs:
                    #track, ablum, artist = song.ul.text.strip().split('/n')[0:3]
                    #print song.ul.text.strip().split('/n')[0:3]
                    ###print track, album, artist
        else:
            print 'No song found'


    def get_search_album(self, query):
        url = self.urls['search_album'].format(query = query)
        response = self.get_url_contents(url)
        soup = BeautifulSoup(response.content)
        print soup
        albums = soup.find_all('a',{'class':re.compile('play-song-small')})
        print albums
        if albums:
            print 'options are :'
            i = 0
            for album in albums:
                print i,album['href']
                i +=1
            option = raw_input('choose one number: ')
            name = albums[int(option)]['href'].split('/')[-1]
            print name
            self.get_songs_from_url(name, 'album')

    def get_search_artist(self, query):
        url = self.urls['search_artist'].format(query = query)
        response = self.get_url_contents(url)
        soup = BeautifulSoup(response.content)
        print soup
        artists = soup.find_all('li',{'id':re.compile('_item_row')})
        if artists:
            print 'options are:'
            i = 0
            for artist in artists:
                print i,artist.a['href'].split('/')[-1]
                i+=1
            option = raw_input('choose one number: ')
            name = artists[int(option)].a['href'].split('/')[-1]
            self.get_songs_from_url(name, 'artist')


    def download_track(self, _id, track_name, dir_name):
        res = requests.post(self.urls['get_token'], data = {'track_id':int(_id), 'protocol':'http', 'quality': 'mp3'})
        print res
        if res.status_code == 200:
            print res.json()
            stream_path = res.json()['stream_path']
            res = requests.get(stream_path)
            track_name = track_name.replace('/','_')
            if res.status_code == 200:
                with open(dir_name + '/' +track_name+'.mp3', 'wb') as f:
                    print track_name
                    f.write(res.content)
                return True
            else:
                print 'Could not download'

