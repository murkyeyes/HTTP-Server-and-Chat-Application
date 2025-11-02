#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.request
~~~~~~~~~~~~~~~~~

This module provides a Request object to manage and persist 
request settings (cookies, auth, proxies).
"""
from .dictionary import CaseInsensitiveDict

class Request():
    """The fully mutable "class" `Request <Request>` object,
    containing the exact bytes that will be sent to the server.

    Instances are generated from a "class" `Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    Usage::

      >>> import deamon.request
      >>> req = request.Request()
      ## Incoming message obtain aka. incoming_msg
      >>> r = req.prepare(incoming_msg)
      >>> r
      <Request>
    """
    __attrs__ = [
        "method",
        "url",
        "headers",
        "body",
        "reason",
        "cookies",
        "body",
        "routes",
        "hook",
    ]

    def __init__(self):
        #: HTTP verb to send to the server.
        self.method = None
        #: HTTP URL to send the request to.
        self.url = None
        #: dictionary of HTTP headers.
        self.headers = None
        #: HTTP path
        self.path = None        
        # The cookies set used to create Cookie header
        self.cookies = None
        #: request body to send to the server.
        self.body = None
        #: Routes
        self.routes = {}
        #: Hook point for routed mapped-path
        self.hook = None

    def extract_request_line(self, request):
        try:
            lines = request.splitlines()
            first_line = lines[0]
            method, path, version = first_line.split()

            if path == '/':
                path = '/index.html'
        except Exception:
            return None, None, None

        return method, path, version
             
    def prepare_headers(self, request):
        """Prepares the given HTTP headers."""
        lines = request.split('\r\n')
        headers = {}
        for line in lines[1:]:
            if ': ' in line:
                key, val = line.split(': ', 1)
                headers[key.lower()] = val
        return headers

    def prepare(self, request, routes=None):
        """Prepares the entire request with the given parameters."""

        # Prepare the request line from the request header
        self.method, self.path, self.version = self.extract_request_line(request)
        print("[Request] {} path {} version {}".format(self.method, self.path, self.version))

        #
        # @bksysnet Preapring the webapp hook with WeApRous instance
        # The default behaviour with HTTP server is empty routed
        #
        # TODO manage the webapp hook in this mounting point
        #
        
        if not routes == {}:
            self.routes = routes
            
            # Strip query string for route matching
            path_without_query = self.path.split('?')[0] if '?' in self.path else self.path
            
            self.hook = routes.get((self.method, path_without_query))
            #
            # self.hook manipulation goes here
            # ...
            #

        self.headers = self.prepare_headers(request)
        
        # Parse cookies from headers
        self.cookies = self.parse_cookies()
        
        # Extract body for POST requests
        if self.method == 'POST':
            self.body = self.extract_body(request)
        else:
            self.body = ""

        return

    def prepare_body(self, data, files, json=None):
        if data:
            self.body = data
        self.prepare_content_length(self.body)
        #
        # TODO prepare the request authentication
        #
        # self.auth = ...
        return


    def prepare_content_length(self, body):
        self.headers["Content-Length"] = "0"
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return


    def prepare_auth(self, auth, url=""):
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        return

    def prepare_cookies(self, cookies):
        self.headers["Cookie"] = cookies

    def parse_cookies(self):
        """Parse cookies from Cookie header."""
        cookies = {}
        cookie_header = self.headers.get('cookie', '')
        if cookie_header:
            for pair in cookie_header.split(';'):
                if '=' in pair:
                    key, value = pair.strip().split('=', 1)
                    cookies[key] = value
        return cookies
    
    def extract_body(self, request):
        """Extract body from POST request."""
        try:
            parts = request.split('\r\n\r\n', 1)
            if len(parts) > 1:
                return parts[1]
        except Exception:
            pass
        return ""
    
    def parse_form_data(self):
        """Parse form data from POST body."""
        form_data = {}
        if self.body:
            for pair in self.body.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    # URL decode if needed
                    form_data[key] = value.replace('+', ' ')
        return form_data
