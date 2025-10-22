import csv
import sqlite3

con = sqlite3.connect("/home/heinz/Documents/School/SUU/School/Machine Learning/MusicRatings/SongPop.db")
cur = con.cursor()

print("Removing previous table")
cur.execute("DROP TABLE IF EXISTS spotify")
con.commit()
print("Creating new table")
cur.execute('''CREATE TABLE "spotify" (
	"track_id"	TEXT,
	"name"	TEXT,
	"artist"	TEXT,
	"spotify_preview_url"	TEXT,
	"spotify_id"	TEXT
);''')
con.commit()

print("Retrieving data")
data = []
file_name = "/home/heinz/Documents/School/SUU/School/Machine Learning/MusicRatings/MSDandSPT/Music Info.csv"
with open(file_name, newline='') as csvfile:
    spamreader = csv.reader(csvfile)
    for row in spamreader:
        # print('\t'.join(row))
        # insert into the rows database the records
        data.append({"track_id":            row[0],
                    "name":                 row[1],
                    "artist":               row[2],
                    "spotify_preview_url":  row[3],
                    "spotify_id":           row[4]})

data.pop(0)  # remove the first line
# print(data[0:5])
# exit()

data = tuple(data)
print("Adding values into the database")
cur.executemany('''INSERT INTO spotify VALUES (:track_id, :name, :artist, :spotify_preview_url, :spotify_id)''', data)
con.commit()

con.close()
