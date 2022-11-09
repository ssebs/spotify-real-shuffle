#!/usr/bin/env python3
from flask import Flask, request, redirect

import json
import requests
import base64
import random

# VARS
scopes = [
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-private",
    "playlist-modify-public"
]
api_base_uri = "https://api.spotify.com/v1"
auth_uri = "https://accounts.spotify.com/authorize"
token_uri = "https://accounts.spotify.com/api/token"
access_token = None
header = None
# Load secrets
secrets = {}
try:
    with open('secrets.json', 'r') as f:
        secrets = json.loads(f.read())
except Exception as e:
    print(e)
    exit(1)

# Start processing
app = Flask(__name__)
print("Spotify Shuffle")
# print(f"cid: {secrets['client_id']}, cs: {secrets['client_secret']}")


@app.route('/')
@app.route('/login/')
def login():
    print("Logging in...")
    r = requests.get(auth_uri, params={
        "response_type": "code",
        "client_id": secrets['client_id'],
        "scope": " ".join(scopes),
        "redirect_uri": "http://localhost:8080/callback"
    })
    return redirect(r.url)


@app.route("/callback/")
def callback():
    if "error" in request.args:
        return request.args["error"]

    code = request.args['code']
    secret = secrets['client_id'] + ":" + secrets["client_secret"]
    auth_encoded = base64.b64encode(secret.encode(("ascii"))).decode("ascii")
    # Get access token
    r = requests.post(token_uri, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://localhost:8080/callback"
    }, headers={
        "Authorization": f"Basic {str(auth_encoded)}",
        "Content-Type": "application/x-www-form-urlencoded"
    })

    playlists = None
    if "access_token" not in r.json():
        print("Failed to login")
        return "Failed to login"
    print("Logged in!")

    access_token = r.json()["access_token"]
    header = {"Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"}

    playlists = get_playlists(header)
    test_playlist = None

    playlist_ids = []
    for pl in playlists['items']:
        if pl["name"] == "Test Playlist":
            test_playlist = pl
            playlist_ids.append(pl["id"])
    # print(pl)
    
    tracks = get_playlist_tracks(playlist_ids[0], header)
    track_uris = []
    track_uris_str = []
    for track in tracks['items']:
        track_uris.append(track["track"]["uri"])
        track_uris_str.append(f'{track["track"]["uri"]} - {track["track"]["name"]}')
    
    # Re-order
    idx_list = list(range(len(track_uris)))
    random.shuffle(idx_list)
    shuffled = [track_uris[i] for i in idx_list]
    print(shuffled)
    obj = {
        "shuffled": shuffled,
        "original": track_uris
    }


    return f"<html><body><a href='/'>home</a><pre>{json.dumps(obj, indent=2)}</pre></body></html>"


def get_playlists(header: dict):
    if header is None:
        print("vars not set")
        return False
    r = requests.get(api_base_uri+"/me/playlists", headers=header)
    return r.json()

def get_playlist_tracks(playlist_id: str, header: dict):
    if header is None:
        print("vars not set")
        return False
    r = requests.get(api_base_uri+"/playlists/"+playlist_id+"/tracks", headers=header)
    return r.json()


# Main func
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
