# coding: utf8
import hippybot.bot
import thread

class Room(object):
    pass


class HipchatRoom(Room):
    def __init__(self, hippy, roomid):
        self.queue = []
        self.hippy = hippy
        self.roomid = roomid

    def fetch_messages(self):
        # flush
        msgs = self.queue
        self.queue = []
        return msgs

    def append_message(self, sender, message):
        self.queue.append((sender, message))

    def send_message(self, sender, message):
        #print sender, message
        self.hippy.send(self.roomid, message, message_type='groupchat')

class Hipchat(object):
    def __init__(self, username, password, nickname, default_room):
        self.prefix = username.split('_')[0]
        self.nickname = nickname
        config = {
            'connection': {
                'username': username,
                'password': password,
                'host': u'conf.hipchat.com',
                'channels': default_room,
                'nickname': nickname,
            }
        }
        self.hippy = hippybot.bot.HippyBot(config)
        self.hippy._all_msg_handlers.append(self.handle)
        self.rooms = {}
        self.join(default_room, initialize=True)
        thread.start_new_thread(self.hippy.serve_forever, ())

    def handle(self, message):
        body = message.getBody()
        if not body:
            return
        channel = message.getFrom().getStripped()
        room = self.rooms.get(channel, None)
        # ignore not joined room message
        if not room:
            return
        sender = self.hippy.get_sender_username(message)
        # ignore echo message
        if sender == self.nickname:
            return
        room.append_message(sender, body)

    def get(self, api, params=None):
        pass

    def post(self, api, data=None, params=None):
        pass

    def rooms(self):
        api_result = self.get('/room', params={'max-results': 1000})
        rooms = [(x['id'], x['name']) for x in api_result.get('items', [])]
        return rooms

    def users(self):
        api_result = self.get('/user', params={'max-results': 1000})
        users = [(x['id'], x['mention_name'], x['name']) for x in api_result.get('items', [])]
        return users

    def join(self, roomid, initialize=False):
        channel = u'%s_%s@%s' % (self.prefix,
                                 roomid.strip().lower().replace(' ', '_'),
                                 'conf.hipchat.com')
        if not initialize:
            self.hippy.join_room(channel, self.nickname)
        room = HipchatRoom(self.hippy, channel)
        self.rooms[channel] = room
        return room

