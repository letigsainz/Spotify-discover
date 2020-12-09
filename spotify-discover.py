import os
from flask import Flask, redirect, request, url_for, session
from dotenv import load_dotenv
import requests
import base64
import json
from datetime import datetime, timedelta, date
import numpy as np

load_dotenv() # load environment variables

# client info
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI') # URI to redirect to after granting user permission
USER_ID = os.getenv('SPOTIFY_USER_ID')

# spotify API endpoints
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
ME_URL = 'https://api.spotify.com/v1/me'
TOP_ARTISTS_URL = 'https://api.spotify.com/v1/me/top/artists'
MY_FOLLOWED_ARTISTS_URL = 'https://api.spotify.com/v1/me/following?type=artists'

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

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
    # parse json
    response = r.json()

    # store tokens
    store_tokens(response)
    print('Successfully completed auth flow!')

    return redirect('/get_artists')


# Get user's top artists
@app.route('/get_artists')
def get_artists():
    tokens = get_tokens()
    if tokens['expires_in'] < 100:
        redirect('/refresh')

    uri = TOP_ARTISTS_URL
    headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
    r = requests.get(uri, headers=headers)

    # set up to get artist ID's
    response = r.json()
    artists = response['items']
    artist_ids = []

    for artist in artists:
        artist_ids.append(artist['id'])
    # print(artist_ids)

    session['artist_ids'] = artist_ids
    return redirect('/get_albums')


# Get all albums for each of our top artists (albums, singles, compilations)
@app.route('/get_albums')
def get_albums():
    tokens = get_tokens()
    artist_ids = session['artist_ids']
    album_ids = []

    # set time frame for new releases (4 weeks)
    today = datetime.now()
    two_weeks = timedelta(weeks=4)
    time_frame = (today - two_weeks).date()
    # print(time_frame)

    # debug_response = {}
    # get albums for each artist
    for id in artist_ids:
        uri = f'https://api.spotify.com/v1/artists/{id}/albums?include_groups=album,single&country=US'
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
        r = requests.get(uri, headers=headers)
        response = r.json()
        # debug_response[id] = response
        # get each album's id
        albums = response['items']
        for album in albums:
            # check for tracks that are new releases (4 weeks)
            try:
                release_date = datetime.strptime(album['release_date'], '%Y-%m-%d') # convert release_date string to datetime
                if release_date.date() > time_frame:
                    album_ids.append(album['id'])
                    # print(release_date)
            except ValueError:
                # there appear to be some older release dates that only contain year (2007) - irrelevant
                print(f'Release date found with format: {album["release_date"]}')


    print('Album ids received!')
    # print(len(album_ids))
    # print(album_ids)
    # return debug_response
    session['album_ids'] = album_ids
    return redirect('/get_tracks')


# Get each individual "album's" track uri's
@app.route('/get_tracks')
def get_tracks():
    tokens = get_tokens()
    album_ids = session['album_ids']
    # print(album_ids)

    # debug_response = {}
    track_uris = []
    for id in album_ids:
        uri = f'https://api.spotify.com/v1/albums/{id}/tracks'
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
        r = requests.get(uri, headers=headers)
        response = r.json()
        # debug_response[id] = response

        for album in response['items']:
            track_uris.append(album['uri'])

    store_track_uris(track_uris)
    print(len(track_uris))

    # return debug_response
    return redirect('/create_playlist')


# Create a new playlist in your user account
@app.route('/create_playlist')
def create_playlist():
    tokens = get_tokens()
    # if tokens['expires_in'] < 60:
    #     redirect('/refresh')
    playlist_name = (date.today()).strftime('%m-%d-%Y')

    uri = f'https://api.spotify.com/v1/users/{USER_ID}/playlists'
    headers = {'Authorization': f'Bearer {tokens["access_token"]}', 'Content-Type': 'application/json'}
    payload = {'name': playlist_name}
    r = requests.post(uri, headers=headers, data=json.dumps(payload))
    response = r.json()
    print(r.status_code)
    print(response)

    session['playlist_id'] = response['id'] # store new playlist's id

    # return response
    return redirect('/add_to_playlist')

# Add new releases to your newly created playlist
@app.route('/add_to_playlist')
def add_to_playlist():
    tokens = get_tokens()
    playlist_id = session['playlist_id']

    # create a JSON array of track URI's to be passed in the requests (100 max at a time)
    track_uris = get_track_uris()
    # print(track_uris)

    # split up the request if number of tracks is too big, Spotify API max 100
    tracks_list = track_uris['uris']
    number_of_tracks = len(tracks_list)
    print(number_of_tracks)

    if number_of_tracks > 200:
        # split track_uris list into 3 sub lists
        three_split = np.array_split(tracks_list, 3)
        # post request to add new releases to playlist
        for lst in three_split:
            uri = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
            headers = {'Authorization': f'Bearer {tokens["access_token"]}', 'Content-Type': 'application/json'}
            payload = {'uris': list(lst)} # convert ndarray to list
            r = requests.post(uri, headers=headers, data=json.dumps(payload))
            response = r.json()
            # print(lst)

    elif number_of_tracks > 100:
        # split track_uris list into 2 sub lists
        two_split = np.array_split(tracks_list, 2)
        # post request to add new releases to playlist
        for lst in three_split:
            uri = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
            headers = {'Authorization': f'Bearer {tokens["access_token"]}', 'Content-Type': 'application/json'}
            payload = {'uris': list(lst)} # convert ndarray to list
            r = requests.post(uri, headers=headers, data=json.dumps(payload))
            response = r.json()
            # print(lst)

    else:
        uri = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        headers = {'Authorization': f'Bearer {tokens["access_token"]}', 'Content-Type': 'application/json'}
        payload = {'uris': tracks_list}
        r = requests.post(uri, headers=headers, data=json.dumps(payload))
        response = r.json()
        # print(tracks_list)

    print(r.status_code)
    print('added to playlist!')
    return response


@app.route('/refresh')
def refresh_tokens():
    # get refresh token from json file
    tokens = get_tokens()

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
    refresh_tokens(response['access_token'], tokens['refresh_token'], response['expires_in'])

    print('Tokens refreshed!')
    # return 'tokens refreshed!'
    return redirect('/get_artists')

# get access/refresh tokens
def get_tokens():
    with open('tokens.json', 'r') as openfile:
        tokens = json.load(openfile)
    return tokens

# store access/refresh tokens
def store_tokens(response_data):
    tokens = {
        'access_token': response_data['access_token'],
        'refresh_token': response_data['refresh_token'],
        'expires_in': response_data['expires_in']
    }
    with open('tokens.json', 'w') as outfile:
        json.dump(tokens, outfile)

# refresh tokens
def refresh_tokens(access_token, refresh_token, expires_in):
    tokens = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': expires_in
    }
    with open('tokens.json', 'w') as outfile:
        json.dump(tokens, outfile)

# store track_uris from get_tracks() in a dictionary - need
def store_track_uris(track_uris):
    uri_dict = {'uris': track_uris}
    with open('track_uris.json', 'w') as outfile:
        json.dump(uri_dict, outfile)

# retrieve track_uris
def get_track_uris():
    with open('track_uris.json', 'r') as openfile:
        uri_dict = json.load(openfile)
    return uri_dict

# check for token expiration
# def is_token_expired(tokens):
#     if tokens['expires_in'] < 50:
#         redirect('/refresh')
#     return False


if __name__ == '__main__':
   app.run(host='0.0.0.0')
