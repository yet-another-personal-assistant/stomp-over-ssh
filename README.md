# stomp-over-ssh

# stomp-param-py!

This is a service for transferring messages using stomp protocol over ssh connection. It assumes that the accepting part of the ssh connection links directly into stomp server like this:

    socat STDIO,echo=0 TCP:localhost:61613