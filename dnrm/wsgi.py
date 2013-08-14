#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Eugene Frolov <profisphantom@gmail.com>.
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

import errno
import os
import socket
import ssl
import sys
import time

import eventlet.wsgi
eventlet.patcher.monkey_patch(all=False, socket=True)

from oslo.config import cfg

import routes.middleware
import webob.dec
import webob.exc

from dnrm.openstack.common import log as logging

LOG = logging.getLogger(__name__)


socket_opts = [
    cfg.IntOpt('backlog',
               default=4096,
               help=_("Number of backlog requests to configure "
                      "the socket with")),
    cfg.IntOpt('tcp_keepidle',
               default=600,
               help=_("Sets the value of TCP_KEEPIDLE in seconds for each "
                      "server socket. Not supported on OS X.")),
    cfg.IntOpt('retry_until_window',
               default=30,
               help=_("Number of seconds to keep retrying to listen")),
    cfg.BoolOpt('use_ssl',
                default=False,
                help=_('Enable SSL on the API server')),
    cfg.StrOpt('ssl_ca_file',
               default=None,
               help=_("CA certificate file to use to verify "
                      "connecting clients")),
    cfg.StrOpt('ssl_cert_file',
               default=None,
               help=_("Certificate file to use when starting "
                      "the server securely")),
    cfg.StrOpt('ssl_key_file',
               default=None,
               help=_("Private key file to use when starting "
                      "the server securely")),
]

CONF = cfg.CONF
CONF.register_opts(socket_opts)


class Request(webob.Request):
    pass


class Router(object):
    """WSGI middleware that maps incoming requests to WSGI apps."""

    @classmethod
    def factory(cls, global_config, **local_config):
        """Return an instance of the WSGI Router class."""
        return cls()

    def __init__(self, mapper):
        """Create a router for the given routes.Mapper.

        Each route in `mapper` must specify a 'controller', which is a
        WSGI app to call.  You'll probably want to specify an 'action' as
        well and have your controller be a wsgi.Controller, who will route
        the request to the action method.

        Examples:
          mapper = routes.Mapper()
          sc = ServerController()

          # Explicit mapping of one route to a controller+action
          mapper.connect(None, "/svrlist", controller=sc, action="list")

          # Actions are all implicitly defined
          mapper.resource("network", "networks", controller=nc)

          # Pointing to an arbitrary WSGI app.  You can specify the
          # {path_info:.*} parameter so the target app can be handed just that
          # section of the URL.
          mapper.connect(None, "/v1.0/{path_info:.*}", controller=BlogApp())
        """
        self.map = mapper
        self._router = routes.middleware.RoutesMiddleware(self._dispatch,
                                                          self.map)

    @webob.dec.wsgify
    def __call__(self, req):
        """Route the incoming request to a controller based on self.map.

        If no match, return a 404.
        """
        return self._router

    @staticmethod
    @webob.dec.wsgify(RequestClass=Request)
    def _dispatch(req):
        """Dispatch a Request.

        Called by self._router after matching the incoming request to a route
        and putting the information into req.environ. Either returns 404
        or the routed WSGI app's response.
        """
        match = req.environ['wsgiorg.routing_args'][1]
        if not match:
            msg = _('The resource could not be found.')
            return webob.exc.HTTPNotFound(explanation=msg)
        app = match['controller']
        return app


class Server(object):
    """Server class to manage multiple WSGI sockets and applications."""

    def __init__(self, name, threads=1000):
        self.pool = eventlet.GreenPool(threads)
        self.name = name

    def _get_socket(self, host, port, backlog):
        bind_addr = (host, port)
        # TODO(dims): eventlet's green dns/socket module does not actually
        # support IPv6 in getaddrinfo(). We need to get around this in the
        # future or monitor upstream for a fix
        try:
            info = socket.getaddrinfo(bind_addr[0],
                                      bind_addr[1],
                                      socket.AF_UNSPEC,
                                      socket.SOCK_STREAM)[0]
            family = info[0]
            bind_addr = info[-1]
        except Exception:
            LOG.exception(_("Unable to listen on %(host)s:%(port)s") %
                          {'host': host, 'port': port})
            sys.exit(1)

        if CONF.use_ssl:
            if not os.path.exists(CONF.ssl_cert_file):
                raise RuntimeError(_("Unable to find ssl_cert_file "
                                     ": %s") % CONF.ssl_cert_file)

            if not os.path.exists(CONF.ssl_key_file):
                raise RuntimeError(_("Unable to find "
                                     "ssl_key_file : %s") % CONF.ssl_key_file)

            # ssl_ca_file is optional
            if CONF.ssl_ca_file and not os.path.exists(CONF.ssl_ca_file):
                raise RuntimeError(_("Unable to find ssl_ca_file "
                                     ": %s") % CONF.ssl_ca_file)

        def wrap_ssl(sock):
            ssl_kwargs = {
                'server_side': True,
                'certfile': CONF.ssl_cert_file,
                'keyfile': CONF.ssl_key_file,
                'cert_reqs': ssl.CERT_NONE,
            }

            if CONF.ssl_ca_file:
                ssl_kwargs['ca_certs'] = CONF.ssl_ca_file
                ssl_kwargs['cert_reqs'] = ssl.CERT_REQUIRED

            return ssl.wrap_socket(sock, **ssl_kwargs)

        sock = None
        retry_until = time.time() + CONF.retry_until_window
        while not sock and time.time() < retry_until:
            try:
                sock = eventlet.listen(bind_addr,
                                       backlog=backlog,
                                       family=family)
                if CONF.use_ssl:
                    sock = wrap_ssl(sock)

            except socket.error as err:
                if err.errno != errno.EADDRINUSE:
                    raise
                eventlet.sleep(0.1)
        if not sock:
            raise RuntimeError(_("Could not bind to %(host)s:%(port)s "
                               "after trying for %(time)d seconds") %
                               {'host': host,
                                'port': port,
                                'time': CONF.retry_until_window})
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # sockets can hang around forever without keepalive
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        # This option isn't available in the OS X version of eventlet
        if hasattr(socket, 'TCP_KEEPIDLE'):
            sock.setsockopt(socket.IPPROTO_TCP,
                            socket.TCP_KEEPIDLE,
                            CONF.tcp_keepidle)

        return sock

    def start(self, application, port, host='0.0.0.0'):
        """Run a WSGI server with the given application."""
        self._host = host
        self._port = port
        backlog = CONF.backlog

        self._socket = self._get_socket(self._host,
                                        self._port,
                                        backlog=backlog)
        self._server = self.pool.spawn(self._run, application, self._socket)

    @property
    def host(self):
        return self._socket.getsockname()[0] if self._socket else self._host

    @property
    def port(self):
        return self._socket.getsockname()[1] if self._socket else self._port

    def stop(self):
        self._server.kill()

    def wait(self):
        """Wait until all servers have completed running."""
        try:
            self.pool.waitall()
        except KeyboardInterrupt:
            pass

    def _run(self, application, socket):
        """Start a WSGI server in a new green thread."""
        logger = logging.getLogger('eventlet.wsgi.server')
        eventlet.wsgi.server(socket, application, custom_pool=self.pool,
                             log=logging.WritableLogger(logger))
