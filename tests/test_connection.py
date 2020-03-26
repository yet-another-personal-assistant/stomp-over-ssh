import unittest

import stomp

from sshstomp import SshBasedTransport, Connection


class ConnectionTest(unittest.TestCase):

    def test_create(self):
        tr = SshBasedTransport("localhost",
                               12345,
                               "username",
                               "files/test.key")
        conn = Connection(tr,
                          heartbeats=(120000, 180000),
                          auto_content_length=True,
                          heart_beat_receive_scale=1.5)

        self.assertIsInstance(conn, stomp.Connection12)

    def test_create_defaults(self):
        tr = SshBasedTransport("localhost",
                               12345,
                               "username",
                               "files/test.key")
        Connection(tr)
