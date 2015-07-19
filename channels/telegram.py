import thread
from pytg import Telegram as CLI
from pytg.utils import coroutine
from channels import Channel, Room


class TencentRoom(Room):
    def __init__(self, sender, roomid):
        self.queue = []
        self.sender = sender
        self.roomid = roomid

    def append_message(self, sender, message):
        self.queue.append((sender, message))

    def send_message(self, sender, message):
        self.sender.send_msg(self.roomid, message)


class Telegram(Channel):
    def __init__(self, cli, key):
        self.rooms = {}
        self.cli = CLI(telegram=cli, pubkey_file=key)
        self.cli.receiver.start()
        thread.start_new_thread(self.cli.receiver.message,
                                (self.handle(self.cli.sender),))

    @coroutine
    def handle(self, sender):
        while True:
            msg = (yield)
            sender.status_online()
            #print 'dump', msg
            if msg.event != 'message':
                continue
            if msg.own:
                # prevent echo message
                continue
            s = msg.sender
            username = s.get('username', None) \
                    or s.get('print_name', None) \
                    or '_'.join((s.first_name, s.last_name))
            print 'sender', username
            print 'event', msg.event
            print 'receiver', msg.receiver.cmd
            room = self.rooms.get(msg.receiver.cmd, None)
            if not room:
                continue
            if msg.get('media', None):
                print 'media', msg.media.type
                print 'media download not support yet'
                print msg.id
                #if msg.media.type == 'photo':
                #    print self.cli.sender.load_photo(msg.id)
                #    {u'result': u'/home/d3m3vilurr/.telegram-cli/downloads/download_702222016_26560.jpg', u'event': u'download'}
                #if msg.media.type == 'document':
                #    print self.cli.sender.load_document(msg.id)
                #...
                room.append_message(username, 'send media data ' + msg.media.type)
            else:
                room.append_message(username, msg.text)

    def join(self, roomid):
        room = self.rooms[roomid] = TencentRoom(self.cli.sender, str(roomid))
        return room

    def close(self):
        self.cli.receiver.stop()
