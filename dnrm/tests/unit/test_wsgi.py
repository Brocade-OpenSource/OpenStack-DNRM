# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack Foundation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import socket
import urllib2

import mock
from oslo.config import cfg
import webob

from dnrm.tests import base
from dnrm import wsgi


CONF = cfg.CONF


TEST_VAR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
                               '..', 'var'))


class TestWSGIServer(base.BaseTestCase):
    """WSGI server tests."""

    def test_start_random_port(self):
        server = wsgi.Server("test_random_port")
        server.start(None, 0, host="127.0.0.1")
        self.assertNotEqual(0, server.port)
        server.stop()
        server.wait()

    def test_start_random_port_with_ipv6(self):
        server = wsgi.Server("test_random_port")
        server.start(None, 0, host="::1")
        self.assertEqual("::1", server.host)
        self.assertNotEqual(0, server.port)
        server.stop()
        server.wait()

    def test_ipv6_listen_called_with_scope(self):
        server = wsgi.Server("test_app")

        with mock.patch.object(wsgi.eventlet, 'listen') as mock_listen:
            with mock.patch.object(socket, 'getaddrinfo') as mock_get_addr:
                mock_get_addr.return_value = [
                    (socket.AF_INET6,
                     socket.SOCK_STREAM,
                     socket.IPPROTO_TCP,
                     '',
                     ('fe80::204:acff:fe96:da87%eth0', 1234, 0, 2))
                ]
                with mock.patch.object(server, 'pool') as mock_pool:
                    server.start(None,
                                 1234,
                                 host="fe80::204:acff:fe96:da87%eth0")

                    mock_get_addr.assert_called_once_with(
                        "fe80::204:acff:fe96:da87%eth0",
                        1234,
                        socket.AF_UNSPEC,
                        socket.SOCK_STREAM
                    )

                    mock_listen.assert_called_once_with(
                        ('fe80::204:acff:fe96:da87%eth0', 1234, 0, 2),
                        family=socket.AF_INET6,
                        backlog=cfg.CONF.backlog
                    )

                    mock_pool.spawn.assert_has_calls([
                        mock.call(
                            server._run,
                            None,
                            mock_listen.return_value)
                    ])

    def test_app(self):
        greetings = 'Hello, World!!!'

        def hello_world(env, start_response):
            if env['PATH_INFO'] != '/':
                start_response('404 Not Found',
                               [('Content-Type', 'text/plain')])
                return ['Not Found\r\n']
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return [greetings]

        server = wsgi.Server("test_app")
        server.start(hello_world, 0, host="127.0.0.1")

        response = urllib2.urlopen('http://127.0.0.1:%d/' % server.port)
        self.assertEqual(greetings, response.read())

        server.stop()


class TestWSGIServerWithSSL(base.BaseTestCase):
    """WSGI server tests."""

    def test_app_using_ssl(self):
        CONF.set_default('use_ssl', True)
        CONF.set_default("ssl_cert_file",
                         os.path.join(TEST_VAR_DIR, 'certificate.crt'))
        CONF.set_default("ssl_key_file",
                         os.path.join(TEST_VAR_DIR, 'privatekey.key'))

        greetings = 'Hello, World!!!'

        @webob.dec.wsgify
        def hello_world(req):
            return greetings

        server = wsgi.Server("test_app")
        server.start(hello_world, 0, host="127.0.0.1")

        response = urllib2.urlopen('https://127.0.0.1:%d/' % server.port)
        self.assertEqual(greetings, response.read())

        server.stop()

    def test_app_using_ipv6_and_ssl(self):
        CONF.set_default('use_ssl', True)
        CONF.set_default("ssl_cert_file",
                         os.path.join(TEST_VAR_DIR, 'certificate.crt'))
        CONF.set_default("ssl_key_file",
                         os.path.join(TEST_VAR_DIR, 'privatekey.key'))

        greetings = 'Hello, World!!!'

        @webob.dec.wsgify
        def hello_world(req):
            return greetings

        server = wsgi.Server("test_app")
        server.start(hello_world, 0, host="::1")

        response = urllib2.urlopen('https://[::1]:%d/' % server.port)
        self.assertEqual(greetings, response.read())

        server.stop()
