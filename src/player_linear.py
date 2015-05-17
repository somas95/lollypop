#!/usr/bin/python
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

from lollypop.define import Objects, NextContext
from lollypop.player_base import BasePlayer
from lollypop.track import Track

# Manage normal playback
class LinearPlayer(BasePlayer):
    """
        Init linear player
    """
    def __init__(self):
        BasePlayer.__init__(self)

    """
        Next track based on.current_track context
        @param sql as sqlite cursor
        @return track as Track
    """
    def next(self, sql=None):
        track_id = None
        if self.context.current_position is not None and self._albums:
            tracks = Objects.albums.get_tracks(self.current_track.album_id,
                                               self.context.genre_id,
                                               sql)
            if self.context.current_position + 1 >= len(tracks) or\
               self.context.next == NextContext.START_NEW_ALBUM:  # next album
                self.context.next = NextContext.NONE
                pos = self._albums.index(self.current_track.album_id)
                # we are on last album, go to first
                if pos + 1 >= len(self._albums):
                    pos = 0
                else:
                    pos += 1
                self.context.next_position = 0
                track_id = Objects.albums.get_tracks(self._albums[pos],
                                                     self.context.genre_id,
                                                     sql)[0]
            else:
                self.context.next_position = self.context.current_position + 1
                track_id = tracks[self.context.next_position]
        return Track(track_id)

    """
        Prev track base on.current_track context
        @param sql as sqlite cursor
        @return track as Track
    """
    def prev(self, sql=None):
        track_id = None            
        if track_id is None and self.context.current_position is not None:
            tracks = Objects.albums.get_tracks(self.current_track.album_id,
                                               self.context.genre_id)
            if self.context.current_position <= 0:  # Prev album
                pos = self._albums.index(self.current_track.album_id)
                if pos - 1 < 0:  # we are on last album, go to first
                    pos = len(self._albums) - 1
                else:
                    pos -= 1
                tracks = Objects.albums.get_tracks(self._albums[pos],
                                                   self.context.genre_id)
                self.context.prev_position = len(tracks) - 1
                track_id = tracks[self.context.prev_position]
            else:
                self.context.prev_position = self.context.current_position - 1
                track_id = tracks[self.context.prev_position]
        return Track(track_id)
