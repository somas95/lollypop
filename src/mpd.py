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

import socketserver
import threading

from lollypop.define import Lp
from lollypop.objects import Track

from time import sleep


class MpdHandler(socketserver.BaseRequestHandler):
    def handle(self):
        """
            One function to handle them all
        """
        welcome = "OK MPD 0.19.0\n"
        self.request.send(welcome.encode('utf-8'))
        try:
            while True:
                msg = ''
                cmds = []
                list_ok = False
                sleep(1)
                data = self.request.recv(1024).decode('utf-8')
                print("data: ", data)
                if data == '':
                    return
                commands = data.strip().split('\n')

                for cmd in commands:
                    if cmd == 'command_list_ok_begin':
                        list_ok = True
                    elif cmd not in ['command_list_begin',
                                     'command_list_end']:
                        cmds.append(cmd)
                if cmds:
                    for cmd in cmds:
                        try:
                            command = cmd.split(' ')
                            call = getattr(self, '_%s' % command[0])
                            if len(command) > 1:
                                args = command[1:]
                            else:
                                args = None
                            msg += call(args)
                            if list_ok:
                                msg += "list_OK\n"
                        except Exception as e:
                            print("Unknown: ", cmd, e)
                    msg += "OK\n"
                    print(msg.encode("utf-8"))
                    self.request.send(msg.encode("utf-8"))
        except IOError:
            print('fin')

    def _commands(self, args):
        """
            Return availables command
            @param args as [str]
            @return str
        """
        return "command: status\ncommand: stats\ncommand: playlistinfo\
\ncommand: idle\ncommand: currentsong\ncommand: lsinfo\ncommand: list\n"

    def _status(self, args):
        """
            Return lollypop status
            @param args as [str]
            @return str
        """
        return "volume: %s\nrepeat: %s\nrandom: %s\
\nsingle: %s\nconsume: %s\n" % (int(Lp.player.get_volume()*100),
                                1,
                                int(Lp.player.is_party()),
                                1,
                                1)

    def _playlistinfo(self, args):
        """
            Return informations about playlists
            @param args as [str]
            @return str
        """
        return ''

    def _urlhandlers(self, args):
        """
            Return url handlers
            @param args as [str]
            @return str
        """
        return "handler: http\n"

    def _tagtypes(self, args):
        """
            Return available tags
            @param args as [str]
            @return str
        """
        return "tagtype: Artist\ntagtype: Album\ntagtype: Title\
\ntagype: Track\ntagtype: Name\ntagype: Genre\ntagtype: Data\
\ntagype: Performer\n"

    def _idle(self, args):
        print(args)
        return ''

    def _stats(self, args):
        """
            Return stats about db
            @param args as [str]
            @return str
        """
        sql = Lp.db.get_cursor()
        artists = Lp.artists.count(sql)
        albums = Lp.albums.count(sql)
        tracks = Lp.tracks.count(sql)
        sql.close()
        return "artists: %s\nalbums: %s\nsongs: %s\nuptime: 0\
\nplaytime: 0\ndb_playtime: 0\ndb_update: 0\n" % \
            (artists, albums, tracks)

    def _channels(self, args):
        return ''

    def _currentsong(self, args):
        """
            Return lollypop current song
            @param args as [str]
            @return str
        """
        return "playlist: 1\nplaylistlength: 0\nmixrampdb: 0\nstate: stop\n"

    def _lsinfo(self, args):
        """
            List directories and files
            @param args as [str]
            @return str
        """
        entries = ''
        if args[0] == '""':
            sql = Lp.db.get_cursor()
            results = Lp.genres.get(sql)
            for (rowid, genre) in results:
                entries += 'directory: '+genre+'\n'
            sql.close()
        return entries

    def _listplaylists(self, args):
        """
            Return available playlists
            @param args as [str]
            @return str
        """
        return "Main\n"

    def _outputs(self, args):
        """
            Return output
            @param args as [str]
            @return str
        """
        return "outputid: 0\noutputname: null\noutputenabled: 1\n"

    def _listallinfo(self, args):
        """
            List all tracks
            @param args as [str]
            @return str
        """
        sql = Lp.db.get_cursor()
        entries = ''
        for track_id in Lp.tracks.get_ids(sql):
            track = Track(track_id)
            entries += "file: %s\nArtist: %s\nAlbumArtist: %s\
\nTitle= %s\nDate: %s\nGenre: %s\n" %\
                (track.path,
                 track.artist,
                 track.album_artist,
                 track.title,
                 track.year,
                 track.genre)

    def _list(self, args):
        """
            List objects
            @param args as [str]
            @return str
        """
        entries = ''
        if args[0] == 'Album':
            sql = Lp.db.get_cursor()
            results = Lp.albums.get_names(sql)
            sql.close()
            for name in results:
                entries += 'Album: '+name+'\n'
        elif args[0] == 'Artist':
            sql = Lp.db.get_cursor()
            results = Lp.artists.get_names(sql)
            sql.close()
            for name in results:
                entries += 'Artist: '+name+'\n'
        elif args[0] == 'Genre':
            sql = Lp.db.get_cursor()
            results = Lp.genres.get_names(sql)
            sql.close()
            for name in results:
                entries += 'Genre: '+name+'\n'
        return entries


class MpdServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
        Create a MPD server.
    """

    def __init__(self, port=6600):
        """
            Init server
        """
        socketserver.TCPServer.allow_reuse_address = True
        socketserver.TCPServer.__init__(self, ("localhost", port), MpdHandler)

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
        self.thread = threading.Thread(target=self.run)
        self.thread.setDaemon(True)
        self.thread.start()

    def quit(self):
        """
            Stop MPD server deamon
        """
        self.shutdown()
