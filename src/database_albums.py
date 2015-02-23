#!/usr/bin/python
# Copyright (c) 2014-2015 Cedric Bellegarde <gnumdk@gmail.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from gettext import gettext as _
from lollypop.define import Objects, COMPILATIONS, ALL


# All functions take a sqlite cursor as last parameter,
# set another one if you're in a thread
class DatabaseAlbums:
    def __init__(self):
        pass

    """
        Add a new album to database
        @param Album name as string
        @param artist id as int,
        @param genre id as int
        @param year as int,
        @param path as string
        @warning: commit needed
    """
    def add(self, name, artist_id, genre_id,
            year, path, popularity, sql=None):
        if not sql:
            sql = Objects.sql
        sql.execute("INSERT INTO albums (name, artist_id, genre_id, year, path, popularity)\
                     VALUES (?, ?, ?, ?, ?, ?)", (name, artist_id, genre_id,
                                                  year, path, popularity))

    """
        Set artist id
        @param album id as int, artist_id as int
        @warning: commit needed
    """
    def set_artist_id(self, album_id, artist_id, sql):
        if not sql:
            sql = Objects.sql
        sql.execute("UPDATE albums SET artist_id=? WHERE rowid=?",
                    (artist_id, album_id))

    """
        Set album path for album id
        @param Album id as int, path as string
        @warning: commit needed
    """
    def set_path(self, album_id, path, sql=None):
        if not sql:
            sql = Objects.sql
        sql.execute("UPDATE albums SET path=? WHERE rowid=?", (path, album_id))

    """
        Increment popularity field for album id
        No commit needed
        @param int
    """
    def set_more_popular(self, album_id, sql=None):
        if not sql:
            sql = Objects.sql
        result = sql.execute("SELECT popularity from albums WHERE rowid=?",
                             (album_id,))
        pop = result.fetchone()
        if pop:
            current = pop[0]
        else:
            current = 0
        current += 1
        sql.execute("UPDATE albums set popularity=? WHERE rowid=?",
                    (current, album_id))
        sql.commit()

    """
        Get album id
        @param Album name as string,
        @param artist id(can be None) as int
        @param genre_id as int
        @return Album id as int
    """
    def get_id(self, album_name, artist_id, genre_id, sql=None):
        if not sql:
            sql = Objects.sql
        result = sql.execute("SELECT rowid FROM albums where name=? COLLATE NOCASE\
                              AND artist_id=? AND genre_id=?", (album_name,
                                                                artist_id,
                                                                genre_id))
        v = result.fetchone()
        if v and len(v) > 0:
            return v[0]

        return None

    """
        Get genre id
        @param Album id as int
        @return Genre id as int
    """
    def get_genre_id(self, album_id, sql=None):
        if not sql:
            sql = Objects.sql
        result = sql.execute("SELECT genre_id FROM albums WHERE rowid=?",
                             (album_id,))
        v = result.fetchone()
        if v and len(v) > 0:
            return v[0]

        return -1

    """
        Get genre name
        @param Album id as int
        @return Genre name as str
    """
    def get_genre_name(self, album_id, sql=None):
        if not sql:
            sql = Objects.sql
        result = sql.execute("SELECT genres.name FROM albums,genres\
                              WHERE albums.rowid=?\
                              AND genres.rowid = albums.genre_id", (album_id,))
        v = result.fetchone()
        if v and len(v) > 0:
            return v[0]

        return ""

    """
        Get album name for album id
        @param Album id as int
        @return Album name as string
    """
    def get_name(self, album_id, sql=None):
        if not sql:
            sql = Objects.sql
        result = sql.execute("SELECT name FROM albums where rowid=?",
                             (album_id,))
        v = result.fetchone()
        if v and len(v) > 0:
            return v[0]

        return _("Unknown")

    """
        Get artist name
        @param Album id as int
        @return Artist name as string
    """
    def get_artist_name(self, album_id, sql=None):
        if not sql:
            sql = Objects.sql
        result = sql.execute("SELECT artists.name from artists, albums\
                              WHERE albums.rowid=? AND albums.artist_id ==\
                              artists.rowid", (album_id,))
        v = result.fetchone()
        if v and len(v) > 0:
            return v[0]

        return _("Compilation")

    """
        Get album artist id
        @param album_id
        @return artist id
    """
    def get_artist_id(self, album_id, sql=None):
        if not sql:
            sql = Objects.sql
        result = sql.execute("SELECT artist_id FROM albums where rowid=?",
                             (album_id,))
        v = result.fetchone()
        if v and len(v) > 0:
            return v[0]

        return COMPILATIONS

    """
        Get compilation artists id
        @param album id as int
        @return array of artists id, empty if not a compilation
    """
    def get_compilation_artists(self, album_id, sql=None):
        if not sql:
            sql = Objects.sql
        artists = []
        result = sql.execute("SELECT artist_id from tracks where album_id=?\
                              AND artist_id=?", (album_id, COMPILATIONS))
        for row in result:
            artists += row
        return artists

    """
        Get album year for album id
        @param Album id as int
        @return Album year as string
    """
    def get_year(self, album_id, sql=None):
        if not sql:
            sql = Objects.sql
        result = sql.execute("SELECT year FROM albums where rowid=?",
                             (album_id,))
        v = result.fetchone()
        if v and len(v) > 0:
            if v[0]:
                return str(v[0])

        return ""

    """
        Get album path for album id
        @param Album id as int
        @return Album path as string
    """
    def get_path(self, album_id, sql=None):
        if not sql:
            sql = Objects.sql
        result = sql.execute("SELECT path FROM albums WHERE rowid=?",
                             (album_id,))
        v = result.fetchone()
        if v and len(v) > 0:
            return v[0]

        return ""

    """
        Count album having path as album path
    """
    def get_path_count(self, path, sql=None):
        if not sql:
            sql = Objects.sql

        result = sql.execute("SELECT count(path) FROM albums WHERE path=?",
                             (path,))
        v = result.fetchone()
        if v and len(v) > 0:
            return v[0]

        return 1

    """
        Get albums ids with popularity
        @param None
        @return Array of album ids as int
    """
    def get_populars(self, sql=None):
        if not sql:
            sql = Objects.sql
        albums = []
        result = sql.execute("SELECT rowid FROM albums WHERE popularity!=0\
                             ORDER BY popularity DESC LIMIT 100")
        for row in result:
            albums += row
        return albums

    """
        Get album ids for party mode based on genre ids
        @param Array of genre ids
        @return Array of album ids as int
    """
    def get_party_ids(self, genre_ids, sql=None):
        if not sql:
            sql = Objects.sql
        albums = []
        # get popular first
        if -1 in genre_ids:
            albums = self.get_populars()
        for genre_id in genre_ids:
            for album in Objects.genres.get_albums(genre_id, sql):
                if album not in albums:
                    albums.append(album)
        return albums

    """
        Get number of tracks for album_id
        Will count tracks from albums with same name,
        artist and a different genre
        @param Album id as int
        @return count as int
    """
    def get_count(self, album_id, sql=None):
        if not sql:
            sql = Objects.sql
        artist_id = Objects.albums.get_artist_id(album_id, sql)
        album_name = Objects.albums.get_name(album_id, sql)
        result = sql.execute("SELECT COUNT(tracks.rowid) FROM tracks, albums\
                              WHERE albums.artist_id=? AND albums.name=?\
                              AND albums.rowid=tracks.album_id\
                              ORDER BY discnumber, tracknumber", (artist_id,
                                                                  album_name))
        v = result.fetchone()
        if v and len(v) > 0:
            return v[0]
        return -1

    """
        Get tracks for album id
        Will search track from albums
        @param Album id as int
        @return Arrays of tracks id as int
    """
    def get_tracks(self, album_id, sql=None):
        if not sql:
            sql = Objects.sql
        tracks = []
        result = sql.execute("SELECT tracks.rowid FROM tracks\
                              WHERE album_id=?\
                              ORDER BY discnumber, tracknumber", (album_id,))
        for row in result:
            tracks += row
        return tracks

    """
        Get tracks path for album id
        Will search track from albums from same artist
        with same name and different genre
        @param Album id as int
        @return Arrays of tracks id as int
    """
    def get_tracks_path(self, album_id, sql=None):
        if not sql:
            sql = Objects.sql
        tracks = []
        result = sql.execute("SELECT tracks.filepath FROM tracks\
                              WHERE album_id=?\
                              ORDER BY discnumber, tracknumber", (album_id,))
        for row in result:
            tracks += row
        return tracks

    """
        Get tracks informations for album id
        Will search track from albums from same artist
        with same name and different genre
        @param Album id as int, artist_id as int
        @return Arrays of (tracks id as int, name as string, artist id as int,
                           filepath as string, length as int)
    """
    def get_tracks_infos(self, album_id, sql=None):
        if not sql:
            sql = Objects.sql
        tracks = []
        artist_id = Objects.albums.get_artist_id(album_id, sql)
        album_name = Objects.albums.get_name(album_id, sql)
        result = sql.execute("SELECT tracks.rowid, tracks.name,\
                              tracks.artist_id, tracks.filepath,\
                              tracks.length FROM tracks, albums\
                              WHERE albums.artist_id=? AND albums.name=?\
                              AND albums.rowid=tracks.album_id\
                              ORDER BY discnumber, tracknumber", (artist_id,
                                                                  album_name))
        for row in result:
            tracks += (row,)
        return tracks

    """
        Get albums ids
        @param Artist id as int/None, genre id as int/None
        @return Array of album ids as int
    """
    def get_ids(self, artist_id=None, genre_id=None, sql=None):
        if not sql:
            sql = Objects.sql
        albums = []
        result = []
        # Get albums for artist id and genre id
        if artist_id and genre_id:
            result = sql.execute("SELECT rowid FROM albums\
                                  WHERE artist_id=? and genre_id=?\
                                  ORDER BY year, name", (artist_id, genre_id))
        # Get albums for all artists
        elif not artist_id and not genre_id:
            result = sql.execute("SELECT albums.rowid FROM albums,artists\
                                  WHERE artists.rowid=albums.artist_id\
                                  ORDER BY artists.name COLLATE NOCASE,\
                                  albums.year,\
                                  albums.name COLLATE NOCASE")
        # Get albums for genre
        elif not artist_id:
            result = sql.execute("SELECT albums.rowid FROM albums, artists\
                                  WHERE genre_id=? and artists.rowid=artist_id\
                                  ORDER BY artists.name COLLATE NOCASE,\
                                  albums.year,\
                                  albums.name COLLATE NOCASE", (genre_id,))
        # Get albums for artist
        elif not genre_id:
            result = sql.execute("SELECT DISTINCT rowid FROM albums\
                                  WHERE artist_id=?\
                                  GROUP BY name\
                                  ORDER BY year, name", (artist_id,))

        for row in result:
            albums += row
        return albums

    """
        Get all compilations
        @param genre id as int
        @return Array of album ids as int
    """
    def get_compilations(self, genre_id, sql=None):
        if not sql:
            sql = Objects.sql
        albums = []
        result = []
        # Get all compilations
        if genre_id == ALL or not genre_id:
            result = sql.execute("SELECT albums.rowid FROM albums\
                                  WHERE artist_id=-1\
                                  ORDER BY albums.name, albums.year")
        # Get compilation for genre id
        else:
            result = sql.execute("SELECT albums.rowid FROM albums\
                                  WHERE genre_id=? and artist_id=-1\
                                  ORDER BY albums.name,\
                                  albums.year", (genre_id,))
        for row in result:
            albums += row
        return albums

    """
        Sanitize compilations, after scan some albums marked
        as compilation (no artist album)
        can be albums => all tracks are from the same artist
        No commit needed
    """
    def sanitize(self, sql):
        if not sql:
            sql = Objects.sql
        result = sql.execute("SELECT DISTINCT tracks.artist_id, album_id,\
                              albums.name, albums.genre_id FROM tracks, albums\
                              WHERE albums.rowid == tracks.album_id\
                              AND albums.artist_id == ?\
                              GROUP BY album_id\
                              HAVING COUNT(DISTINCT tracks.artist_id) == 1", (
                              COMPILATIONS,))

        for artist_id, album_id, album_name, album_genre in result:
            existing_id = self.get_id(album_name, artist_id, album_genre, sql)
            # Some tracks from album have an album artist and some not
            if existing_id is not None and existing_id != album_id:
                sql.execute("UPDATE tracks SET album_id=? WHERE album_id=?",
                            (existing_id, album_id))
                sql.execute("DELETE FROM albums WHERE rowid == ?",
                            (album_id,))
            # Album is not a compilation,
            # so update album id to march track album id
            else:
                sql.execute("UPDATE albums SET artist_id=? WHERE rowid=?",
                            (artist_id, album_id))
        sql.commit()

    """
        Search for albums looking like string
        @param string
        return: Array of (id as int, artist_id as int)
    """
    def search(self, string, sql=None):
        if not sql:
            sql = Objects.sql
        albums = []
        result = sql.execute("SELECT rowid, artist_id FROM albums\
                              WHERE name LIKE ?\
                              LIMIT 25", ('%'+string+'%',))
        for row in result:
            albums += (row,)
        return albums
