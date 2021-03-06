import os
import time
import yaml

def get_photo_service(config):
    photo_config = config.get('photo', {})
    if not photo_config.get('use'):
        return
    import photos
    return photos.Picasa(photo_config['account'],
                         photo_config['client_secret'],
                         photo_config['credentials_dat'])

def create_connections(config):
    photo_service = get_photo_service(config)
    connections = {}
    for k, v in config['connections'].items():
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
        elif v['type'] == 'telegram':
            from channels.telegram import Telegram
            connections[k] = Telegram(v['cli'], v['pubkey'], photo_service)
        elif v['type'] == 'slack':
            from channels.slack import Slack
            connections[k] = Slack(v['token'])
    return connections

def do_mapping(connections, config):
    bridges = []
    for mapping in config['bridge']:
        rooms = []
        bridges.append(rooms)
        for k, v in mapping.items():
            room = connections[k].join(v)
            if not room:
                continue
            rooms.append(room)
    return bridges

def mainloop(connections, bridges):
    try:
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
            for conn in connections.values():
                if conn.alive():
                    continue
                conn.result()
                raise IOError('some connection closed')
    except KeyboardInterrupt:
        print('interrupt')
        for conn in connections.values():
            conn.close()
    except Exception as e:
        print(e.args)
        print('die')
        for conn in connections.values():
            conn.close()
    except:
        print('die')
        for conn in connections.values():
            conn.close()

CONFIG_FILE = os.environ.get('INTER_CHAT_BRIDGE_CONF', 'config.yml')
with open(CONFIG_FILE) as r:
    config = yaml.safe_load(r)
    conns = create_connections(config)
    bridges = do_mapping(conns, config)
    mainloop(conns, bridges)
    # suicide
    time.sleep(1)
    os.kill(0, 9)
