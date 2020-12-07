import os
from flask import Flask, redirect, request
from dotenv import load_dotenv
import requests

load_dotenv() # load environment variables
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI') # URI to redirect to after granting user permission

app = Flask(__name__)

@app.route('/')
def request_auth():
    # Auth flow step 1 - request authorization
    return redirect(f'https://accounts.spotify.com/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}')

@app.route('/callback')
def request_tokens():
    # get code from spotify req param
    code = request.args.get('code')
    SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'

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
    access_token = response['access_token']
    refresh_token = response['refresh_token']

    return 'Successfully completed auth flow!'


if __name__ == '__main__':
   app.run(host='0.0.0.0')
