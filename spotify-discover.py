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


app = Flask(__name__)

@app.route('/')
def request_auth():
    # Auth flow step 1 - request authorization
    return redirect(f'https://accounts.spotify.com/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}')

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
    print(response)
    for key, value in response.items():
        print(key, ':', value)

    # store tokens
    tokens = {
        'access_token': response['access_token'],
        'refresh_token': response['refresh_token']
    }
    with open('tokens.json', 'w') as outfile:
        json.dump(tokens, outfile)

    return 'Successfully completed auth flow!'


@app.route('/refresh')
def refresh_tokens():
    # get refresh token from json file
    with open('tokens.json', 'r') as openfile:
        tokens = json.load(openfile)

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
    tokens = {
        'access_token': response['access_token'],
        'refresh_token': response['refresh_token']
    }
    with open('tokens.json', 'w') as outfile:
        json.dump(tokens, outfile)

    return 'tokens refreshed!'

if __name__ == '__main__':
   app.run(host='0.0.0.0')
