# Copyright (c) 2014-2015 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
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

import itertools

from lollypop.sqlcursor import SqlCursor
from lollypop.define import Lp, Type


class MpdDatabase:
    """
        Databse request from MPD module
    """

    def count(self, album, artist_id, genre_id, year):
        """
            Count songs and play time
            @param album as string
            @param artist id as int
            @param genre id as int
            @param year as int
        """
        songs = 0
        playtime = 0
        from_str = "tracks "
        where_str = ""
        print(album, artist_id, genre_id, year)
        if album is not None:
            from_str += ",albums"
            where_str += 'albums.name = "%s" AND' % album
        if artist_id is not None:
            from_str += ", artists"
            if "albums" not in from_str:
                from_str += ",albums"
            where_str += " artists.rowid = %s\
                          AND albums.artist_id = artists.rowid\
                          AND tracks.album_id = albums.rowid\
                          AND" % artist_id
        if genre_id is not None:
            from_str += ",track_genres"
            where_str += " track_genres.genre_id = %s\
                          AND track_genres.track_id = tracks.rowid\
                          AND" % genre_id
        if year is not None:
            where_str += " tracks.year = %s" % year

        with SqlCursor(Lp.db) as sql:
            request = "SELECT COUNT(*), SUM(tracks.duration) FROM "\
                       + from_str
            if where_str != "":
                 request += " WHERE " + where_str
            if request.endswith("AND"):
                request = request[:-3]
            result = sql.execute(request)
            v = result.fetchone()
            if v is not None:
                if v[0] is not None:
                    songs = v[0]
                if v[1] is not None:
                    playtime = v[1]
        return (songs, playtime)

    def get_artists_names(self):
        """
            Get artist names
            @return Artists as [str]
        """
        with SqlCursor(Lp.db) as sql:
            result = sql.execute("SELECT DISTINCT artists.name\
                                  FROM artists, albums\
                                  WHERE albums.artist_id = artists.rowid\
                                  ORDER BY artists.name COLLATE NOCASE")
            return list(itertools.chain(*result))

    def get_albums_ids_for_year(self, year):
        """
            Get albums ids for year
            @param year as str
        """
        with SqlCursor(Lp.db) as sql:
            if year is None:
                result = sql.execute("SELECT albums.rowid\
                                      FROM albums\
                                      WHERE year is null")
            else:
                result = sql.execute("SELECT albums.rowid\
                                      FROM albums\
                                      WHERE albums.year = ?", (year,))
            return list(itertools.chain(*result))

    def get_albums_ids_for(self, album, artist_id, genre, year=None):
        """
            Get all availables albums with name and year
            @param album as str
            @param genre as int
            @param year as int or None or Type.NONE (None or valued)
            @return Array of id as int
        """
        with SqlCursor(Lp.db) as sql:
            if artist_id is None:
                if genre is None:
                    if year is None:
                        result = sql.execute("SELECT rowid\
                                              FROM albums\
                                              WHERE name = ?\
                                              AND year is null",
                                             (album,))
                    elif year == Type.NONE:
                        result = sql.execute("SELECT rowid\
                                              FROM albums\
                                              WHERE name = ?",
                                             (album,))
                    else:
                        result = sql.execute("SELECT rowid\
                                              FROM albums\
                                              WHERE name = ?\
                                              AND year = ?",
                                             (album, year))
                else:
                    if year is None:
                        result = sql.execute(
                                     "SELECT rowid\
                                      FROM albums, album_genres\
                                      WHERE name = ?\
                                      AND album_genres.genre_id=?\
                                      AND album_genres.album_id=albums.rowid\
                                      AND year is null",
                                     (album, genre))
                    elif year == Type.NONE:
                        result = sql.execute(
                                     "SELECT rowid\
                                      FROM albums, album_genres\
                                      WHERE name = ?\
                                      AND album_genres.genre_id=?\
                                      AND album_genres.album_id=albums.rowid",
                                     (album, genre))
                    else:
                        result = sql.execute(
                                     "SELECT rowid\
                                      FROM albums, album_genres\
                                      WHERE name = ?\
                                      AND album_genres.genre_id=?\
                                      AND album_genres.album_id=albums.rowid\
                                      AND year = ?",
                                     (album, genre, year))
            else:
                if genre is None:
                    if year is None:
                        result = sql.execute("SELECT rowid\
                                              FROM albums\
                                              WHERE name = ?\
                                              AND artist_id = ?\
                                              AND year is null",
                                             (album, artist_id))
                    else:
                        result = sql.execute("SELECT rowid\
                                              FROM albums\
                                              WHERE name = ?\
                                              AND artist_id = ?\
                                              AND year = ?",
                                             (album, artist_id, year))
                else:
                    if year is None:
                        result = sql.execute(
                                     "SELECT rowid\
                                      FROM albums, album_genres\
                                      WHERE name = ?\
                                      AND artist_id = ?\
                                      AND album_genres.genre_id=?\
                                      AND album_genres.album_id=albums.rowid\
                                      AND year is null",
                                     (album, artist_id, genre))
                    elif year == Type.NONE:
                        result = sql.execute(
                                     "SELECT rowid\
                                      FROM albums, album_genres\
                                      WHERE name = ?\
                                      AND artist_id = ?\
                                      AND album_genres.genre_id=?\
                                      AND album_genres.album_id=albums.rowid",
                                     (album, artist_id, genre))
                    else:
                        result = sql.execute(
                                     "SELECT rowid\
                                      FROM albums, album_genres\
                                      WHERE name = ?\
                                      AND artist_id = ?\
                                      AND album_genres.genre_id=?\
                                      AND album_genres.album_id=albums.rowid\
                                      AND year = ?",
                                     (album, artist_id, genre, year))
            return list(itertools.chain(*result))

    def get_albums_years_by_name(self, album, artist_id):
        """
            Get all availables albums years
            @return Array of year as int
        """
        with SqlCursor(Lp.db) as sql:
            result = sql.execute("SELECT DISTINCT year\
                                  FROM albums\
                                  WHERE artist_id=?\
                                  AND name=?", (artist_id, album))
            return list(itertools.chain(*result))

    def get_albums_years(self):
        """
            Get all availables albums years
            @return Array of year as int
        """
        with SqlCursor(Lp.db) as sql:
            result = sql.execute("SELECT DISTINCT year\
                                  FROM albums\
                                  WHERE year is not null")
            return list(itertools.chain(*result))
