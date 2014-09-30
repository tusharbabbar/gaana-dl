import requests, re
from bs4 import BeautifulSoup
from flask.ext.script import Manager

proxies = {'http':'http://192.168.1.8:8080',
            'https':'http://192.168.1.8:8080'}

class BadHTTPCodeError(Exception):
    def __init__(self, code):
        print code

class GaanaDownloader():
    def __init__(self):
        self.urls = {
            'search' : 'http://gaana.com/search/songs/{query}',
            'get_token' : 'http://gaana.com//streamprovider/get_stream_data_v1.php',
            'search_album' : 'http://gaana.com/search/albums/{query}',
            'search_artist' : 'http://gaana.com/search/artists/{query}',
            'album' : 'http://gaana.com/album/{name}',
            'artist' : 'http://gaana.com/artist/{name}',
            'search_songs_new' : 'http://api.gaana.com/index.php?type=search&subtype=search_song&content_filter=2&key={query}',
            'search_albums_new' : 'http://api.gaana.com/index.php?type=search&subtype=search_album&content_filter=2&key={query}',
            'get_song_url' : 'http://api.gaana.com/getURLV1.php?quality=medium&album_id={album_id}&delivery_type=stream&hashcode={hashcode}&isrc=0&type=rtmp&track_id={track_id}',
            'album_details' : 'http://api.gaana.com/index.php?type=album&subtype=album_detail&album_id={album_id}'
        }

    def _create_hashcode(self, track_id):
        from base64 import b64encode as en
        import hmac
        key = 'ec9b7c7122ffeed819dc1831af42ea8f'
        hashcode = hmac.new(key, en(track_id)).hexdigest()
        return hashcode
    
    def _get_song_url(self, track_id, album_id):
        from base64 import b64decode as dec
        url = self.urls['get_song_url']
        hashcode = self._create_hashcode(track_id)
        url = url.format(track_id = track_id, album_id = album_id, hashcode = hashcode)
        response = requests.get(url , headers = {'deviceType':'GaanaAndroidApp', 'appVersion':'V5'}, proxies = proxies )
        song_url_b64 = response.json()['data']
        print song_url_b64
        song_url = dec(song_url_b64)
        return song_url

    def _download_track(self, song_url):
        response = self._get_url_contents(song_url)
        with open('temp.mp3','wb') as f:
            f.write(response.content)

    def search_songs(self, query):
        from pprint import pprint
        url = self.urls['search_songs_new']
        url = url.format(query = query)
        response = self._get_url_contents(url)
        tracks = response.json()['tracks']
        tracks_list = map(lambda x:[x['track_title'],x['track_id'],x['album_id'],x['album_title']], tracks)
        pprint(tracks_list)
        i = raw_input('Enter a number :')
        i = int(i)
        song_url = self._get_song_url(tracks_list[i][1], tracks_list[i][2])
        self._download_track(song_url)

    def search_albums(self, query):
        from pprint import pprint
        url = self.urls['search_songs_new']
        url = url.format(query = query)
        response = self._get_url_contents(url)
        albums = response.json()['tracks']
        albums_list = map(lambda x:[x['album_id'],x['album_title']], albums)
        pprint(albums_list)
        album_details_url = self.urls['album_details']
        album_details_url = album_details_url.format(album_id = albums_list[0][0])
        response = requests.get(album_details_url , headers = {'deviceType':'GaanaAndroidApp', 'appVersion':'V5'}, proxies = proxies )
        tracks = response.json()['tracks']
        #tracks = response.json()['tracks']
        tracks_list = map(lambda x:[x['track_title'],x['track_id'],x['album_id'],x['album_title']], tracks)
        pprint(tracks_list)
        #i = raw_input('Enter a number :')
        #i = int(i)
        #song_url = self._get_song_url(tracks_list[i][1], tracks_list[i][2])
        #self._download_track(song_url)

    def _get_url_contents(self, url):
        url = url.replace(' ','%20')
        print url
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

if __name__ == '__main__':
    import sys
    query = sys.argv[1]
    d = GaanaDownloader()
    #d.get_search_artist(query)
    #d.get_search_song(query, 'temp')
    #d.get_search_album(query)
    d.search_albums(query)
