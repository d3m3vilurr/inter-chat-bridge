import thread
from pytg import Telegram as CLI
from pytg.utils import coroutine
from pytg.exceptions import IllegalResponseException
from channels import Channel, Room


class TelegramRoom(Room):
    def __init__(self, sender, roomid):
        self.queue = []
        self.sender = sender
        self.roomid = roomid

    def append_message(self, sender, message):
        self.queue.append((sender, message))

    def send_message(self, sender, message):
        self.sender.send_msg(self.roomid, message)


class Telegram(Channel):
    def __init__(self, cli, key, photo_service):
        super(Telegram, self).__init__()
        self.rooms = {}
        self.photo_service = photo_service
        self.cli = CLI(telegram=cli, pubkey_file=key)
        self.cli.receiver.start()
        thread.start_new_thread(self.cli.receiver.message,
                                (self.handle(self.cli.sender),))

    @coroutine
    def handle(self, sender):
        while True:
            msg = (yield)
            try:
                sender.status_online()
            except IllegalResponseException:
                print 'status_online raised exception'
            #print 'dump', msg
            if msg.event != 'message':
                continue
            if msg.own:
                # prevent echo message
                continue
            s = msg.sender
            username = s.get('username', None) \
                    or s.get('print_name', None) \
                    or '_'.join(filter(None, (s.first_name, s.last_name)))
            #print 'sender', username
            #print 'event', msg.event
            #print 'receiver', msg.receiver.cmd
            room = self.rooms.get(msg.receiver.cmd, None)
            if not room:
                continue
            if msg.get('text', None):
                room.append_message(username, msg.text)
            elif msg.get('media', None):
                if not self.photo_service:
                    print 'disabled photo_service'
                    print msg
                    room.append_message(username, 'send media data: ' + msg.media.type)
                    continue
                if msg.media.type == 'photo':
                    photo = self.cli.sender.load_photo(msg.id)
                    photo_url = self.photo_service.post(photo['result'],
                                                        room.roomid)
                    room.append_message(username, photo_url)
                    continue
                #if msg.media.type == 'document':
                #    print self.cli.sender.load_document(msg.id)
                #...
                print msg
                room.append_message(username, 'send media data: ' + msg.media.type)
            else:
                print msg
                room.append_message(username, 'send unknown type message')

    def join(self, roomid):
        room = self.rooms[roomid] = TelegramRoom(self.cli.sender, str(roomid))
        return room

    def close(self):
        self.cli.stopCLI()
