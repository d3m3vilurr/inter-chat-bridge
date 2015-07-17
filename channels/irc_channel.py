import irc.client
import threading
import time


class Room(object):
    def fetch_messages(self):
        pass

    def send_message(self, sender, message):
        pass

    def users(self):
        pass

class IRCRoom(Room):
    def __init__(self, connection, roomid):
        self.queue = []
        self.conn = connection
        self.roomid = roomid

    def fetch_messages(self):
        # flush
        msgs = self.queue
        self.queue = []
        return msgs

    def append_message(self, sender, message):
        self.queue.append((sender, message))

    def send_message(self, sender, message):
        self.conn.privmsg(self.roomid,
                          ('<%s> %s' % (sender, message)))

class IRCThread(threading.Thread):

    def __init__(self, host, port=6667, nickname='bridge'):
        super(IRCThread, self).__init__()
        self.reactor = irc.client.Reactor()
        self.ready = False
        server = self.reactor.server()
        self.client = server.connect(host, int(port), nickname)
        self.reactor.add_global_handler('all_events', self.handle, -10)
        self.rooms = {}

    def handle(self, connection, event):
        #print event.type, event.arguments, event.target, event.source
        if event.type == 'welcome':
            self.ready = True
        #print event, dir(event)
        if event.type == 'pubmsg':
            room = self.rooms.get(event.target, None)
            if not room:
                # ignore not joined room message
                return
            message = event.arguments[0]
            room.append_message(event.source, message)

    def command(self, command, *args):
        while not self.ready:
            time.sleep(1)
        if command == 'join':
            rooms = {}
            for roomid in args:
                self.client.join(roomid)
                self.rooms[roomid] = IRCRoom(self.client, roomid)
                rooms[roomid] = self.rooms[roomid]
            return rooms

    def run(self):
        self.reactor.process_forever()


class IRC(irc.client.SimpleIRCClient):

    def __init__(self, host, port=6667, nickname='bridge'):
        self.client = IRCThread(host, port, nickname)
        self.client.start()

    def join(self, roomid):
        rets = self.client.command('join', roomid)
        return rets[roomid]

if __name__ == '__main__':
    server = IRC('172.16.25.10', 6667)
    room = server.join('#test')
    while True:
        messages = room.fetch_messages()
        if not messages:
            time.sleep(10)
        for x in messages:
            room.send_message('testman', x)
