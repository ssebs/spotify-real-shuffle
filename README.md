# Spotify-real-shuffle

We all know how bad Spotify's shuffle is, so this tool will shuffle up your custom order for your playlists.

## Goals
- [x] Connect to API and read playlist info
- [X] Re-arrange some songs
- [X] Shuffle a playlist and save it
- [x] Support Pagination (max 100 by default)
- [x] User can select which playlists to shuffle
- [ ] User can easily run this
- [x] Support playlists over 100 items (update func)
- [ ] Cleanup
- [x] Generate secrets.json on `/setup`
- [ ] Add error handling for incorrect secrets
    - Not possible, find a good way to present this to users
- [ ] Good error handling
- [ ] GUI?

## Prereqs
- Setup your Spotify Developer account (you'll need a regular Spotify account)
    - https://developer.spotify.com/dashboard/
    - Click **Log in** and log in with your regular Spotify account
    - Click **CREATE AN APP**
        - Enter something for the name and description, it can be whatever you want
        - Click **Create**
    - Copy the **Client ID**, you'll need this
    - Click **SHOW CLIENT SECRET**
    - Copy the **Client Secret**, you'll need this
    - Click **Edit Settings** in green
        - Under **Redirect URIs**, add: `http://127.0.0.1:8080/callback`
        - Save
- Clone this repo or download the zip
    - Clone:
        - `$ git clone https://github.com/ssebs/spotify-real-shuffle`
    - Zip:
        - Go to https://github.com/ssebs/spotify-real-shuffle
        - Click the green Code button > Download ZIP
- Create a `secrets.json` file
- Within the `spotify-real-shuffle/` directory, create a new text file called `secrets.json` with the contents below. (Replace id and secret with the ones you copied earlier)
```json
{
    "client_id": "<somehashvalue>",
    "client_secret": "<somehashvalue>"
}
```


## Installation
- Install python if not already installed (or, run the [binary release](https://github.com/ssebs/spotify-real-shuffle/releases/))
- Linux/Mac
    - `$ python -m venv venv`
    - `$ source ./venv/bin/activate` 
    - `(venv) $ pip install -r requirements.txt`
- Windows
    - `PS> python.exe -m venv venv`
    - `PS> .\venv\Scripts\Activate.ps1`
        > If you get an execution policy warning, open PowerShell as an administrator and run `Set-ExecutionPolicy RemoteSigned`
    - `(venv) PS> pip install -r requirements.txt`

## Usage
- Binary:
    - Download the spotify-shuffle.exe from the [binary release's page](https://github.com/ssebs/spotify-real-shuffle/releases/))
    - Create the `secrets.json` file as noted in the prereqs
    - Double click the exe and open a web browser to http://127.0.0.1:8080 
- From Source:
    - After setting up the venv above
    - `$ python spotify-shuffle.py`
    - Open a web browser to http://127.0.0.1:8080 
        - Login
        - Select playlists to update
            > Note: You must be the playlist owner

## Build
- `pyinstaller -c -F --add-data "templates;templates" --add-data "static;static" spotify-shuffle.py`
    - Built file is under `./dist/`
    - `secrets.json` file needs to be next to the binary

## LICENSE
[GPL V3](./LICENSE)
