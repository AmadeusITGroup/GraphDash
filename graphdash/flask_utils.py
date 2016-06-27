# -*- coding: utf-8 -*-

from functools import wraps
from datetime import datetime
import socket

from flask import current_app, request, make_response


# Logging utils
#
def after_request_log(response):
    name = dns_resolve(request.remote_addr)
    current_app.logger.warn(u"""[client {ip} {host}] {http} "{method} {path}" {status}
    Request:   {method} {path}
    Version:   {http}
    Status:    {status}
    Url:       {url}
    IP:        {ip}
    Hostname:  {host}
    Agent:     {agent_platform} | {agent_browser} | {agent_browser_version}
    Raw Agent: {agent}
    """.format(method=request.method,
               path=request.path,
               url=request.url,
               ip=request.remote_addr,
               host=name if name is not None else '?',
               agent_platform=request.user_agent.platform,
               agent_browser=request.user_agent.browser,
               agent_browser_version=request.user_agent.version,
               agent=request.user_agent.string,
               http=request.environ.get('SERVER_PROTOCOL'),
               status=response.status))

    return response


def dns_resolve(ip_addr):
    """Safe DNS query."""
    try:
        name = socket.gethostbyaddr(ip_addr)[0]
    except (socket.herror, socket.gaierror):
        # 1: IP not known
        # 2: Probably badly formated IP
        name = None
    return name


# Cache utils
#
def cache(timeout):
    def _cache(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            resp = make_response(f(*args, **kwargs))
            resp.cache_control.max_age = timeout  # seconds
            return resp
        return wrapper
    return _cache


def nocache(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        resp = make_response(f(*args, **kwargs))
        resp.headers['Last-Modified'] = datetime.now()
        resp.headers['Cache-Control'] = ('no-store, no-cache, must-revalidate, '
                                         'post-check=0, pre-check=0, max-age=0')
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '-1'
        return resp
    return wrapper
