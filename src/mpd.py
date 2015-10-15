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


class MpdHandler(socketserver.BaseRequestHandler):
    def handle(self):
        """
            One function to handle them all
        """
        welcome = "OK MPD 0.20.0\n"
        self.request.send(welcome.encode('utf-8'))
        while True:
            try:
                msg = ''
                cmds = []
                data_ok = False
                list_ok = False
                while not data_ok:
                    data = self.request.recv(1024).decode('utf-8')
                    if data == '':
                        break
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
                            call = getattr(self, '_%s' % cmd)
                            msg += call() + '\n'
                            if list_ok:
                                msg += "list_OK\n"
                        except:
                            pass
                    msg += "OK\n"
                    print(msg.encode("utf-8"))
                    self.request.send(msg.encode("utf-8"))
            except IOError:
                print('fin')
                break

    def _status(self):
        return "volume: 0 repeat: 0 random: 0 single: 0 consume: 0"

    def _currentsong(self):
        return "playlist: 1 playlistlength: 0 mixrampdb: 0 state: stop"


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
