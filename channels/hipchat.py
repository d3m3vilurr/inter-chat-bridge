import requests
try:
    import simplejson as json
except ImportError:
    import json

HIPCHAT_API = 'https://api.hipchat.com/v2/'


class Room(object):
    pass


class HipchatRoom(Room):

    def __init__(self, hipchat, roomid):
        self.hipchat = hipchat
        self.roomid = roomid
        self.lastid = None
        self.ignore = []
        self.fetch_messages()

    def fetch_messages(self):
        api = '/'.join(['room', self.roomid, 'history'])
        api_result = self.hipchat.get(api)
        messages = api_result.get('items', [])
        if self.lastid:
            for idx, message in enumerate(messages):
                if message['id'] == self.lastid:
                    messages = messages[idx + 1:]
                    break
        messages = filter(lambda x: x['id'] not in self.ignore, messages)
        if messages:
            self.lastid = messages[-1]['id']
        ret = []
        for msg in messages:
            if type(msg['from']) == unicode:
                name = msg['from']
            else:
                name = msg['from'].get('mention_name', None) or \
                       msg['from'].get('name', 'UNKNOWN')
            if name in self.hipchat.ignores:
                continue
            ret.append((name, msg['message']))
        self.ignore = []
        return ret

    def send_message(self, sender, message):
        api = '/'.join(['room', self.roomid, 'message'])
        api_result = self.hipchat.post(api, data={'message': message})
        self.ignore.append(api_result['id'])

    def users(self):
        api = '/'.join(['room', self.roomid, 'member'])
        api_result = self.hipchat.get(api, params={'max-results': 1000})
        users = [(x['id'], x['mention_name'], x['name']) for x in api_result.get('items', [])]
        return users

class Hipchat(object):
    def __init__(self, token, ignores=None):
        self.token = token
        self.ignores = ignores or []

    def get(self, api, params=None):
        if not params:
            params = dict()
        params['auth_token'] = self.token
        url = HIPCHAT_API + api
        ret = requests.get(url, params=params)
        if ret.status_code == 200:
            data = json.loads(ret.text)
            return data
        if ret.status_code == 429:
            print 'exceed api limit'
        raise Exception

    def post(self, api, data=None, params=None):
        if not params:
            params = dict()
        params['auth_token'] = self.token
        if not data:
            data = dict()
        url = HIPCHAT_API + api
        ret = requests.post(url, params=params, data=json.dumps(data),
                            headers={'Content-Type': 'application/json'})
        if ret.status_code >= 200 and ret.status_code < 300:
            data = json.loads(ret.text)
            return data
        raise Exception

    def rooms(self):
        api_result = self.get('/room', params={'max-results': 1000})
        rooms = [(x['id'], x['name']) for x in api_result.get('items', [])]
        return rooms

    def users(self):
        api_result = self.get('/user', params={'max-results': 1000})
        users = [(x['id'], x['mention_name'], x['name']) for x in api_result.get('items', [])]
        return users

    def join(self, roomid):
        return HipchatRoom(self, str(roomid))
