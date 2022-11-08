#!/usr/bin/env python3
from flask import Flask, request, redirect

import json
import requests

# VARS
scopes = [
    "playlist-read-private", 
    "playlist-read-collaborative", 
    "playlist-modify-private", 
    "playlist-modify-public"
]

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
print(f"cid: {secrets['client_id']}, cs: {secrets['client_secret']}")


# with open('response.html', 'w') as f:
#     f.write(r.text)
# print(r.text)

# def default_route():
#     return "Spotify Shuffle"

@app.route('/')
@app.route('/login/')
def login():
    print("Logging in...")
    auth_uri = "https://accounts.spotify.com/authorize"
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
    return code

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)