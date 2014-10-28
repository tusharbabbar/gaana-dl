#!/usr/bin/python
import requests, re, sys, os
import argparse
from bs4 import BeautifulSoup
from terminaltables import AsciiTable

proxies = {'http':'http://192.168.1.8:8080',
            'https':'http://192.168.1.8:8080'}

class BadHTTPCodeError(Exception):
    def __init__(self, code):
        print(code)

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

    def _get_url_contents(self, url):
        url = url.replace(' ','%20')
        response = requests.get(url)
        if response.status_code == 200:
            return response
        else:
            raise BadHTTPCodeError(response.status_code)

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
        response = requests.get(url , headers = {'deviceType':'GaanaAndroidApp', 'appVersion':'V5'})
        song_url_b64 = response.json()['data']
        song_url = dec(song_url_b64)
        return song_url

    def _download_track(self, song_url, track_name, dir_name):
        if 'mp3' in song_url:
            track_name = track_name + '.mp3'
        else:
            track_name = track_name + '.mp4'
        file_path = dir_name + '/' + track_name
        print 'Downloading to', file_path
        response = self._get_url_contents(song_url)
        with open(file_path,'wb') as f:
            f.write(response.content)

    def _check_path(self, _dir):
        import os
        if not os.path.exists(_dir):
            os.system('mkdir %s'%_dir)

    def _check_input(self, ids, len_of_tracks):
        ids = map(lambda x:x.strip(),ids.split(','))
        for i in ids:
            if not i.isdigit():
                return False
            if int(i) > len_of_tracks:
                return False
        return True

    def search_songs(self, query, _dir = 'misc'):
        from pprint import pprint
        self._check_path(_dir)
        url = self.urls['search_songs_new']
        url = url.format(query = query)
        response = self._get_url_contents(url)
        tracks = response.json()['tracks']
        tracks_list = map(lambda x:[x['track_title'],x['track_id'],x['album_id'],x['album_title'], ','.join(map(lambda y:y['name'], x['artist'])), x['duration']], tracks)
        tabledata = [['S No.', 'Track Title', 'Track Artist', 'Album']]
        for idx, value in enumerate(tracks_list):
            tabledata.append([str(idx), value[0], value[4], value[3]])
        table = AsciiTable(tabledata)
        print table.table
        idx = raw_input('Which album do you wish to download? Enter S No. :')
        while not self._check_input(idx, len(tracks_list)-1):
            print 'Oops!! You made some error in entering input'
            idx = raw_input('Which album do you wish to download? Enter S No. :')
        idx = int(idx)
        song_url = self._get_song_url(tracks_list[idx][1], tracks_list[idx][2])
        self._download_track(song_url, tracks_list[idx][0].replace(' ','-'), _dir)

    def search_albums(self, query, _dir = None):
        from pprint import pprint
        url = self.urls['search_albums_new']
        url = url.format(query = query)
        response = self._get_url_contents(url)
        albums = response.json()['album']
        albums_list = map(lambda x:[x['album_id'],x['title'], x['language'], x['seokey'], x['release_date'],','.join(map(lambda y:y['name'], x.get('artists',[])[:2])) ,x['trackcount']], albums)
        tabledata = [['S No.', 'Album Title', 'Album Language', 'Release Date', 'Artists', 'Track Count']]
        for idx, value in enumerate(albums_list):
            tabledata.append([str(idx), value[1], value[2], value[4], value[5], value[6]])
        table = AsciiTable(tabledata)
        print table.table
        idx = int(raw_input('Which album do you wish to download? Enter S No. :'))
        album_details_url = self.urls['album_details']
        album_details_url = album_details_url.format(album_id = albums_list[idx][0])
        response = requests.get(album_details_url , headers = {'deviceType':'GaanaAndroidApp', 'appVersion':'V5'})
        tracks = response.json()['tracks']
        tracks_list = map(lambda x:[x['track_title'].strip(),x['track_id'],x['album_id'],x['album_title'], ','.join(map(lambda y:y['name'], x['artist'])), x['duration']], tracks)
        print 'List of tracks for ', albums_list[idx][1]
        tabledata = [['S No.', 'Track Title', 'Track Artist']]
        for idy, value in enumerate(tracks_list):
            tabledata.append([str(idy), value[0], value[4]])
        tabledata.append([str(idy+1), 'Enter this to download them all.',''])
        table = AsciiTable(tabledata)
        print table.table
        print 'Downloading tracks to %s folder'%albums_list[idx][3]
        ids = raw_input('Please enter csv of S no. to download:')
        while not self._check_input(ids, len(tracks_list)) or not ids:
            print 'Oops!! You made some error in entering input'
            ids = raw_input('Please enter csv of S no. to download:')
        if not _dir:
            _dir = albums_list[idx][3]
        self._check_path(_dir)
        ids = map(int,map(lambda x:x.strip(),ids.split(',')))
        if len(ids) == 1 and ids[0] == idy + 1:
            for item in tracks_list:
                song_url = self._get_song_url(item[1], item[2])
                self._download_track(song_url, item[0].replace(' ','-').strip(), _dir)
        else:
            for i in ids:
                item = tracks_list[i]
                song_url = self._get_song_url(item[1], item[2])
                self._download_track(song_url, item[0].replace(' ','-').strip(), _dir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--album', nargs='?', help="choose this to search albums. Space seperated query must be enclosed in quotes('')", type = str )
    parser.add_argument('-s', '--song', nargs='?', help="choose this to search songs. Space seperated query must be enclosed in quotes('')", type = str)
    parser.add_argument('-d', '--dir', nargs='?', help="can be used to specify directory to download songs to", type = str)
    args = parser.parse_args()
    d = GaanaDownloader()
    if args.album:
        if args.dir:
            d.search_albums(args.album, args.dir)
        else:
            d.search_albums(args.album)
    elif args.song:
        if args.dir:
            d.search_songs(args.song, args.dir)
        else:
            d.search_songs(args.song)
    else:
        print parser.parse_args(['--help'])
