class Room(object):
    def fetch_messages(self):
        # flush
        msgs = self.queue
        self.queue = []
        return msgs

    def send_message(self, sender, message):
        pass

    def users(self):
        pass


class Channel(object):
    def __init__(self):
        super(Channel, self).__init__()
        self.connected = True

    def join(self, roomid):
        pass

    def close(self):
        pass

