import os
from flask import Flask, redirect, request
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
GET_ARTIST_ALBUMS_URL = 'https://api.spotify.com/v1/artists/{id}/albums'

app = Flask(__name__)

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
    # print(response)
    # for key, value in response.items():
    #     print(key, ':', value)

    # store tokens
    store_tokens(response)
    print('Successfully completed auth flow!')

    return redirect('/create_playlist')


@app.route('/create_playlist')
def create_playlist():
    tokens = get_tokens()
    # if tokens['expires_in'] < 60:
    #     redirect('/refresh')

    # request to get user's top artists
    uri = TOP_ARTISTS_URL
    headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
    r = requests.get(uri, headers=headers)

    # set up to get artist ID's
    response = r.json()
    artists = response['items']
    artist_ids = []

    for artist in artists:
        artist_ids.append(artist['id'])

    print(artist_ids)


    return r.json()


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
