import irc.client
import time
from channels import Channel, Room


def chunks(s, n):
    """
    http://stackoverflow.com/a/6044299
    """
    assert n >= 4
    start = 0
    lens = len(s)
    while start < lens:
        if lens - start <= n:
            yield s[start:]
            return # StopIteration
        end = start + n
        while '\x80' <= s[end] <= '\xBF':
            end -= 1
        assert end > start
        yield s[start:end]
        start = end


class IRCRoom(Room):
    def __init__(self, connection, roomid):
        self.queue = []
        self.conn = connection
        self.roomid = roomid
        # PRIVMSG #CHAN_NAME :MSGMSG\r\n
        self.privmsg_length = 12 + len(self.roomid.encode('utf-8'))

    def append_message(self, sender, message):
        self.queue.append((sender, message))

    def send_message(self, sender, message):
        # IRC line must be 512 bytes.
        # One UTF-8 character can be 1~4 bytes
        sender_length = len(sender.encode('utf-8'))
        line_limit = 512 - self.privmsg_length - (sender_length + 3)
        for line in message.split(u'\n'):
            line = line.rstrip().encode('utf-8')
            for c in chunks(line, line_limit):
                self.conn.privmsg(self.roomid,
                                  ('<%s> %s' % (sender, c.decode('utf-8'))))


class IRC(Channel):
    def __init__(self, host, port=6667, nickname='bridge'):
        super(IRC, self).__init__()
        self.reactor = irc.client.Reactor()
        self.ready = False
        server = self.reactor.server()
        self.client = server.connect(host, int(port), nickname)
        self.reactor.add_global_handler('all_events', self.handle, -10)
        self.rooms = {}
        self.future = self.executor.submit(self.reactor.process_forever)

    def handle(self, connection, event):
        #print(event.type, event.arguments, event.target, event.source)
        if event.type == 'welcome':
            self.ready = True
        #print(event, dir(event))
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
