# coding: utf8
import hippybot.bot
import thread
import time
import xmpp
from channels import Channel, Room

class HipchatRoom(Room):
    def __init__(self, hippy, roomid):
        self.queue = []
        self.hippy = hippy
        self.roomid = roomid

    def append_message(self, sender, message):
        self.queue.append((sender, message))

    def send_message(self, sender, message):
        #print sender, message
        self.hippy.send(self.roomid, message, message_type='groupchat')


class HippyBot(hippybot.bot.HippyBot):

    def __init__(self, config):
        super(HippyBot, self).__init__(config)

    def _idle_ping(self):
        # copy from jabberbot
        if self.PING_FREQUENCY \
            and time.time() - self._last_send_time > self.PING_FREQUENCY:
            self._last_send_time = time.time()
            #logging.debug('Pinging the server.')
            ping = xmpp.Protocol('iq', typ='get', \
                                 payload=[xmpp.Node('ping', attrs={'xmlns':'urn:xmpp:ping'})])
            try:
                res = self.conn.SendAndWaitForResponse(ping, self.PING_TIMEOUT)
                print res
                #logging.debug('Got response: ' + str(res))
                if res is None:
                    self.on_ping_timeout()
            except IOError, e:
                #logging.error('Error pinging the server: %s, '\
                #              'treating as ping timeout.' % e)
                self.on_ping_timeout()

    def on_ping_timeout(self):
        self.quit()
        raise IOError('hipchat disconnected')


class Hipchat(Channel):
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
        self.hippy = HippyBot(config)
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
