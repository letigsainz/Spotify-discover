import os
from flask import Flask, redirect, request, url_for, session
from dotenv import load_dotenv
import requests
import base64
import json

load_dotenv() # load environment variables

# client info
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI') # URI to redirect to after granting user permission

# spotify API endpoints
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
ME_URL = 'https://api.spotify.com/v1/me'
TOP_ARTISTS_URL = 'https://api.spotify.com/v1/me/top/artists'
MY_FOLLOWED_ARTISTS_URL = 'https://api.spotify.com/v1/me/following?type=artist'
GET_ALL_ARTIST_ALBUMS_URL = 'https://api.spotify.com/v1/artists/{id}/albums'
GET_ALBUM_URL = 'https://api.spotify.com/v1/albums/{id}'

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

@app.route('/')
def request_auth():
    # Auth flow step 1 - request authorization
    scope = 'user-top-read playlist-modify-public user-follow-read'
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


# Create a playlist of new releases
@app.route('/create_playlist/')
def create_playlist():
    tokens = get_tokens()
    # if tokens['expires_in'] < 60:
    #     redirect('/refresh')
    pass


# Get user's top artists
@app.route('/get_artists')
def get_artists():
    tokens = get_tokens()

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
@app.route('/get_albums/')
def get_albums():
    tokens = get_tokens()
    album_ids = []
    artist_ids = session['artist_ids']

    print(f'Artist Ids: {artist_ids}')
    debug_response = {}
    # get albums for each artist
    for id in artist_ids:
        uri = f'https://api.spotify.com/v1/artists/{id}/albums'
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
        r = requests.get(uri, headers=headers)
        response = r.json()
        debug_response[id] = response
        # get each album's id
        # albums = response['items']
        # for album in albums:
        #     album_ids.append(album['id'])

    # print('Album ids received!')
    return debug_response


# Get each individual album's release date and tracks
@app.route('/get_albums/album')
def get_album():
    pass


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
    store_tokens(response)

    return 'tokens refreshed!'
    # return redirect('/create_playlist')

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


if __name__ == '__main__':
   app.run(host='0.0.0.0')
