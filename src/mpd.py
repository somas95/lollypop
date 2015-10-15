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


class MpdHandler(socketserver.BaseRequestHandler):
    def handle(self):
        """
            One function to handle them all
        """
        welcome = "OK MPD 0.19.0\n"
        self.request.send(welcome.encode('utf-8'))
        try:
            msg = ''
            cmds = []
            data_ok = False
            list_ok = False
            while not data_ok:
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
                if len(data) < 1024:
                    data_ok = True
            if cmds:
                for cmd in cmds:
                    try:
                        command = cmd.split(' ')
                        print(command)
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

    def _status(self, args):
        """
            Return lollypop status
            @param args as [str]
        """
        return "volume: %s\nrepeat: %s\nrandom: %s\
\nsingle: %s\nconsume: %s\n" % (int(Lp.player.get_volume()*100),
                                1,
                                int(Lp.player.is_party()),
                                1,
                                1)

    def _playlistinfo(self, args):
        return ''

    def _idle(self, args):
        return ''

    def _stats(self, args):
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
        """
        return "playlist: 1\nplaylistlength: 0\nmixrampdb: 0\nstate: stop\n"

    def _lsinfo(self, args):
        """
            List directories and files
            @param args as [str]
        """
        entries = ''
        if args[0] == '""':
            sql = Lp.db.get_cursor()
            results = Lp.genres.get(sql)
            for (rowid, genre) in results:
                entries += 'directory: '+genre+'\n'
            sql.close()
        return entries

    def _list(self, args):
        """
            List objects
            @param args as [str]
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
