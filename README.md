# Inter chat service bridge

## How to use
```bash
git clone https://github.com/d3m3vilurr/inter-chat-bridge.git
cd inter-chat-bridge
cp config.yml.sample config.yml
vi config.yml
python bridge.py
```

## Channels
Support these channels

### IRC
```bash
pip install irc
```

### Hipchat
```bash
pip install hippybot
pip install https://github.com/normanr/xmpppy/archive/master.tar.gz --upgrade
```
Old `xmpppy` was not work on to python 2.7.9.
Check issue 1stvamp/hippybot#18

### Telegram
```bash
pip install https://github.com/luckydonald/pytg/archive/master.tar.gz
```
`pytg` require installed [telegrem-cli](https://github.com/vysheng/tg)

You need chat room's id. `chat_info` command will print this.
