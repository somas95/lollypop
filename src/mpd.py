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

from gi.repository import GLib, Gst

import socketserver
import threading
from time import sleep

from lollypop.define import Lp, Type
from lollypop.objects import Track
from lollypop.database_mpd import MpdDatabase
from lollypop.utils import translate_artist_name, format_artist_name


class MpdHandler(socketserver.BaseRequestHandler):
    idle = None

    def handle(self):
        """
            One function to handle them all
        """
        self._mpddb = MpdDatabase()
        self._playlist_version = 0
        self._idle_strings = []
        self._current_song = None
        self._signal1 = Lp.player.connect('current-changed',
                                          self._on_player_changed)
        self._signal2 = Lp.player.connect('status-changed',
                                          self._on_player_changed)
        self._signal3 = Lp.player.connect('seeked',
                                          self._on_player_changed)
        self._signal4 = Lp.playlists.connect('playlist-changed',
                                             self._on_playlist_changed)
        self.request.send("OK MPD 0.19.0\n".encode('utf-8'))
        try:
            while self.server.running:
                list_ok = False
                # sleep(1)
                data = self.request.recv(4096).decode('utf-8')
                # We check if we need to wait for a command_list_end
                list_begin = data.startswith('command_list_begin')
                list_end = data.endswith('command_list_end\n')
                if list_end:
                    data = data.replace('command_list_end\n', '')
                    list_begin = False
                # We remove begin/end
                data = data.replace('command_list_begin\n', '')
                while list_begin:
                    data += self.request.recv(1024).decode('utf-8')
                    if data.endswith('command_list_end\n'):
                        data = data.replace('command_list_end\n', '')
                        list_begin = False
                if data == '':
                    raise IOError
                else:
                    if data.find('command_list_ok_begin') != -1:
                        list_ok = True
                        data = data.replace('command_list_ok_begin\n', '')
                    cmds = data.split('\n')
                    print(cmds)
                    if cmds:
                        try:
                            # Group commands
                            cmd_dict = {}
                            for cmd in cmds:
                                command = cmd.split(' ')[0]
                                if command != '':
                                    size = len(command) + 1
                                    if command not in cmd_dict:
                                        cmd_dict[command] = []
                                    cmd_dict[command].append(cmd[size:])
                            print(cmd_dict)
                            for key in cmd_dict.keys():
                                if key.find("idle") == -1:
                                    self._noidle(None, None)
                                call = getattr(self, '_%s' % key)
                                call(cmd_dict[key], list_ok)
                        except Exception as e:
                            print("MpdHandler::handle(): ", command, e)
                            self._send_msg()
                self._idle_strings = []
        except:
            self._noidle(None, None)
        Lp.player.disconnect(self._signal1)
        Lp.player.disconnect(self._signal2)
        Lp.player.disconnect(self._signal3)
        Lp.playlists.disconnect(self._signal4)

    def _add(self, args_array, list_ok):
        """
            Add track to mpd playlist
            @param args as [str]
            @param add list_OK as bool
        """
        tracks = []
        for args in args_array:
            track_id = Lp.tracks.get_id_by_path(self._get_args(args)[0])
            tracks.append(Track(track_id))
        Lp.playlists.add_tracks(Type.MPD, tracks)
        self._send_msg()

    def _clear(self, args_array, list_ok):
        """
            Clear mpd playlist
            @param args as [str]
            @param add list_OK as bool
        """
        Lp.playlists.clear(Type.MPD, True)
        self._send_msg()

    def _channels(self, args_array, list_ok):
        msg = ""
        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _commands(self, args_array, list_ok):
        """
            Send available commands
            @param args as [str]
            @param add list_OK as bool
        """
        msg = "command: add\ncommand: clear\ncommand: channels\ncommand: count\
\ncommand: currentsong\ncommand: delete\ncommand: idle\ncommand: noidle\
\ncommand: list\ncommand: listallinfo\ncommand: listplaylists\ncommand: lsinfo\
\ncommand: next\ncommand: outputs\ncommand: pause\ncommand: play\
\ncommand: playid\ncommand: playlistinfo\ncommand: plchanges\
\ncommand: plchangesposid\ncommand: prev\ncommand: replay_gain_status\
\ncommand: repeat\ncommand: seek\ncommand: seekid\ncommand: search\
\ncommand: setvol\ncommand: stats\ncommand: status\ncommand: sticker\
\ncommand: stop\ncommand: tagtypes\ncommand: update\ncommand: urlhandlers\n"
        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _count(self, args_array, list_ok):
        """
            Send lollypop current song
            @param args as [str]
            @param add list_OK as bool
        """
        args = self._get_args(args_array[0])
        count = 0
        playtime = 0
        # Search for filters
        i = 0
        artist = artist_id = None
        album = None
        genre = genre_id = None
        date = ''
        while i < len(args) - 1:
            if args[i].lower() == 'album':
                album = args[i+1]
            elif args[i].lower() == 'artist':
                artist = format_artist_name(args[i+1])
            elif args[i].lower() == 'genre':
                genre = args[i+1]
            elif args[i].lower() == 'date':
                date = args[i+1]
            i += 2

        try:
            year = int(date)
        except:
            year = None
        if genre is not None:
            genre_id = Lp.genres.get_id(genre)
        if artist is not None:
            artist_id = Lp.artists.get_id(artist)
        albums = []
        if album is None and artist_id is not None:
            albums = Lp.albums.get_ids(artist_id, genre_id)
        else:
            albums = self._mpddb.get_albums_ids_for(album, artist_id,
                                                    genre_id, year)

        for album_id in albums:
            for disc in Lp.albums.get_discs(album_id, None):
                count += Lp.albums.get_count_for_disc(album_id, None, disc)
                playtime += Lp.albums.get_duration_for_disc(album_id,
                                                            None,
                                                            disc)
        msg = "songs: %s\nplaytime: %s\n" % (count, playtime)
        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _currentsong(self, args_array, list_ok):
        """
            Send lollypop current song
            @param args as [str]
            @param add list_OK as bool
        """
        if self._current_song is None:
            self._current_song = self._string_for_track_id(
                                                    Lp.player.current_track.id)
        msg = self._current_song
        if list_ok:
            msg = "list_OK\n"
        self._send_msg(msg)

    def _delete(self, args_array, list_ok):
        """
            Delete track from playlist
            @param args as [str]
            @param add list_OK as bool
        """
        for args in args_array:
            tracks = []
            for track_id in Lp.playlists.get_tracks_ids(Type.MPD):
                tracks.append(Track(track_id))
            del tracks[self._get_args(args)[0]]
            Lp.playlists.clear(Type.MPD, False)
            Lp.playlists.add_tracks(Type.MPD, tracks)

    def _idle(self, args_array, list_ok):
        msg = ''
        self.request.settimeout(0)
        MpdHandler.idle = self
        while not self._idle_strings and MpdHandler.idle == self:
            print('IDLE', MpdHandler.idle, self, self._idle_strings)
            sleep(1)
        if MpdHandler.idle == self:
            for string in self._idle_strings:
                msg += "changed: %s\n" % string
        self._send_msg(msg)
        self.request.settimeout(10)

    def _noidle(self, args_array, list_ok):
        MpdHandler.idle = None

    def _list(self, args_array, list_ok):
        """
            List objects
            @param args as [str]
            @param add list_OK as bool
        """
        msg = ""
        args = self._get_args(args_array[0])

        # Search for filters
        i = 1
        artist = None
        album = None
        date = None
        while i < len(args) - 1:
            if args[i].lower() == 'album':
                album = args[i+1]
            elif args[i].lower() == 'artist':
                artist = format_artist_name(args[i+1])
            elif args[i].lower() == 'date':
                try:
                    date = int(args[i+1])
                except:
                    date = None
            i += 2
        if args[0].lower() == 'file':
            if artist is not None and album is not None:
                artist_id = Lp.artists.get_id(artist)
                album_id = Lp.albums.get_album_id(album, artist_id, date, None)
                for track in Lp.albums.get_tracks(album_id, None):
                    path = Lp.tracks.get_path(track)
                    msg += "File: "+path+"\n"
        if args[0].lower() == 'album':
            if artist is None:
                albums_ids = Lp.albums.get_ids()
            else:
                artist_id = Lp.artists.get_id(artist)
                albums_ids = Lp.artists.get_albums(artist_id)
            for album_id in albums_ids:
                msg += "Album: "+Lp.albums.get_name(album_id)+"\n"
        elif args[0].lower() == 'artist':
            results = self._mpddb.get_artists_names()
            for name in results:
                msg += "Artist: "+translate_artist_name(name)+"\n"
        elif args[0].lower() == 'genre':
            results = Lp.genres.get_names()
            for name in results:
                msg += "Genre: "+name+"\n"
        elif args[0].lower() == 'date':
            if artist is not None and album is not None:
                artist_id = Lp.artists.get_id(artist)
                for year in self._mpddb.get_albums_years_by_name(album,
                                                                 artist_id):
                    msg += "Date: "+str(year)+"\n"
            else:
                for year in self._mpddb.get_albums_years():
                    msg += "Date: "+str(year)+"\n"
        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _listall(self, args_array, list_ok):
        """
            List all tracks
            @param args as [str]
            @param add list_OK as bool
        """
        self._send_msg()

    def _listallinfo(self, args_array, list_ok):
        """
            List all tracks
            @param args as [str]
            @param add list_OK as bool
        """
        i = 0
        msg = ""
        for track_id in Lp.tracks.get_ids():
            msg += self._string_for_track_id(track_id)
            if i > 100:
                self.request.send(msg.encode("utf-8"))
                msg = ""
                i = 0
            else:
                i += 1

        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _listplaylists(self, args_array, list_ok):
        """
            Send available playlists
            @param args as [str]
            @param add list_OK as bool
        """
        msg = ""
        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _lsinfo(self, args_array, list_ok):
        """
            List directories and files
            @param args as [str]
            @param add list_OK as bool
        """
        msg = ""
        if args_array:
            pass  # args = self._get_args(args_array[0])
        else:
            results = Lp.genres.get()
            i = 0
            for (rowid, genre) in results:
                msg += 'directory: '+genre+'\n'
                if i > 100:
                    self._send_msg(msg)
                    msg = ""
                    i = 0
                i += 1

        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _next(self, args_array, list_ok):
        """
            Send output
            @param args as [str]
            @param add list_OK as bool
        """
        GLib.idle_add(Lp.player.next)
        self._send_msg()

    def _outputs(self, args_array, list_ok):
        """
            Send output
            @param args as [str]
            @param add list_OK as bool
        """
        msg = "outputid: 0\noutputname: null\noutputenabled: 1\n"
        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _pause(self, args_array, list_ok):
        """
            Pause track
            @param args as [str]
            @param add list_OK as bool
        """
        try:
            args = self._get_args(args_array[0])
            if args[0] == "0":
                GLib.idle_add(Lp.player.play)
            else:
                GLib.idle_add(Lp.player.pause)
        except Exception as e:
            print("MpdHandler::_pause(): %s" % e)
        self._send_msg()

    def _play(self, args_array, list_ok):
        """
            Play track
            @param args as [str]
            @param add list_OK as bool
        """
        try:
            if Lp.player.get_user_playlist_id() != Type.MPD:
                Lp.player.set_user_playlist(Type.MPD)
            if self._get_status == 'stop':
                track_id = Lp.player.get_user_playlist()[0]
                GLib.idle_add(Lp.player.load_in_playlist, track_id)
            else:
                GLib.idle_add(Lp.player.play)
        except Exception as e:
            print("MpdHandler::_play(): %s" % e)
        self._send_msg()

    def _playid(self, args_array, list_ok):
        """
            Play track
            @param args as [str]
            @param add list_OK as bool
        """
        try:
            arg = int(self._get_args(args_array[0])[0])
            if Lp.player.get_user_playlist_id() != Type.MPD:
                Lp.player.set_user_playlist(Type.MPD)
            GLib.idle_add(Lp.player.load_in_playlist, arg)
        except Exception as e:
            print("MpdHandler::_playid(): %s" % e)
        self._send_msg()

    def _playlistinfo(self, args_array, list_ok):
        """
            Send informations about playlists
            @param args as [str]
            @param add list_OK as bool
        """
        msg = ""
        tracks_ids = Lp.playlists.get_tracks_ids(Type.MPD)
        if Lp.player.is_playing() and\
           Lp.player.current_track.id not in tracks_ids:
            tracks_ids.insert(0, Lp.player.current_track.id)
        for track_id in tracks_ids:
            msg += self._string_for_track_id(track_id)
        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _plchanges(self, args_array, list_ok):
        """
            Send informations about playlists
            @param args as [str]
            @param add list_OK as bool
        """
        self._playlistinfo(args_array, list_ok)

    def _plchangesposid(self, args_array, list_ok):
        """
            Send informations about playlists
            @param args as [str]
            @param add list_OK as bool
        """
        msg = ""
        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _prev(self, args_array, list_ok):
        """
            Send output
            @param args as [str]
            @param add list_OK as bool
        """
        GLib.idle_add(Lp.player.prev)
        self._send_msg()

    def _replay_gain_status(self, args_array, list_ok):
        """
            Send output
            @param args as [str]
            @param add list_OK as bool
        """
        msg = "replay_gain_mode: off\n"
        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _repeat(self, args_array, list_ok):
        """
            Ignore
            @param args as [str]
            @param add list_OK as bool
        """
        self._send_msg()

    def _seek(self, args_array, list_ok):
        """
           Seek current
           @param args as [str]
           @param add list_OK as bool
        """
        args = self._get_args(args_array[0])
        seek = int(args[1])
        GLib.idle_add(Lp.player.seek, seek)
        self._send_msg()

    def _seekid(self, args_array, list_ok):
        """
            Seek track id
            @param args as [str]
            @param add list_OK as bool
        """
        args = self._get_args(args_array[0])
        track_id = int(args[0])
        seek = int(args[1])
        if track_id == Lp.player.current_track.id:
            GLib.idle_add(Lp.player.seek, seek)
        self._send_msg()

    def _search(self, args_array, list_ok):
        """
            Send stats about db
            @param args as [str]
            @param add list_OK as bool
        """
        args = self._get_args(args_array[0])
        msg = ""
        # Search for filters
        i = 0
        artist = None
        album = None
        date = ''
        while i < len(args) - 1:
            if args[i].lower() == 'album':
                album = args[i+1]
            elif args[i].lower() == 'artist':
                artist = format_artist_name(args[i+1])
            elif args[i].lower() == 'date':
                date = args[i+1]
            i += 2
        try:
            year = int(date)
        except:
            year = None

        albums = []
        if album is None:
            if artist is not None:
                artist_id = Lp.artists.get_id(artist)
                if artist_id is not None:
                    albums = Lp.artists.get_albums(artist_id)
        else:
            if artist is None:
                albums = self._mpddb.get_albums_ids_for(album, None, year)
            else:
                artist_id = Lp.artists.get_id(artist)
                if artist_id is not None:
                    albums = [Lp.albums.get_album_id(album, artist_id,
                                                     year, None)]
        for album_id in albums:
            for track_id in Lp.albums.get_tracks(album_id, None):
                msg += self._string_for_track_id(track_id)
        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _setvol(self, args_array, list_ok):
        """
            Send stats about db
            @param args as [str]
            @param add list_OK as bool
        """
        args = self._get_args(args_array[0])
        vol = float(args[0])
        Lp.player.set_volume(vol/100)

    def _stats(self, args_array, list_ok):
        """
            Send stats about db
            @param args as [str]
            @param add list_OK as bool
        """
        artists = Lp.artists.count()
        albums = Lp.albums.count()
        tracks = Lp.tracks.count()
        msg = "artists: %s\nalbums: %s\nsongs: %s\nuptime: 0\
\nplaytime: 0\ndb_playtime: 0\ndb_update: 0\n" % \
            (artists, albums, tracks)
        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _status(self, args_array, list_ok):
        """
            Send lollypop status
            @param args as [str]
            @param add list_OK as bool
        """
        if self._get_status() != 'stop':
            elapsed = Lp.player.get_position_in_track() / 1000000 / 60
            time = Lp.player.current_track.duration
            songid = Lp.player.current_track.id
        else:
            time = 0
            elapsed = 0
            songid = -1
        msg = "volume: %s\nrepeat: %s\nrandom: %s\
\nsingle: %s\nconsume: %s\nplaylist: %s\
\nplaylistlength: %s\nstate: %s\nsong: %s\
\nsongid: %s\ntime: %s:%s\nelapsed: %s\n" % (
           int(Lp.player.get_volume()*100),
           1,
           int(Lp.player.is_party()),
           1,
           1,
           self._playlist_version,
           len(Lp.playlists.get_tracks(Type.MPD)),
           self._get_status(),
           Lp.playlists.get_position(Type.MPD,
                                     Lp.player.current_track.id),
           songid,
           int(elapsed),
           time,
           elapsed)
        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _sticker(self, args_array, list_ok):
        """
            Send stickers
            @param args as [str]
            @param add list_OK as bool
        """
        args = self._get_args(args_array[0])
        msg = ""
        if args[0].find("get song ") != -1 and\
                args[2].find("rating") != -1:
            track_id = Lp.tracks.get_id_by_path(args[1])
            track = Track(track_id)
            msg = "sticker: rating=%s\n" % int(track.get_popularity()*2)
        elif args[0].find("set song") != -1 and\
                args[2].find("rating") != -1:
            track_id = Lp.tracks.get_id_by_path(args[1])
            track = Track(track_id)
            track.set_popularity(int(args[3])/2)
        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _stop(self, args_array, list_ok):
        """
            Stop player
            @param args as [str]
            @param add list_OK as bool
        """
        GLib.idle_add(Lp.player.stop)

    def _tagtypes(self, args_array, list_ok):
        """
            Send available tags
            @param args as [str]
            @param add list_OK as bool
        """
        msg = "tagtype: Artist\ntagtype: Album\ntagtype: Title\
\ntagtype: Track\ntagtype: Name\ntagtype: Genre\ntagtype: Date\
\ntagtype: Performer\ntagtype: Disc\n"
        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _update(self, args_array, list_ok):
        """
            Update database
            @param args as [str]
            @param add list_OK as bool
        """
        Lp.window.update_db()
        self._send_msg()

    def _urlhandlers(self, args_array, list_ok):
        """
            Send url handlers
            @param args as [str]
            @param add list_OK as bool
        """
        msg = "handler: http\n"
        if list_ok:
            msg += "list_OK\n"
        self._send_msg(msg)

    def _string_for_track_id(self, track_id):
        """
            Get mpd protocol string for track id
            @param track id as int
            @return str
        """
        if track_id is None:
            msg = ""
        else:
            track = Track(track_id)
            msg = "file: %s\nArtist: %s\nAlbum: %s\nAlbumArtist: %s\
\nTitle: %s\nDate: %s\nGenre: %s\nTime: %s\nId: %s\nPos: %s\n" % (
                     track.path,
                     track.artist,
                     track.album.name,
                     track.album_artist,
                     track.name,
                     track.year,
                     track.genre,
                     track.duration,
                     track.id,
                     track.position)
        return msg

    def _get_status(self):
        """
            Player status
            @return str
        """
        state = Lp.player.get_status()
        if state == Gst.State.PLAYING:
            return 'play'
        elif state == Gst.State.PAUSED:
            return 'pause'
        else:
            return 'stop'

    def _get_args(self, args):
        """
            Get args from string
            @param args as str
            @return args as [str]
        """
        splited = args.split('"')
        ret = []
        for arg in splited:
            if len(arg.replace(' ', '')) == 0:
                continue
            ret.append(arg)
        return ret

    def _send_msg(self, msg=''):
        """
            Send message to client
            @msg as string
        """
        msg += "OK\n"
        self.request.send(msg.encode("utf-8"))
        print(msg.encode("utf-8"))

    def _on_player_changed(self, player, data=None):
        """
            Add player to idle
            @param player as Player
        """
        self._current_song = None
        self._idle_strings.append("player")

    def _on_playlist_changed(self, playlists, playlist_id):
        """
            Add playlist to idle if mpd
            @param playlists as Playlist
            @param playlist id as int
        """
        if playlist_id == Type.MPD:
            self._idle_strings.append("playlist")
            self._playlist_version += 1


class MpdServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
        Create a MPD server.
    """

    def __init__(self, port=6600):
        """
            Init server
        """
        socketserver.TCPServer.allow_reuse_address = True
        socketserver.TCPServer.__init__(self, ("", port), MpdHandler)

    def run(self):
        """
            Run MPD server in a blocking way.
        """
        self.serve_forever()


class MpdServerDaemon(MpdServer):
    """
        Create a deamonized MPD server
    """
    def __init__(self, port=6600):
        """
            Init daemon
        """
        MpdServer.__init__(self, port)
        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.setDaemon(True)
        self.thread.start()

    def quit(self):
        """
            Stop MPD server deamon
        """
        self.running = False
        self.shutdown()
