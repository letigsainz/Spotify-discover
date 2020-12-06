import os
from flask import Flask, redirect
from dotenv import load_dotenv
import requests

load_dotenv() # load environment variables
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

app = Flask(__name__)

@app.route('/')
def request_auth():
    return redirect(f'https://accounts.spotify.com/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}')

@app.route('/redirect')
def request_access():
    pass


if __name__ == '__main__':
   app.run(host='0.0.0.0')
