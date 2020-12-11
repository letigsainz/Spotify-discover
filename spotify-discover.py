from flask import Flask, redirect, request, session
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
import helpers as hp
import numpy as np
import requests
import base64
import json
import os

load_dotenv() # load environment variables

# client info
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI') # URI to redirect to after granting user permission
USER_ID = os.getenv('SPOTIFY_USER_ID')

# spotify API endpoints
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
ME_URL = 'https://api.spotify.com/v1/me'
MY_FOLLOWED_ARTISTS_URL = 'https://api.spotify.com/v1/me/following?type=artist'

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

hp.open_browser() # open browser automatically


@app.route('/')
def request_auth():
    # Auth flow step 1 - request authorization
    scope = 'user-top-read playlist-modify-public playlist-modify-private user-follow-read'
    return redirect(f'https://accounts.spotify.com/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={scope}')


@app.route('/callback')
def request_tokens():
    # get code from spotify req param
    code = request.args.get('code')

    # necessary request body params
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    # Auth flow step 2 - request refresh and access tokens
    r = requests.post(SPOTIFY_TOKEN_URL, data=payload)
    response = r.json() # parse json

    # store tokens
    hp.store_tokens(response)
    print(f'{r.status_code} - Successfully completed Auth flow!')

    return redirect('/get_artists')


# Get user's followed artists
@app.route('/get_artists')
def get_artists():
    tokens = hp.get_tokens()
    if tokens['expires_in'] < 100:
        redirect('/refresh')

    # Make request to get followed artists endpoint
    uri = MY_FOLLOWED_ARTISTS_URL
    headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
    r = requests.get(uri, headers=headers)
    response = r.json()

    # Get artist ID's setup
    artist_ids = []
    artists = response['artists']['items']

    for artist in artists:
        artist_ids.append(artist['id'])

    # While next results page exists, get it and its artist_ids
    while response['artists']['next']:
        next_page_uri = response['artists']['next']
        r = requests.get(next_page_uri, headers=headers)
        response = r.json()
        for artist in response['artists']['items']:
            artist_ids.append(artist['id'])

    print('Retrieved artist IDs!')
    session['artist_ids'] = artist_ids

    return redirect('/get_albums')


# Get all albums for each followed artist (albums, singles)
@app.route('/get_albums')
def get_albums():
    tokens = hp.get_tokens()
    artist_ids = session['artist_ids']
    album_ids = []
    album_names = {} # used to check for duplicates with different id's * issue with some albums

    # set time frame for new releases (4 weeks)
    today = datetime.now()
    two_weeks = timedelta(weeks=4)
    time_frame = (today - two_weeks).date()

    # get albums for each artist
    for id in artist_ids:
        uri = f'https://api.spotify.com/v1/artists/{id}/albums?include_groups=album,single&country=US'
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
        r = requests.get(uri, headers=headers)
        response = r.json()

        # get each album's id
        albums = response['items']
        for album in albums:
            # check for tracks that are new releases (4 weeks)
            try:
                release_date = datetime.strptime(album['release_date'], '%Y-%m-%d') # convert release_date string to datetime
                album_name = album['name']
                artist_name = album['artists'][0]['name']
                if release_date.date() > time_frame:
                    # if we do find a duplicate album name, check if it's by a different artist
                    if album_name not in album_names or artist_name != album_names[album_name]:
                        album_ids.append(album['id'])
                        album_names[album_name] = artist_name
            except ValueError:
                # there appear to be some older release dates that only contain year (2007) - irrelevant
                print(f'Release date found with format: {album["release_date"]}')

    session['album_ids'] = album_ids
    print('Retrieved album IDs!')
    return redirect('/get_tracks')


# Get each individual "album's" track uri's
@app.route('/get_tracks')
def get_tracks():
    tokens = hp.get_tokens()
    album_ids = session['album_ids']

    # debug_response = {}
    track_uris = []

    # get tracks for each album
    for id in album_ids:
        uri = f'https://api.spotify.com/v1/albums/{id}/tracks'
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
        r = requests.get(uri, headers=headers)
        response = r.json()
        # debug_response[id] = response

        for album in response['items']:
            track_uris.append(album['uri'])

    hp.store_track_uris(track_uris)
    print('Retrieved tracks!')

    # return debug_response
    return redirect('/create_playlist')


# Create a new playlist in user account
@app.route('/create_playlist')
def create_playlist():
    tokens = hp.get_tokens()
    current_date = (date.today()).strftime('%m-%d-%Y')
    playlist_name = f'New Monthly Releases - {current_date}'

    # make request to create_playlist endpoint
    uri = f'https://api.spotify.com/v1/users/{USER_ID}/playlists'
    headers = {'Authorization': f'Bearer {tokens["access_token"]}', 'Content-Type': 'application/json'}
    payload = {'name': playlist_name}
    r = requests.post(uri, headers=headers, data=json.dumps(payload))
    response = r.json()

    session['playlist_id'] = response['id'] # store our new playlist's id
    session['playlist_url'] = response['external_urls']['spotify'] # store new playlist's url

    print(f'{r.status_code} - Created playlist!')
    return redirect('/add_to_playlist')


# Add new music releases to our newly created playlist
@app.route('/add_to_playlist')
def add_to_playlist():
    tokens = hp.get_tokens()
    playlist_id = session['playlist_id']

    # get track_uris dict
    track_uris = hp.get_track_uris()

    # split up the request if number of tracks is too big. Spotify API max 100 per req.
    tracks_list = track_uris['uris']
    number_of_tracks = len(tracks_list)

    # split track_uris list into 3 sub lists
    if number_of_tracks > 200:
        three_split = np.array_split(tracks_list, 3)
        # post request to add new releases to playlist
        for lst in three_split:
            uri = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
            headers = {'Authorization': f'Bearer {tokens["access_token"]}', 'Content-Type': 'application/json'}
            payload = {'uris': list(lst)} # convert ndarray to list
            r = requests.post(uri, headers=headers, data=json.dumps(payload))
            response = r.json()

    # split track_uris list into 2 sub lists
    elif number_of_tracks > 100:
        two_split = np.array_split(tracks_list, 2)
        # post request to add new releases to playlist
        for lst in two_split:
            uri = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
            headers = {'Authorization': f'Bearer {tokens["access_token"]}', 'Content-Type': 'application/json'}
            payload = {'uris': list(lst)} # convert ndarray to list
            r = requests.post(uri, headers=headers, data=json.dumps(payload))
            response = r.json()

    else:
        uri = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        headers = {'Authorization': f'Bearer {tokens["access_token"]}', 'Content-Type': 'application/json'}
        payload = {'uris': tracks_list}
        r = requests.post(uri, headers=headers, data=json.dumps(payload))
        response = r.json()

    print('Added tracks to playlist!')

    # redirect to playlsit page & shut down flask server
    hp.shutdown_server(request.environ)
    return redirect(session['playlist_url'])


# Refresh access token near expiration
@app.route('/refresh')
def refresh_tokens():
    # get refresh token from json file
    tokens = hp.get_tokens()

    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': tokens['refresh_token']
    }
    base64encoded = str(base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode('ascii')), 'ascii')
    headers = {'Authorization': f'Basic {base64encoded}'}

    # post request for new tokens
    r = requests.post(SPOTIFY_TOKEN_URL, data=payload, headers=headers)

    # rewrite tokens file with new tokens
    response = r.json()
    hp.refresh_tokens(response['access_token'], tokens['refresh_token'], response['expires_in'])

    print('Tokens refreshed!')
    return redirect('/get_artists')


if __name__ == '__main__':
   app.run(host='0.0.0.0')
