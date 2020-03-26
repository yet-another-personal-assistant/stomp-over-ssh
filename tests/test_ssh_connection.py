import unittest

import stomp

from sshstomp import SshBasedConnection


class SshConnectionTest(unittest.TestCase):

    def test_create(self):
        conn = SshBasedConnection("localhost",
                                  12345,
                                  "username",
                                  "files/test.key",
                                  heartbeats=(120000, 180000),
                                  auto_content_length=True,
                                  heart_beat_receive_scale=1.5)

        self.assertIsInstance(conn, stomp.Connection12)

    def test_create_defaults(self):
        SshBasedConnection("localhost",
                           12345,
                           "username",
                           "files/test.key")
