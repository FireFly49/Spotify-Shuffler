import os
from secret import client_id, client_secret, secret_key

from flask import Flask, session, redirect, url_for, request, render_template

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
from random import randint      


app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
redirect_uri = 'http://localhost:5000/callback'
scope = 'playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public'

cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id = client_id,
    client_secret= client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
) 

sp = Spotify(auth_manager=sp_oauth)

@app.route('/')
def home():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('get_playlists')) 

@app.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('get_playlists'))


@app.route('/get_playlists')

def get_playlists():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)

    playlists = sp.current_user_playlists()
    playlists_info = [(pl['name'], pl['external_urls']['spotify']) for pl in playlists['items']]
    return render_template('index.html', playlists=playlists_info)

@app.route('/process_playlist', methods=['POST'])
def process_playlist():
    #bunch the calls up 
    tracks = []
    id = request.form['playlist_id']
    offset = 0
    while True:
        response = sp.playlist_tracks(playlist_id=id, offset=offset, limit=100)
        tracks.extend(response['items'])
        if len(tracks) >= response['total']:
            break
        offset += 100

    # Bulk shuffle of tracks locally, reducing api calls
    track_ids = [track['track']['id'] for track in tracks]
    total_tracks = len(track_ids)
    for i in range(total_tracks - 1, 0, -1):
        j = randint(0,i)
        track_ids[i], track_ids[j] = track_ids[j], track_ids[i]
    
    sp.playlist_replace_items(id, track_ids)

    return redirect(url_for('get_playlists'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)