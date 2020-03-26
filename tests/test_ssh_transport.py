import unittest

import mockssh
import stomp

from sshstomp import SshBasedTransport


_USERS = {'username': 'files/test.key'}


class SshTransportTest(unittest.TestCase):

    def setUp(self):
        self.serv = mockssh.Server(_USERS)
        self.serv.__enter__()
        self.addCleanup(self.serv.__exit__)
        self.tr = SshBasedTransport("localhost", self.serv.port,
                                    "username", 'files/test.key')

    def test_create(self):
        self.assertFalse(self.tr.is_connected())

    def test_vhost(self):
        # stomp.py requires this parameter
        self.assertEqual(self.tr.vhost, f"username@localhost:{self.serv.port}")

    def test_send_not_connected(self):
        with self.assertRaises(stomp.exception.NotConnectedException):
            self.tr.send(b'echo hello, world')

    def test_connect(self):
        self.tr.attempt_connection()

        self.assertTrue(self.tr.is_connected())

        # stomp.py requires this parameter to be set after connection
        self.assertEqual(self.tr.current_host_and_port, ("localhost", self.serv.port))

    def test_send(self):
        self.tr.attempt_connection()

        data = b'echo hello, world'
        self.tr.send(data)

    def test_recv(self):
        self.tr.attempt_connection()
        self.tr.send(b'hello, world')

        result = self.tr.receive()

        self.assertEqual(result, b'hello, world')

    def test_cleanup(self):
        # only closes shell, doesn't disconnect the socket
        self.tr.attempt_connection()
        self.tr.send(b'hello, world')

        self.tr.cleanup()

        self.assertFalse(self.tr.is_connected())

        self.tr.attempt_connection()
        self.tr.send(b'yo')
        self.assertEqual(self.tr.receive(), b'yo')

    def test_disconnect(self):
        # disconnects the socket completely
        self.tr.attempt_connection()
        self.tr.send(b'hello, world')

        self.tr.disconnect_socket()

        self.assertFalse(self.tr.is_connected())

        self.tr.attempt_connection()
        self.tr.send(b'yo')
        self.assertEqual(self.tr.receive(), b'yo')
