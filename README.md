# stomp-param-py!

This is a service for transferring messages using stomp protocol over
ssh connection. It assumes that the accepting part of the ssh
connection links directly into stomp server like this:

    socat STDIO,raw,echo=0 TCP:localhost:61613

## main.py

The main.py script is a basic listener that utilizes the transport. It
connects to the specified server and subscribes to 'brain' queue and
sends messages to 'tg' queue assuming it is a [telegram relay]
implementation.

### Custom components

The transport uses [modified stomp.py] module which fixes certain
heartbeat/reconnect issues. Testing uses [modified mock ssh server].

[telegram relay]: https://gitlab.com/personal-assistant-bot/infrastructure/pa-tg
[modified stomp.py]: https://github.com/aragaer/stomp.py/tree/heartbeat
[modified mock ssh server]: https://github.com/aragaer/mock-ssh-server/tree/shell
