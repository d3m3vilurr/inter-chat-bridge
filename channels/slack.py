from slackclient import SlackClient
import re
import HTMLParser
from channels import Channel, Room

USER_REGEX = re.compile('(<@([a-zA-Z0-9]+)(|[^>]+)?>)')
ROOM_REGEX = re.compile('(<#([_-a-zA-Z0-9]+)(|[^>]+)?>)')
URL_REGEX = re.compile('(<([^>|]+)(|[^>]+)?>)')

unescape = HTMLParser.HTMLParser().unescape

class SlackRoom(Room):

    def __init__(self, slack, channel):
        self.slack = slack
        self.channel = channel
        self.lastid = None
        self.queue = []

    def fetch_messages(self):
        self.slack.fetch_messages()
        return super(SlackRoom, self).fetch_messages()

    def append_message(self, sender, message):
        user = self.slack.client.server.users.find(sender)
        if user:
            sender = user.name
        for t, m, _ in USER_REGEX.findall(message):
            _ = self.slack.client.server.users.find(m)
            if _:
                m = '@' + _.name
            message = message.replace(t, m)
        for t, c, _ in ROOM_REGEX.findall(message):
            _ = self.slack.client.server.channels.find(c)
            if _:
                c = '#' + _.name
            message = message.replace(t, c)
        for t, u, a in URL_REGEX.findall(message):
            message = message.replace(t, u + ' ' + a)
        message = unescape(message)
        self.queue.append((sender, message))

    def send_message(self, sender, message):
        self.slack.client.rtm_send_message(self.channel.id, message)

class Slack(Channel):
    def __init__(self, token):
        self.client = SlackClient(token)
        self.rooms = {}
        self.reconnect()
        #self.ignore = self.client.server.users.find(self.client.server.username).id
        self.ignore = ''

    def reconnect(self):
        return self.client.rtm_connect()

    def join(self, roomname):
        channel = self.client.server.channels.find(roomname)
        if not channel:
            return
        room = self.rooms[channel.id] = SlackRoom(self, channel)
        return room

    def alive(self):
        if not self.client.server.websocket.connected:
            self.reconnect()
        return self.client.server.websocket.connected

    def fetch_messages(self):
        while True:
            msgs = self.client.rtm_read()
            if not len(msgs):
                break
            for msg in msgs:
                if not msg.get('type'):
                    continue
                if msg['type'] == 'hello':
                    continue
                if msg['type'] == 'presence_change':
                    continue
                if msg['type'] == 'reconnect_url':
                    continue
                if msg['type'] == 'message':
                    room = self.rooms.get(msg['channel'])
                    if not room:
                        continue
                    #print 'DEBUG_SLACK_MSG', msg
                    user = msg.get('user') or msg.get('username') or \
                           msg.get('comment', {}).get('user') or '_'
                    if user == self.ignore:
                        continue
                    room.append_message(user, msg.get('text', ''))
                else:
                    print 'UNKNOWN_SLACK_MSG', msg

    def close(self):
        pass
