'''
This is a program to access spotify and create a youtube play list based on a song or premade playlist
in spotify so that Rythm bot can play the playlists made in spotify

This technique will then be used to create a discord bot that accesses spotify and can access playlists from that

Process:
Step 1 - Open spotify
Step 2 - Access Playlists and/or songs desired by using name of song/playlists and name of artist/playlist user
Step 3 - Get name of song and artists of the song and/or songs in the playlist of use the name and song found in
         step 3
Step 4 - Open youtube
Step 5 - Find song or songs
Step 6 - Add song to playlists, if new playlists ask for name or use the first song to give the playlists a name
         and make it public. Else add song to existing playlist
Step 7 - Logout of both spotify and Youtube
'''
import base64

import requests
import os
from secrets import spotify_user_id, spotify_token, youtube_client_id, youtube_client_secret
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

class YouTubify:

    def _init_(self):
        self.spotify_user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.youtube_client_id = youtube_client_id
        self.youtube_client_secret = youtube_client_secret

    def get_youtube_client(self):
        """ Log Into Youtube, Copied from Youtube Data API """
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "youtube_requirements.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    def addSongToPlaylist(self):
        # get list of youtube video ids
        youtube_video_id = self.search_youtube()

        request_add = self.addPlaylist()
        request_add.execute()

        # find user playlist with list my playlists
        request = self.get_youtube_client().playlists().list(
            part="snippet,contentDetails",
            maxResults=25,
            mine=True
        )

        response = request.execute()
        print(response)

        # access playlist
        playlist_id = response["items"][0]["id"]

        print(playlist_id)

        insert_video_client = self.get_youtube_client()

        # loop through video id list to get the youtube videos that will be add to the playlist
        while youtube_video_id:
            request_2 = insert_video_client.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "position": 0,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": youtube_video_id.pop(0)
                        }
                    }
                }
            )
            response_2 = request_2.execute()

            print(response_2)

    def addPlaylist(self):
        playlist_name = input("Type the name for the playlist ")
        playlist_description = input("Type a description for the playlist ")

        request = self.get_youtube_client().playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": playlist_name,
                    "description": playlist_description,
                    "tags": [
                        "sample playlist",
                        "API call"
                    ],
                    "defaultLanguage": "en"
                },
                "status": {
                    "privacyStatus": "private"
                }
            }
        )

        return request

    def search_youtube(self):
        # use song list to search for youtube videos
        spotify_list = self.findSongs()
        youtube_id_list = []

        i = 0

        youtube_client = self.get_youtube_client()

        while i < 10:
            request = youtube_client.search().list(
                part="snippet",
                maxResults=1,
                q=spotify_list.pop(0) + " " + spotify_list.pop(0)
            )
            response = request.execute()

            # retrieve song id and make list that will be used to add to playlist
            song_id = response["items"][0]["id"]["videoId"]

            # print(response)
            print(song_id)

            i = i + 1

            youtube_id_list.append(song_id)

        print(youtube_id_list)

        return youtube_id_list

    def get_Spotify_token(self):
        # use endpoint given on spotify websire
        token_url = "https://accounts.spotify.com/api/token"

        # convert client credentials to base64 for authorization header
        client_creds = f"{spotify_user_id}:{spotify_token}"
        client_token = base64.b64encode(client_creds.encode())

        # authorization header
        token_auth = {
            "Authorization": f"Basic {client_token.decode()}"
        }

        # data for POST
        token_grant = {
            "grant_type": "client_credentials"
        }

        # make POST using url, data, and header
        access_token = requests.post(token_url, data=token_grant, headers=token_auth)
        access_json = access_token.json()

        print(access_json)
        # return access token for use in findSpotifyPlaylist and findSongs
        return access_json['access_token']

    def findSpotifyPlaylist(self):
        # add in functionality for searching song or playlist
        # prompt user input for searching for a song or playlist
        print("Type in the name of the playlist. Ex: Name\n")
        playlistName = input()

        # setup a query for the song or playlist
        search_url = "https://api.spotify.com/v1/search"
        search_params = {
            "q": playlistName,
            "type": "playlist"
        }

        search_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self.get_Spotify_token())
        }

        response = requests.get(search_url, params=search_params, headers=search_headers)

        # take the info and get the id of the playlist or song to use in another function to add to playlist in yt
        response_json = response.json()
        print(response_json)
        music_id = response_json['playlists']['items'][0]['id']

        # The id necessary for finding songs(for songs we can use the name and artist field here)
        return music_id

    def findSongs(self):
        # find soptifyPlaylist
        playlist = self.findSpotifyPlaylist()

        # request.get playlist by id to get the total number of songs
        total_url = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist)
        total_parameters = {
            "fields": "total",
            "market": "US"
        }
        total_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self.get_Spotify_token())
        }

        total = requests.get(total_url, params=total_parameters, headers=total_headers)

        total_json = total.json()
        total_num_song = total_json["total"]

        counter = 0

        # create list to hold all of the song info from the playlist song_list[name][artist]
        song_list = []

        # use the total number of songs to loop through the playlist bc spotify caps it at 100
        while total_num_song != 0:
            # initial offset = 0
            offset = counter

            # check to see if there are more or less than 100 songs in the playlist as we traverse through it
            if 100 < total_num_song:
                counter = 100
            else:
                counter = total_num_song
            # counter will be the loop counter to make sure we are in bounds and will be the offset for the next
            # recursion

            # set arguments for the GET request
            song_url = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist)
            song_parameters = {
                "fields": "items(track(name,artists(name)))",
                "offset": offset,
                "market": "US"
            }
            song_headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.get_Spotify_token())
            }

            # make the request
            songs = requests.get(song_url, params=song_parameters, headers=song_headers)
            songs_json = songs.json()

            # loop with i to get all the songs which is the same number as counter
            i = 0
            while i < counter:
                song_name = songs_json["items"][i]["track"]["name"]
                song_artist = songs_json["items"][i]["track"]["artists"][0]["name"]
                song_list.append(song_name)
                song_list.append(song_artist)
                i = i + 1

            total_num_song = total_num_song - counter

        print(song_list)
        return song_list


yt = YouTubify()
yt.addSongToPlaylist()
