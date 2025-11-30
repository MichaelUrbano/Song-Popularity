OK, the base database is **mxm_dataset.db**, but in the Python code it’s called **SongPop.db**.
This database has two tables: **lyrics and words**.
The python files each add another table to the database.
1. **add_metadata.py** - it adds a table called **songs**, copied directly from **track_metadata.db**
2. **Add_chords.py** - it adds a table called **chords**, copied from **chordonomicon_v2.csv**
3. **Add_ratings.py** - it adds a table called **ratings**, copied from **song_ratings_data.csv**
4. **Add_spotify.py** - it adds a table called **spotify**, copied from **Music Info.csv**

Run each of these files in order, and you’ve got the complete database!
**Important: make sure to change the file paths in the code before running any of these!**

The main table is **songs**. The **chords** and **ratings** tables connect to **songs** through the **spotify** table, which contains the exact same title used in the **ratings** table, and the spotify id used in the **chords** table.
The **lyrics** table connects directly to the **songs** table via the same Million Song Dataset ID.
Using a big join, it should be possible to create a table with all the relevant info.
I would prioritize songs which have ratings, then lyrics, then chords.
