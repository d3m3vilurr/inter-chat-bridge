import irc.client
import thread
import time
from channels import Channel, Room


def chunks(l, n):
    """Yield successive n-sized chunks from l.

    http://stackoverflow.com/a/312464
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


class IRCRoom(Room):
    def __init__(self, connection, roomid):
        self.queue = []
        self.conn = connection
        self.roomid = roomid

    def append_message(self, sender, message):
        self.queue.append((sender, message))

    def send_message(self, sender, message):
        # IRC line must be 512 bytes.
        # One UTF-8 character can be 1~4 bytes
        line_limit = 128 - (len(sender) + 3)
        for line in message.split('\n'):
            line = line.rstrip()
            for s in chunks(line, line_limit):
                self.conn.privmsg(self.roomid,
                                  ('<%s> %s' % (sender, s)))


class IRC(Channel):
    def __init__(self, host, port=6667, nickname='bridge'):
        self.reactor = irc.client.Reactor()
        self.ready = False
        server = self.reactor.server()
        self.client = server.connect(host, int(port), nickname)
        self.reactor.add_global_handler('all_events', self.handle, -10)
        self.rooms = {}
        thread.start_new_thread(self.reactor.process_forever, ())

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

    def join(self, roomid):
        if not self.ready:
            time.sleep(1)
        self.client.join(roomid)
        room = self.rooms[roomid] = IRCRoom(self.client, roomid)
        return room
