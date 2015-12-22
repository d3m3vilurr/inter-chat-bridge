from concurrent.futures import ThreadPoolExecutor

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
        self.executor = ThreadPoolExecutor(max_workers=1)

    def join(self, roomid):
        pass

    def close(self):
        self.executor.shutdown(wait=False)

    def alive(self):
        return self.future.running()

    def result(self):
        # TODO executor clean up
        return self.future.result()
