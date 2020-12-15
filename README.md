# Spotify Discover

## About The Project
This flask app is meant to run locally every month and allow the user to discover new music.

It uses the Spotify Web API to access your followed artists, check if they've released any new music, and if so, add the tracks to a new playlist for that month.

## Getting Started

Make sure you have Python3 installed.

[Register](https://developer.spotify.com/documentation/general/guides/app-settings/#register-your-app) your application with ``http://127.0.0.1:5000/callback`` as the redirect URI to obtain a client ID and secret.

## Setup

Clone the repository and step inside.

Set up a .env file in the project directory that looks like this:
```
SPOTIFY_CLIENT_ID= '<your_client_id>'
SPOTIFY_CLIENT_SECRET= '<your_client_secret>'
SPOTIFY_REDIRECT_URI= 'http://127.0.0.1:5000/callback'
SPOTIFY_USER_ID= '<your_spotify_user_id>'
SECRET_KEY= '<your_secret_key>'
```
The SECRET_KEY is used by flask to keep data safe (encryption). You must set the secret key in order to use session in flask.

Create a secret key using the following command. Copy the resulting string into the SECRET_KEY variable in your .env file.
```
$ python -c 'import os; print(os.urandom(16))'

b'_5#y2L"F4Q8z\n\xec]/'
```

## How To Run

Create a virtual environment within your project directory and activate it (not required, but highly recommended)
```
python3 -m venv venv
```
```
source venv/bin/activate
```

Install required packages:
```
pip install -r requirements.txt
```

Start up the server:
```
export FLASK_APP=spotify-discover.py

python -m flask run
```
