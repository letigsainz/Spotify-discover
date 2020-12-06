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
def request_access():
    SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
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
    return r.text

if __name__ == '__main__':
   app.run(host='0.0.0.0')
