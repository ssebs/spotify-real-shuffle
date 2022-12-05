#!/usr/bin/env python3
from flask import Flask, request, redirect, session, render_template

import traceback
import json
import os
import requests
import base64
import random
from datetime import datetime
import math
import webbrowser

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
backup_path = "./backups/"
access_token = None
header = None

# Start processing
app = Flask(__name__)
app.secret_key = datetime.now().isoformat()
app.config["SESSION_COOKIE_HTTPONLY"] = False
# print("Spotify Shuffle")
# print(f"cid: {secrets['client_id']}, cs: {secrets['client_secret']}")

if not os.environ.get("WERKZEUG_RUN_MAIN"):
    webbrowser.open("http://127.0.0.1:8080", new=0, autoraise=True)


@app.route('/home/')
def home_rt():
    # TODO: make this a wrapper func
    if "secrets" not in session:
        load_secrets()
    if "header" in session:
        header = session["header"]

        playlists = get_playlists(header)
        with open(backup_path+"playlists.json", "w") as f:
            f.write(json.dumps(playlists, indent=2))

        return render_template("home.html", playlists=playlists)
    else:
        if session == {}:
            return redirect("/login")
        return render_template('error.html', error=json.dumps(session, indent=2))


@app.route('/login/')
def login_rt():
    if "secrets" not in session:
        return redirect("/setup")

    # Handle login pt 1 (will move on to /callback/)
    print("Logging in...")
    r = requests.get(auth_uri, params={
        "response_type": "code",
        "client_id": session["secrets"]['client_id'],
        "scope": " ".join(scopes),
        "redirect_uri": "http://127.0.0.1:8080/callback"
    })
    return redirect(r.url)


@app.route("/callback/")
def callback_rt():
    # Handle login pt 2
    if "error" in request.args:
        return render_template('error.html', error=request.args["error"])

    secret = session["secrets"]['client_id'] + ":" + session["secrets"]["client_secret"]
    auth_encoded = base64.b64encode(secret.encode(("ascii"))).decode("ascii")
    # Get access token
    r = requests.post(token_uri, data={
        "grant_type": "authorization_code",
        "code": request.args['code'],
        "redirect_uri": "http://127.0.0.1:8080/callback"
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
    with open(backup_path+'playlists.json', 'r') as f:
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
            with open(f"{backup_path}{cleaned_name}-tracks-backup.json", "w") as f:
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
            shuffled_del = [{"uri": track_uris[i]} for i in idx_list]
            shuffled_str = [track_uris_str[i] for i in idx_list]
            # print(shuffled)
            obj = {
                "Original": track_uris_str,
                "Shuffled": shuffled_str
            }

            # Update playlist
            resp = update_playlist_items(
                shuffled, shuffled_del, _playlist["id"], header)

            if "status" in resp and resp["status"] == "OK":
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


@app.route('/')
@app.route("/setup/", methods=["GET", "POST"])
def setup_rt():
    # Don't do setup if we already have the header configured
    if "header" in session:
        load_secrets()
        return redirect("/home")
    
    # User fills out form for client id and secret, POST's it back here to save as a file
    if request.method == 'POST':
        # Save credentials, then redirect to login
        try:
            if "client_id" in request.form and "client_secret" in request.form:
                _id = request.form.get("client_id")
                _secret = request.form.get("client_secret")

                with open("secrets.json", "w") as f:
                    f.write(json.dumps({
                        "client_id": _id,
                        "client_secret": _secret
                    }))
                load_secrets()
                print("secrets")
                print(session["secrets"])
                return redirect("/login")
            else:
                msg = "The client_id or client_secret field is missing. If you submitted the form, report this bug. "
                return render_template('error.html', error=msg)
        except Exception as e:
            return render_template('error.html', error=json.dumps(e, indent=2))
    else:
        # Will turn into the POST request expected above
        return render_template("setup.html")
        # Render site


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


def update_playlist_items(uris: list, uris_del: list, playlist_id: str, header: dict):
    if header is None:
        print("vars not set")
        return False
    try:
        # print("uris")
        # print(json.dumps(uris, indent=2))

        # API has a limit of 100 items, so lets loop as many times divided by ceil(multiple)
        # Remove old songs first, then add new ones
        multiple = 100
        temp_ret = {"deleted": [], "added": []}

        # Remove items
        # print("Deleting tracks")
        for idx, uri in enumerate(range(math.ceil(len(uris_del) / multiple)), start=1):
            if uri is None:
                break
            data = {
                "tracks": uris_del[(idx - 1) * multiple: idx * multiple],
            }
            try:
                r = requests.delete(api_base_uri+"/playlists/"+playlist_id+"/tracks",
                                    json=data, headers=header)
                if "error" in r.json():
                    return r.json()
            except Exception as e:
                print(e)
                return r.text
            temp_ret["resp-del"] = r.json()
            temp_ret["deleted"].append(data)
        # print("Delete complete")

        # Add items
        # print("Adding tracks")
        for idx, uri in enumerate(range(math.ceil(len(uris) / multiple)), start=1):
            if uri is None:
                break
            data = {
                "uris": uris[(idx - 1) * multiple: idx * multiple],
            }
            try:
                r = requests.post(api_base_uri+"/playlists/"+playlist_id+"/tracks",
                                  json=data, headers=header)
                if "error" in r.json():
                    return r.json()
            except Exception as e:
                print(e)
                return r.text
            temp_ret["resp-add"] = r.json()
            temp_ret["added"].append(data)
        # print("Adds complete")

        # Check status of update
        if "resp-del" in temp_ret and "snapshot_id" in temp_ret["resp-del"]:
            # Deletion succeeded
            if "resp-add" in temp_ret and "snapshot_id" in temp_ret["resp-add"]:
                # Adding back succeeded
                temp_ret["status"] = "OK"
            else:
                temp_ret["status"] = "DEL OK, ADD FAIL"
        else:
            temp_ret["status"] = "DEL FAIL, ADD UNKNOWN"

        return temp_ret
    except Exception as e:
        print(e)
        return {"Error": e, "Request": r.text}


def load_secrets():
    try:
        with open('secrets.json', 'r') as f:
            session["secrets"] = json.loads(f.read())
        if not os.path.exists(backup_path):
            os.mkdir(backup_path)
    except Exception as e:
        print(e)
        print("You must create a secrets.json file. See https://github.com/ssebs/spotify-real-shuffle/")
        return render_template("setup.html")

# Main func
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
