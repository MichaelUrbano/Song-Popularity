import sqlite3

songpop = "/home/heinz/Documents/School/SUU/School/Machine Learning/MusicRatings/SongPop.db"
metadata = "/home/heinz/Documents/School/SUU/School/Machine Learning/MusicRatings/track_metadata.db"

con3 = sqlite3.connect(songpop)

print("Removing previous table")
con3.execute("DROP TABLE IF EXISTS songs")
con3.commit()
print("Creating new table")
con3.execute('''CREATE TABLE "songs" (
	"track_id"	text,
	"title"	text,
	"song_id"	text,
	"release"	text,
	"artist_id"	text,
	"artist_mbid"	text,
	"artist_name"	text,
	"duration"	real,
	"artist_familiarity"	real,
	"artist_hotttnesss"	real,
	"year"	int,
	"track_7digitalid"	int,
	"shs_perf"	int,
	"shs_work"	int,
	PRIMARY KEY("track_id")
);''')
con3.commit()

print("Copying data")
con3.execute("ATTACH '" + metadata +  "' as dba")
con3.execute("INSERT or IGNORE INTO songs SELECT * FROM dba.songs")
con3.commit()
con3.execute("detach database dba")
con3.close()
