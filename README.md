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

### Configuration

./main.py script accepts the following command line arguments:


- `-c`, `--config`: configuration file (default /etc/sshstomp/sshstomp.conf)
- `-h`, `--host`: host of stomp server
- `-p`, `--port`: port of stomp server
- `-k`, `--key`: ssh key to use
- `-u`, `--user`: user name
- `--chat-id`: telegram chat_id where messages are sent by default
- `-o`, `--log-file`: file to write log
- `-d`, `--debug`: verbose debug output

Configuration file (if present) is an INI file with a single
`sshstomp` section which could contain the following parameters:

- `host`
- `port`
- `key`
- `user`
- `chat-id`
- `log-file`
- `debug`

These parameters mirror the command line arguments. If both
configuration file entry and command line parameter are present,
command line parameter overrides the configuration file.

`log-file` can be omitted, default behavior is not to write logs to
any file.  `debug` can be omitted, default behavior is to not print
debug messages. All other parameters have to be specified either in a
file or command line.

### Dumb bot implementation

The code currently implements a simple chat bot. All messages are sent
to ChatID specified in configuration unless stated otherwise.

#### Greeting message

The bot sends a greeting message when it is started.

#### Reconnect message

When connection is lost the bot sends a message about it after reconnection.

#### Random ping messages

The bot sends one of random messages with random intervals of about 1 hour.

#### "Don't understand" messages

When bot receives a message from telegram it replies with "Don't
understand" and "What is <quote>?" These messages are sent back to the
chat which was the source of initial message.

### Custom components

The transport uses [modified stomp.py] module which fixes certain
heartbeat/reconnect issues. Testing uses [modified mock ssh server].

[telegram relay]: https://gitlab.com/personal-assistant-bot/infrastructure/pa-tg
[modified stomp.py]: https://github.com/aragaer/stomp.py/tree/heartbeat
[modified mock ssh server]: https://github.com/aragaer/mock-ssh-server/tree/shell
