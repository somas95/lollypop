# Copyright (c) 2014-2015 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# Copyright (C) 2011 kedals0@gmail.com
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


class MpdHandler(socketserver.BaseRequestHandler):
    def handle(self):
        """
            One function to handle them all
        """
        self._playlist_version = 0
        self._idle_strings = []
        self._signal1 = Lp.player.connect('current-changed',
                                          self._on_player_changed)
        self._signal2 = Lp.player.connect('seeked',
                                          self._on_player_changed)
        self._signal3 = Lp.playlists.connect('playlist-changed',
                                             self._on_playlist_changed)
        welcome = "OK MPD 0.19.0\n"
        self.request.send(welcome.encode('utf-8'))
        try:
            while self.server.running:
                msg = "OK\n"
                list_ok = False
                # sleep(1)
                data = self.request.recv(1024).decode('utf-8')
                # We check if we need to wait for a command_list_end
                data_ok = not data.startswith('command_list_begin')
                # We remove begin/end
                data = data.replace('command_list_begin\n', '')
                data = data.replace('command_list_end\n', '')
                while not data_ok:
                    data += self.request.recv(1024).decode('utf-8')
                    if data.endswith('command_list_end\n'):
                        data = data.replace('command_list_end\n', '')
                        data_ok = True
                if data != '':
                    if data.find('command_list_ok_begin') != -1:
                        list_ok = True
                        data = data.replace('command_list_ok_begin\n', '')
                    cmds = data.split('\n')

                    if cmds:
                        try:
                            if list_ok:
                                for cmd in cmds:
                                    command = cmd.split(' ')[0]
                                    if command != '':
                                        size = len(command) + 1
                                        call = getattr(self, '_%s' % command)
                                        args = cmd[size:]
                                        call([args], list_ok)
                            else:
                                args = []
                                command = cmds[0].split(' ')[0]
                                size = len(command) + 1
                                call = getattr(self, '_%s' % command)
                                for cmd in cmds:
                                    arg = cmd[size:]
                                    if arg != '':
                                        args.append(arg)
                                call(args, list_ok)
                        except Exception as e:
                            print("MpdHandler::handle(): ", cmd, e)
                self.request.send(msg.encode("utf-8"))
                self._idle_strings = []
        except Exception as e:
            print("MpdHandler::handle(): %s" % e)
        Lp.player.disconnect(self._signal1)
        Lp.player.disconnect(self._signal2)
        Lp.playlists.disconnect(self._signal3)

    def _add(self, args, list_ok):
        """
            Add track to mpd playlist
            @param args as [str]
            @param add list_OK as bool
        """
        tracks = []
        for arg in args:
            track_id = Lp.tracks.get_id_by_path(arg[1:-1])
            tracks.append(Track(track_id))
        Lp.playlists.add_tracks(Type.MPD, tracks)

    def _clear(self, args, list_ok):
        """
            Clear mpd playlist
            @param args as [str]
            @param add list_OK as bool
        """
        Lp.playlists.clear(Type.MPD, True)

    def _channels(self, args, list_ok):
        msg = ""
        if list_ok:
            msg += "list_OK\n"
        self.request.send(msg.encode("utf-8"))

    def _commands(self, args, list_ok):
        """
            Send available commands
            @param args as [str]
            @param add list_OK as bool
        """
        msg = "command: status\ncommand: stats\ncommand: playlistinfo\
\ncommand: idle\ncommand: currentsong\ncommand: lsinfo\ncommand: list\n"
        if list_ok:
            msg += "list_OK\n"
        self.request.send(msg.encode("utf-8"))

    def _currentsong(self, args, list_ok):
        """
            Send lollypop current song
            @param args as [str]
            @param add list_OK as bool
        """
        msg = self._string_for_track_id(Lp.player.current_track.id)
        if list_ok:
            msg += "list_OK\n"
        self.request.send(msg.encode("utf-8"))

    def _delete(self, args, list_ok):
        """
            Delete track from playlist
            @param args as [str]
            @param add list_OK as bool
        """
        for arg in args:
            tracks = []
            for track_id in Lp.playlists.get_tracks_ids(Type.MPD):
                tracks.append(Track(track_id))
            del tracks[int(arg[1:-1])]
            Lp.playlists.clear(Type.MPD, False)
            Lp.playlists.add_tracks(Type.MPD, tracks)

    def _idle(self, args, list_ok):
        self.request.settimeout(0)
        while not self._idle_strings:
            sleep(1)
        if self._idle_strings != Type.NONE:
            msg = ''
            for string in self._idle_strings:
                msg += "changed: %s\n" % string
            self.request.send(msg.encode("utf-8"))
        self.request.settimeout(10)

    def _noidle(self, args, list_ok):
        self._idle_strings = Type.NONE

    def _list(self, args, list_ok):
        """
            List objects
            @param args as [str]
            @param add list_OK as bool
        """
        # Should not happen as mutitple list should happen with list_ok==True
        for arg in args:
            msg = ""
            if arg == 'Album':
                results = Lp.albums.get_names()
                for name in results:
                    msg += 'Album: '+name+'\n'
            elif arg == 'Artist':
                results = Lp.artists.get_names()
                for name in results:
                    msg += 'Artist: '+name+'\n'
            elif arg == 'Genre':
                results = Lp.genres.get_names()
                for name in results:
                    msg += 'Genre: '+name+'\n'
            if list_ok:
                msg += "list_OK\n"
            self.request.send(msg.encode("utf-8"))

    def _listallinfo(self, args, list_ok):
        """
            List all tracks
            @param args as [str]
            @param add list_OK as bool
        """
        msg = ""
        i = 0
        for track_id in Lp.tracks.get_ids():
            msg += self._string_for_track_id(track_id)
            if i > 100:
                self.request.send(msg.encode("utf-8"))
                msg = ""
                i = 0
            i += 1
        if list_ok:
            msg += "list_OK\n"
        self.request.send(msg.encode("utf-8"))

    def _listplaylists(self, args, list_ok):
        """
            Send available playlists
            @param args as [str]
            @param add list_OK as bool
        """
        msg = "Main\n"
        if list_ok:
            msg += "list_OK\n"
        self.request.send(msg.encode("utf-8"))

    def _lsinfo(self, args, list_ok):
        """
            List directories and files
            @param args as [str]
            @param add list_OK as bool
        """
        for arg in args:
            msg = ""
            if arg == '""':
                results = Lp.genres.get()
                i = 0
                for (rowid, genre) in results:
                    msg += 'directory: '+genre+'\n'
                    if i > 100:
                        self.request.send(msg.encode("utf-8"))
                        msg = ""
                        i = 0
                    i += 1
            if list_ok:
                msg += "list_OK\n"
            self.request.send(msg.encode("utf-8"))

    def _next(self, args, list_ok):
        """
            Send output
            @param args as [str]
            @param add list_OK as bool
        """
        GLib.idle_add(Lp.player.next)

    def _outputs(self, args, list_ok):
        """
            Send output
            @param args as [str]
            @param add list_OK as bool
        """
        msg = "outputid: 0\noutputname: null\noutputenabled: 1\n"
        if list_ok:
            msg += "list_OK\n"
        self.request.send(msg.encode("utf-8"))

    def _play(self, args, list_ok):
        """
            Play track
            @param args as [str]
            @param add list_OK as bool
        """
        for arg in args:
            try:
                if Lp.player.get_user_playlist_id() != Type.MPD:
                    Lp.player.set_user_playlist(Type.MPD)
                track_id = Lp.player.get_user_playlist()[0]
                GLib.idle_add(Lp.player.load_in_playlist, track_id)
            except Exception as e:
                print("MpdHandler::_play(): %s" % e)

    def _playid(self, args, list_ok):
        """
            Play track
            @param args as [str]
            @param add list_OK as bool
        """
        try:
            for arg in args:
                if Lp.player.get_user_playlist_id() != Type.MPD:
                    Lp.player.set_user_playlist(Type.MPD)
                GLib.idle_add(Lp.player.load_in_playlist, int(arg[1:-1]))
        except Exception as e:
            print("MpdHandler::_playid(): %s" % e)

    def _playlistinfo(self, args, list_ok):
        """
            Send informations about playlists
            @param args as [str]
            @param add list_OK as bool
        """
        msg = ""
        for track_id in Lp.playlists.get_tracks_ids(Type.MPD):
            msg += self._string_for_track_id(track_id)
        if list_ok:
            msg += "list_OK\n"
        self.request.send(msg.encode("utf-8"))

    def _plchangesposid(self, args, list_ok):
        """
            Send informations about playlists
            @param args as [str]
            @param add list_OK as bool
        """
        msg = ""
        if list_ok:
            msg += "list_OK\n"
        self.request.send(msg.encode("utf-8"))

    def _prev(self, args, list_ok):
        """
            Send output
            @param args as [str]
            @param add list_OK as bool
        """
        GLib.idle_add(Lp.player.prev)

    def _replay_gain_status(self, args, list_ok):
        """
            Send output
            @param args as [str]
            @param add list_OK as bool
        """
        msg = "replay_gain_mode: off\n"
        if list_ok:
            msg += "list_OK\n"
        self.request.send(msg.encode("utf-8"))

    def _seekid(self, args, list_ok):
        """
            Send stats about db
            @param args as [str]
            @param add list_OK as bool
        """
        for arg in args:
            args = arg.split('"')
            track_id = int(args[1])
            seek = int(args[3])
            if track_id == Lp.player.current_track.id:
                GLib.idle_add(Lp.player.seek, seek)

    def _setvol(self, args, list_ok):
        """
            Send stats about db
            @param args as [str]
            @param add list_OK as bool
        """
        for arg in args:
            vol = float(arg[1:-1])
            Lp.player.set_volume(vol/100)

    def _stats(self, args, list_ok):
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
        self.request.send(msg.encode("utf-8"))

    def _status(self, args, list_ok):
        """
            Send lollypop status
            @param args as [str]
            @param add list_OK as bool
        """
        if Lp.player.is_playing():
            elapsed = Lp.player.get_position_in_track() / 1000000 / 60
            msg = "time: %s:%s\nelapsed: %s\n" % (
                int(elapsed),
                Lp.player.current_track.duration,
                elapsed)
            songid = Lp.player.current_track.id
        else:
            msg = ""
            songid = -1
        msg += "volume: %s\nrepeat: %s\nrandom: %s\
\nsingle: %s\nconsume: %s\nplaylist: %s\
\nplaylistlength: %s\nstate: %s\nsong: %s\
\nsongid: %s\n" % (
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
           songid)
        if list_ok:
            msg += "list_OK\n"
        self.request.send(msg.encode("utf-8"))

    def _sticker(self, args, list_ok):
        for arg in args:
            args_array = arg.split('"')
            msg = ""
            if args_array[0].find("get song ") != -1 and\
                    args_array[2].find("rating") != -1:
                track_id = Lp.tracks.get_id_by_path(args_array[1])
                track = Track(track_id)
                msg = "sticker: rating=%s\n" % int(track.get_popularity()*2)
            elif args_array[0].find("set song") != -1 and\
                    args_array[2].find("rating") != -1:
                track_id = Lp.tracks.get_id_by_path(args_array[1])
                track = Track(track_id)
                track.set_popularity(int(args_array[3])/2)
            if list_ok:
                msg += "list_OK\n"
            self.request.send(msg.encode("utf-8"))

    def _tagtypes(self, args, list_ok):
        """
            Send available tags
            @param args as [str]
            @param add list_OK as bool
        """
        msg = "tagtype: Artist\ntagtype: Album\ntagtype: Title\
\ntagype: Track\ntagtype: Name\ntagype: Genre\ntagtype: Data\
\ntagype: Performer\n"
        if list_ok:
            msg += "list_OK\n"
        self.request.send(msg.encode("utf-8"))

    def _update(self, args, list_ok):
        """
            Update database
            @param args as [str]
            @param add list_OK as bool
        """
        Lp.window.update_db()

    def _urlhandlers(self, args, list_ok):
        """
            Send url handlers
            @param args as [str]
            @param add list_OK as bool
        """
        msg = "handler: http\n"
        if list_ok:
            msg += "list_OK\n"
        self.request.send(msg.encode("utf-8"))

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

    def _on_player_changed(self, player, data=None):
        """
            Add player to idle
            @param player as Player
        """
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
