from flask import redirect
import json
# Helper functions for spotify-discover

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

# Shut down the flask server
def shutdown_server(environ):
    # look for dev server shutdown function in request environment
    if not 'werkzeug.server.shutdown' in environ:
        raise RuntimeError('Not running the development server')
    environ['werkzeug.server.shutdown']() # call the shutdown function
    print('Shutting down server...')
