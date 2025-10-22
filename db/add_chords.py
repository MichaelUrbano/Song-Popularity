import csv
import sqlite3

con = sqlite3.connect("/home/heinz/Documents/School/SUU/School/Machine Learning/MusicRatings/SongPop.db")
cur = con.cursor()

print("Removing previous table")
cur.execute("DROP TABLE IF EXISTS chords")
con.commit()
print("Creating new table")
cur.execute('''CREATE TABLE "chords" (
	"song_id"	INTEGER,
	"chords"	TEXT,
	"release_date"	TEXT,
	"genres"	TEXT,
	"decade"	INTEGER,
	"rock_genre"	TEXT,
	"artist_id"	TEXT,
	"main_genre"	TEXT,
	"spotify_song_id"	TEXT,
	"spotify_artist_id"	TEXT
);''')
con.commit()

print("Retrieving data")
data = []
file_name = "/home/heinz/Documents/School/SUU/School/Machine Learning/MusicRatings/Chordonomicon/chordonomicon_v2.csv"
with open(file_name, newline='') as csvfile:
    spamreader = csv.reader(csvfile)
    # i = 0
    for row in spamreader:
        # print()
        # for egg in row:
        #     print(repr(egg))
        # if i > 3:
        #     break;
        # print('\t'.join(row))
        # insert into the rows database the records
        # Blank values should be NULL in the database - that's what all the expressions are for
        data.append({"song_id":             (row[0] if row[0] != '' else None),
                    "chords":               (row[1] if row[1] != '' else None),
                    "release_date":         (row[2] if row[2] != '' else None),
                    "genres":               (row[3] if row[3] != '' else None),
                    "decade":               (row[4] if row[4] != '' else None),
                    "rock_genre":           (row[5] if row[5] != '' else None),
                    "artist_id":            (row[6] if row[6] != '' else None),
                    "main_genre":           (row[7] if row[7] != '' else None),
                    "spotify_song_id":      (row[8] if row[8] != '' else None),
                    "spotify_artist_id":    (row[9] if row[9] != '' else None)})
        # print(data[i])
        # i += 1

data.pop(0)  # remove the first line
# print(data[0:5])
# exit()

data = tuple(data)
print("Adding values into the database")
cur.executemany('''INSERT INTO chords VALUES (:song_id, :chords, :release_date, :genres, :decade, :rock_genre, :artist_id, :main_genre, :spotify_song_id, :spotify_artist_id)''', data)
con.commit()

con.close()
