#!/usr/bin/python3
"""Translates URIs from a database into human-readable names"""
import os
import base64
import sqlite3
from time import sleep
import requests
from dotenv import load_dotenv

def get_access_token(cid, secret):
    """Will get an access token, based on Client Credential Flow"""
    try:
        url = "https://accounts.spotify.com/api/token"
        auth_string = f"{cid}:{secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_base64}"
            }
        data = {
            "grant_type": "client_credentials"
        }
        token = requests.post(url, headers=headers, data=data, timeout=30)
        return token.json()["access_token"]
    except requests.ConnectionError:
        print("Could not create access token")

def get_tracks(cid, secret, token, track_uris):
    """Will translate URIs into readable tracknames"""
    results = []
    endpoint = "https://api.spotify.com/v1/tracks"
    headers = {"Authorization": f"Bearer {token}"}
    for i in range(0, len(track_uris), 50):
        batch = track_uris[i:i+50]
        params = {"ids": ",".join(batch)}
        response = requests.get(endpoint, headers=headers, params=params, timeout=30)

        match response.status_code:
            case 200:
                data = response.json()["tracks"]
                results.extend(data)
            case 429:
                while response.status_code == 429:
                    sleep(30)
                    response = requests.get(endpoint, headers=headers, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()["tracks"]
                    results.extend(data)
                elif response.status_code == 401:
                    print("Expired Token, trying to reauthenticate...")
                    token = get_access_token(cid, secret)
                    response = requests.get(endpoint, headers=headers, params=params, timeout=30)
                    data = response.json()["tracks"]
                    results.extend(data)
                else:
                    raise requests.RequestException
            case 401:
                print("Expired Token, trying to reauthenticate...")
                token = get_access_token(cid, secret)
                response = requests.get(endpoint, headers=headers, params=params, timeout=30)
                data = response.json()["tracks"]
                results.extend(data)
            case _:
                raise requests.RequestException

    return results

def main():
    """Will load environment variables to use the API, and retrieve track names"""
    try:
        load_dotenv()
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        if "ACCESS_TOKEN" not in os.environ:
            access_token = get_access_token(client_id, client_secret)
        else:
            access_token = os.getenv("ACCESS_TOKEN")
        db_path = os.getenv("DB_PATH")
    except OSError:
        print("Could not properly parse .env file")

    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except sqlite3.Error:
        print("Could not connect to database")

    try:
        cur.execute("""
        SELECT
            chords.spotify_song_id AS track_id,
            chords.spotify_artist_id AS artist_id
        FROM chords
        WHERE 
            track_id IS NOT NULL
            AND artist_id IS NOT NULL
        LIMIT 50;
        """)
        rows = cur.fetchall()
        track_ids = [r[0] for r in rows]
        artist_ids = [r[1] for r in rows]
    except sqlite3.Error:
        print("Could not query database")
    print(get_tracks(client_id, client_secret, access_token, track_ids))

if __name__ == "__main__":
    main()
