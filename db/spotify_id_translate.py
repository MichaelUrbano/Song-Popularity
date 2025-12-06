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
    try:
        token = requests.post(url, headers=headers, data=data, timeout=30)
        return token.json()["access_token"]
    except requests.RequestException:
        print("Could not create access token")
        return None

def get_tracks(cid, secret, token, track_uris, con, cur):
    """Will translate URIs into readable tracknames"""
    endpoint = "https://api.spotify.com/v1/tracks"
    total_batches = (len(track_uris) + 49) // 50
    batch_counter = 0

    for i in range(0, len(track_uris), 50):
        batch = track_uris[i:i+50]
        params = {"ids": ",".join(batch)}

        while True:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(endpoint, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()["tracks"]

                for track in data:
                    if track is None:
                        continue
                    track_id = track["id"]
                    artist_id = track["artists"][0]["id"]
                    track_name = track["name"]
                    artist_name = track["artists"][0]["name"]

                    cur.execute("""
                        INSERT OR REPLACE INTO id_translations (
                            track_id,
                            artist_id,
                            track_name,
                            artist_name
                        )
                        VALUES (?, ?, ?, ?);
                    """, (track_id, artist_id, track_name, artist_name))

                con.commit()
                batch_counter += 1
                print(f"Completed batch {batch_counter}/{total_batches}")
                break

            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 30))
                print(f"Rate limited, retrying after {retry_after} seconds...")
                sleep(retry_after)
                continue

            elif response.status_code == 401:
                print("Access token expired, attempting to get a new one...")
                sleep(10)
                token = get_access_token(cid, secret)
                if not token:
                    print("Token refresh failed...")
                continue

            else:
                print("Unknown error, trying again in 30 seconds...")
                sleep(30)
                continue

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
        if not access_token:
            print("Access token creation failed.")
            return
        db_path = os.getenv("DB_PATH")
    except OSError:
        print("Could not properly parse .env file")
        return

    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
    except sqlite3.Error:
        print("Could not connect to database")
        return

    try:
        cur.execute("""
            SELECT spotify_song_id
            FROM chords
            WHERE spotify_song_id IS NOT NULL;
        """)
        rows = cur.fetchall()
        track_ids = [r[0] for r in rows]
        cur.execute("""
        CREATE TABLE IF NOT EXISTS id_translations (
            track_id TEXT PRIMARY KEY,
            artist_id TEXT NOT NULL,
            track_name TEXT NOT NULL,
            artist_name TEXT NOT NULL
        );
        """)
        con.commit()

        cur.execute("SELECT track_id FROM id_translations;")
        existing = {r[0] for r in cur.fetchall()}
        track_ids = [tid for tid in track_ids if tid not in existing]
        if not track_ids:
            print("No new tracks to process.")
            con.close()
            return
    except sqlite3.Error:
        print("Could not utilize database")
        return
    try:
        get_tracks(client_id, client_secret, access_token, track_ids, con, cur)
        con.close()
    except KeyboardInterrupt:
        con.close()

if __name__ == "__main__":
    main()
