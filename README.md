# Spotify Discover

## About The Project
This flask app is meant to run every month (or couple of weeks) and allow the user to discover new music.

It uses the Spotify Web API to access your followed artists, check if they've released any new music, and if so, add the tracks to a new playlist for that month.

## Getting Started
Set up a .env file in the project directory that looks like this:
```
SPOTIFY_CLIENT_ID='<your_client_id>'
SPOTIFY_CLIENT_SECRET='<your_client_secret>'
SPOTIFY_REDIRECT_URI='http://127.0.0.1:5000/callback'
SPOTIFY_USER_ID='<your_user_id>'
```

Create a virtual environment for the project and activate it:
```
virtualenv venv
```
```
source venv/bin/activate
```

Install required packages:
```
pip install -r requirements.txt
```
