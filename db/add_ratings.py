import csv
import sqlite3

con = sqlite3.connect("/home/heinz/Documents/School/SUU/School/Machine Learning/MusicRatings/SongPop.db")
cur = con.cursor()

print("Removing previous table")
cur.execute("DROP TABLE IF EXISTS ratings")
con.commit()
print("Creating new table")
cur.execute('''CREATE TABLE "ratings" (
	"song_name"	TEXT,
	"song_popularity"	INTEGER,
	"song_duration_ms"	INTEGER,
	"acousticness"	REAL,
	"danceability"	REAL,
	"energy"	REAL,
	"instrumentalness"	REAL,
	"key"	INTEGER,
	"liveness"	REAL,
	"loudness"	REAL,
	"audio_mode"	INTEGER,
	"speechiness"	REAL,
	"tempo"	REAL,
	"time_signature"	INTEGER,
	"audio_valence"	REAL
);''')
con.commit()

print("Retrieving data")
data = []
file_name = "/home/heinz/Documents/School/SUU/School/Machine Learning/MusicRatings/song_ratings_data.csv"
with open(file_name, newline='') as csvfile:
    spamreader = csv.reader(csvfile)
    for row in spamreader:
        # print('\t'.join(row))
        # insert into the rows database the records
        data.append({"song_name":           row[0],
                    "song_popularity":      row[1],
                    "song_duration_ms":     row[2],
                    "acousticness":         row[3],
                    "danceability":         row[4],
                    "energy":               row[5],
                    "instrumentalness":     row[6],
                    "key":                  row[7],
                    "liveness":             row[8],
                    "loudness":             row[9],
                    "audio_mode":           row[10],
                    "speechiness":          row[11],
                    "tempo":                row[12],
                    "time_signature":       row[13],
                    "audio_valence":        row[14]})

data.pop(0)  # remove the first line
# print(data[0:5])
# exit()

data = tuple(data)
print("Adding values into the database")
cur.executemany('''INSERT INTO ratings VALUES (:song_name, :song_popularity, :song_duration_ms, :acousticness, :danceability, :energy, :instrumentalness, :key, :liveness, :loudness, :audio_mode, :speechiness, :tempo, :time_signature, :audio_valence)''', data)
con.commit()

con.close()
