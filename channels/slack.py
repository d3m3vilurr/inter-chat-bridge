from slackclient import SlackClient
import re
import HTMLParser
import cgi
from channels import Channel, Room

SEND_USER_REGEX = re.compile('(@([a-zA-Z0-9]+))')
SEND_ROOM_REGEX = re.compile('(#([_\-a-zA-Z0-9]+))')
RECV_USER_REGEX = re.compile('(<@([a-zA-Z0-9]+)(|[^>]+)?>)')
RECV_ROOM_REGEX = re.compile('(<#([_\-a-zA-Z0-9]+)(|[^>]+)?>)')
RECV_URL_REGEX = re.compile('(<([^>|]+)(|[^>]+)?>)')

escape = cgi.escape
unescape = HTMLParser.HTMLParser().unescape

def to_send_format(msg, pattern, process):
    tmp = msg
    buf = []
    while True:
        s = pattern.split(tmp, maxsplit=1)
        if not len(s):
            break
        if len(s) == 1:
            buf.append(s[0])
            break
        r = process(s[2])
        if r != s[1]:
            r = '<' + r + '>'
        buf += [s[0], r]
        tmp = s[3]
    return ''.join(buf)

class SlackRoom(Room):

    def __init__(self, slack, channel):
        self.slack = slack
        self.channel = channel
        self.lastid = None
        self.queue = []

    def find_userid(self, username):
        _ = self.slack.client.server.users.find(username)
        return '@' + (_ and _.id or username)
    def find_username(self, userid):
        _ = self.slack.client.server.users.find(userid)
        return '@' + (_ and _.name or userid)

    def find_roomid(self, roomname):
        _ = self.slack.client.server.channels.find(roomname)
        return '#' + (_ and _.id or roomname)

    def find_roomname(self, roomid):
        _ = self.slack.client.server.channels.find(roomid)
        return '#' + (_ and _.name or roomid)

    def fetch_messages(self):
        self.slack.fetch_messages()
        return super(SlackRoom, self).fetch_messages()

    def append_message(self, sender, message, orig_data):
        user = self.slack.client.server.users.find(sender)
        if user:
            sender = user.name
        for t, m, _ in RECV_USER_REGEX.findall(message):
            m = self.find_username(m)
            message = message.replace(t, m)
        for t, c, _ in RECV_ROOM_REGEX.findall(message):
            c = self.find_roomname(c)
            message = message.replace(t, c)
        for t, u, a in RECV_URL_REGEX.findall(message):
            if orig_data.get('subtype'):
                if orig_data['subtype'] == 'file_share' and \
                        orig_data.get('file'):
                    file_data = orig_data['file']
                    u = file_data.get('url_private') or \
                            file_data.get('url_private_download') or \
                            u
            message = message.replace(t, u + ' ' + a)
        message = unescape(message)
        self.queue.append((sender, message))

    def send_message(self, sender, message):
        message = escape(message)
        message = to_send_format(message, SEND_USER_REGEX, self.find_userid)
        message = to_send_format(message, SEND_ROOM_REGEX, self.find_roomid)
        #print 'DEBUG_SLACK_SEND_MSG', message
        self.slack.client.rtm_send_message(self.channel.id, message)

class Slack(Channel):
    def __init__(self, token):
        self.client = SlackClient(token)
        self.rooms = {}
        self.reconnect()
        self.ignore = self.client.server.users.find(self.client.server.username).id

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
                    #print 'DEBUG_SLACK_RECV_MSG', msg
                    user = msg.get('user') or msg.get('username') or \
                           msg.get('comment', {}).get('user') or '_'
                    if user == self.ignore:
                        continue
                    room.append_message(user, msg.get('text', ''), msg)
                else:
                    print 'UNKNOWN_SLACK_RECV_MSG', msg

    def close(self):
        pass
