#!/usr/bin/env python3
from flask import Flask, request, redirect, session, render_template

import traceback
import json
import requests
import base64
import random
from datetime import datetime
import math

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
    print("You must create a secrets.json file. See https://github.com/ssebs/spotify-real-shuffle/")
    exit(1)

# Start processing
app = Flask(__name__)
app.secret_key = datetime.now().isoformat()
# print("Spotify Shuffle")
# print(f"cid: {secrets['client_id']}, cs: {secrets['client_secret']}")


@app.route('/')
@app.route('/home/')
def home_rt():
    if "header" in session:
        header = session["header"]

        playlists = get_playlists(header)
        with open("playlists.json", "w") as f:
            f.write(json.dumps(playlists, indent=2))

        return render_template("home.html", playlists=playlists)
    else:
        if session == {}:
            return redirect("/login")
        return render_template('error.html', error=json.dumps(session, indent=2))


@app.route('/login/')
def login_rt():
    # Handle login pt 1 (will move on to /callback/)
    print("Logging in...")
    r = requests.get(auth_uri, params={
        "response_type": "code",
        "client_id": secrets['client_id'],
        "scope": " ".join(scopes),
        "redirect_uri": "http://localhost:8080/callback"
    })
    return redirect(r.url)


@app.route("/callback/")
def callback_rt():
    # Handle login pt 2
    if "error" in request.args:
        return request.args["error"]

    secret = secrets['client_id'] + ":" + secrets["client_secret"]
    auth_encoded = base64.b64encode(secret.encode(("ascii"))).decode("ascii")
    # Get access token
    r = requests.post(token_uri, data={
        "grant_type": "authorization_code",
        "code": request.args['code'],
        "redirect_uri": "http://localhost:8080/callback"
    }, headers={
        "Authorization": f"Basic {str(auth_encoded)}",
        "Content-Type": "application/x-www-form-urlencoded"
    })

    if "access_token" not in r.json():
        print("Failed to login")
        return "Failed to login - no access token in <pre>" + r.text + f"</pre><strong>HTTP {r.status_code}</strong>"
    print("Logged in!")

    header = {"Authorization": f"Bearer {r.json()['access_token']}",
              "Content-Type": "application/json"}
    session["header"] = header

    return redirect("/")


@app.route("/update/", methods=["POST"])
def update_rt():
    try:
        # print(request.form)
        playlist_ids = []
        for pid in request.form.values():
            playlist_ids.append(pid)
        # playlist_ids should be a comma separated list
        # e.g. 7lS8RnhxDyUGdola0ZGQJS,4WzLv9T6sZ0CvwNdknqH88
        # print(playlist_ids)
    except Exception:
        return render_template('error.html', error=traceback.format_exc())

    try:
        header = session["header"]
    except Exception:
        return redirect("/login")

    # Get current user's playlists
    playlists = []
    # This should be updated from the last time the user went to /home
    with open('playlists.json', 'r') as f:
        playlists = json.loads(f.read())

    # TODO: Move this to another function
    playlists_to_update = {}
    for pid in playlist_ids:
        playlists_to_update[pid] = {}

    # Fill playlists_to_update with the actual playlist items
    for pl in playlists:
        for _id, val in playlists_to_update.items():
            if _id == pl["id"]:
                playlists_to_update[_id] = pl
    # print(playlists_to_update)
    # return render_template('error.html', error=json.dumps(playlists_to_update, indent=2))

    ui_obj = {}
    for _playlist in playlists_to_update.values():
        try:
            # Get tracks from a playlist
            tracks = get_playlist_tracks(
                _playlist["id"], _playlist["tracks"]["total"], header)
            # return render_template('error.html', error=json.dumps(_playlist, indent=2))

            # for sanitization
            regex = r'/[^A-Za-z0-9]+/g'
            cleaned_name = _playlist["name"].replace(
                regex, '-').replace(" ", "-").lower()
            # Save a copy of the old version
            with open(f"{cleaned_name}-tracks-backup.json", "w") as f:
                f.write(json.dumps(tracks))

            track_uris = []
            track_uris_str = []
            for track in tracks:
                track_uris.append(track["track"]["uri"])
                track_uris_str.append(
                    f'{track["track"]["name"]}')

            # Re-order
            idx_list = list(range(len(track_uris)))
            random.shuffle(idx_list)
            shuffled = [track_uris[i] for i in idx_list]
            shuffled_str = [track_uris_str[i] for i in idx_list]
            # print(shuffled)
            obj = {
                "original": track_uris_str,
                "shuffled": shuffled_str
            }

            # Update playlist
            # OLD WAY
            # # https://developer.spotify.com/documentation/web-api/reference/#/operations/reorder-or-replace-playlists-tracks
            # resp = update_playlist_items(
            #     ",".join(shuffled), _playlist["id"], header)
            # NEW WAY
            resp = update_playlist_items(shuffled, _playlist["id"], header)

            if "snapshot_id" in resp:
                # Successful update, keep looping
                ui_obj[_playlist["name"]] = obj
                continue
            else:
                # Not sure what the error may be
                # return render_template('error.html', error=json.dumps(resp, indent=2))
                return render_template('error.html', error=resp)
        except Exception:
            # 500 server error
            return render_template('error.html', error=traceback.format_exc())
    # All updates complete
    return render_template('updated.html', updates=ui_obj)


def get_playlists(header: dict):
    if header is None:
        print("vars not set")
        return False
    r = requests.get(api_base_uri+"/me/playlists", headers=header)
    return r.json()["items"]


def get_playlist_tracks(playlist_id: str, tracks_total: int, header: dict):
    if header is None:
        print("vars not set")
        return False
    # print(f"tracks total: {tracks_total}")
    tracks = []
    count = 0
    limit = 100

    bad_var_name = tracks_total
    if tracks_total > limit:
        bad_var_name = (math.floor(tracks_total / limit)) + 1

    for track_num in range(bad_var_name):
        offset = limit * count
        fields = "&fields=href,items(track(name,id,uri))"
        query_params = f"?limit={limit}&offset={offset}{fields}"
        url = api_base_uri + "/playlists/" + playlist_id + "/tracks" + query_params
        r = requests.get(url, headers=header)
        # tracks.append(r.json())
        # print(r.json())
        tracks.extend(
            r.json()["items"]
        )
        count += 1
    return tracks


def update_playlist_items(uris: list, playlist_id: str, header: dict):
    if header is None:
        print("vars not set")
        return False
    try:
        print("uris")
        print(json.dumps(uris, indent=2))
        # NEW WAY
        # remove old songs first, then add new ones
        multiple = 3
        temp_ret = {"deleted": [], "added": []}
        # API has a limit of 100 items, so lets loop

        # Remove items
        # as many times divided by 100 + 1
        print("Deleting tracks")
        # idx should be # of times - 1
        # old - for idx, uri in enumerate(range((len(uris) % multiple) + 1)):
        # new
        count = 0
        for idx, uri in enumerate(range(math.ceil(len(uris) / multiple)), start=1):
            # print(f"{idx} - {uris[uri]}")
            if uris[uri] is None:
                break
            # r = requests.delete(api_base_uri+"/playlists/"+playlist_id+"/tracks",
            data = {
                "tracks": uris[count*multiple: idx*multiple],
            }
            # temp_ret["deleted"].append(data)
            # , headers=header)
            # check for err
            count += 1
        # print("deleted:")
        # print(json.dumps(temp_ret["deleted"], indent=2))

        # Add items
        # print("Adding tracks")
        count = 0
        for idx, uri in enumerate(range(math.ceil(len(uris) / multiple)), start=1):
            if uri is None:
                break
            data = {
                "uris": uris[count*multiple: idx*multiple],
            }
            r = requests.post(api_base_uri+"/playlists/"+playlist_id+"/tracks",
                              json=data, headers=header)
            temp_ret["resp"] = r.json()
            count += 1
            temp_ret["added"].append(data)
        # print("Added: ")
        # print(json.dumps(temp_ret["added"], indent=2))

        return temp_ret

        # OLD WAY
        # # See https://developer.spotify.com/documentation/web-api/reference/#/operations/reorder-or-replace-playlists-tracks
        # # TODO: Stop replaceing and instead re-order.
        # # TODO: Support more than 100 items
        # # Maybe shuffle first 100, then loop?
        # r = requests.put(api_base_uri+"/playlists/"+playlist_id+"/tracks", params={
        #     "uris": uris,
        # }, headers=header)
        # return r.json()
    except Exception as e:
        print(e)
        return {"Error": e, "Request": r.text}


# Main func
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
