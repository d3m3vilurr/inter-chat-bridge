import time
import yaml

with open('config.yml') as r:
    config = yaml.safe_load(r)
connections = {}
for k, v in config['connections'].iteritems():
    if v['type'] == 'irc':
        from channels.irc_channel import IRC
        connections[k] = IRC(v['host'], v['port'], v['nickname'])
    elif v['type'] == 'hipchat':
        from channels.hipchat import Hipchat
        connections[k] = Hipchat(v['token'], v.get('ignores'))
    elif v['type'] == 'hipchat_xmpp':
        from channels.hipchat_xmpp import Hipchat as HipchatXMPP
        connections[k] = HipchatXMPP(v['username'], v['password'],
                                     v['nickname'], v['default_room'])

bridges = []
for mapping in config['bridge']:
    rooms = []
    bridges.append(rooms)
    for k, v in mapping.iteritems():
        rooms.append(connections[k].join(v))

# mainloop
while True:
    time.sleep(1)
    for bridge in bridges:
        for room in bridge:
            for sender, message in room.fetch_messages():
                for receiver in bridge:
                    # prevent echo
                    if receiver == room:
                        continue
                    receiver.send_message(sender, message)