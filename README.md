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
- [ ] GUI?

## Installation
- git clone this repo
- Linux/Mac
    - `$ python -m venv venv`
    - `$ source ./venv/bin/activate` 
    - `(venv) $ pip install -r requirements.txt`
- Windows
    - `PS> python.exe -m venv venv`
    - `PS> .\venv\Scripts\Activate.ps1`
        > If you get an execution policy warning, open PowerShell as an administrator and run `Set-ExecutionPolicy RemoteSigned`
    - `(venv) PS> pip install -r requirements.txt`
- Create a `secrets.json` file with your spotify dev api
    - Should look like this:
    - ```json
        {
            "client_id": "<somehashvalue>",
            "client_secret": "<somehashvalue>"
        }
      ```
- 
## Usage
- `$ python spotify-shuffle.py`
- Open a web browser to http://127.0.0.1:8080 
    - Login
    - Select playlists to update
        > Note: You must be the playlist owner
