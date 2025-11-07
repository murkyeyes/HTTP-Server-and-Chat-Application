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
daemon.httpadapter
~~~~~~~~~~~~~~~~~

This module provides a http adapter object to manage and persist 
http settings (headers, bodies). The adapter supports both
raw URL paths and RESTful route definitions, and integrates with
Request and Response objects to handle client-server communication.
"""

from .request import Request
from .response import Response
from .dictionary import CaseInsensitiveDict

class HttpAdapter:
    """
    A mutable :class:`HTTP adapter <HTTP adapter>` for managing client connections
    and routing requests.

    The `HttpAdapter` class encapsulates the logic for receiving HTTP requests,
    dispatching them to appropriate route handlers, and constructing responses.
    It supports RESTful routing via hooks and integrates with :class:`Request <Request>` 
    and :class:`Response <Response>` objects for full request lifecycle management.

    Attributes:
        ip (str): IP address of the client.
        port (int): Port number of the client.
        conn (socket): Active socket connection.
        connaddr (tuple): Address of the connected client.
        routes (dict): Mapping of route paths to handler functions.
        request (Request): Request object for parsing incoming data.
        response (Response): Response object for building and sending replies.
    """

    __attrs__ = [
        "ip",
        "port",
        "conn",
        "connaddr",
        "routes",
        "request",
        "response",
    ]

    def __init__(self, ip, port, conn, connaddr, routes):
        """
        Initialize a new HttpAdapter instance.

        :param ip (str): IP address of the client.
        :param port (int): Port number of the client.
        :param conn (socket): Active socket connection.
        :param connaddr (tuple): Address of the connected client.
        :param routes (dict): Mapping of route paths to handler functions.
        """

        #: IP address.
        self.ip = ip
        #: Port.
        self.port = port
        #: Connection
        self.conn = conn
        #: Conndection address
        self.connaddr = connaddr
        #: Routes
        self.routes = routes
        #: Request
        self.request = Request()
        #: Response
        self.response = Response()

    def handle_client(self, conn, addr, routes):
        """
        Handle an incoming client connection.

        This method reads the request from the socket, prepares the request object,
        invokes the appropriate route handler if available, builds the response,
        and sends it back to the client.

        :param conn (socket): The client socket connection.
        :param addr (tuple): The client's address.
        :param routes (dict): The route mapping for dispatching requests.
        """

        # Connection handler.
        self.conn = conn        
        # Connection address.
        self.connaddr = addr
        # Request handler
        req = self.request
        # Response handler
        resp = self.response

        try:
            # Handle the request
            msg = conn.recv(1024).decode()
            # --- BỔ SUNG KHẮC PHỤC LỖI ---
            if not msg:
                print("[HttpAdapter] Client closed connection or sent empty request.")
                conn.close()
                return # Thoát khỏi hàm xử lý client
            # -----------------------------
            req.prepare(msg, routes)

            # Public paths that don't require authentication
            public_paths = [
                '/login.html',
                '/chat.html',
                '/nonexistent.html'  # For 404 testing
            ]
            
            # Check if path is public (login page, static files, API routes)
            is_public = (
                req.path in public_paths or
                req.path.startswith('/static/') or
                req.path.startswith('/api/') or
                req.path.startswith('/images/')
            )

            # Handle authentication for /login POST request
            if req.hook:
                print("[HttpAdapter] hook in route-path METHOD {} PATH {}".format(req.hook._route_path, req.hook._route_methods))
                # Call the hook function with proper parameters
                hook_result = req.hook(headers=str(req.headers), body=req.body)
                # Set the response content
                resp.content = hook_result if hook_result else ""
                response = resp.build_response(req)
            # Handle authentication for /login POST request (ƯU TIÊN 2)
            elif req.method == 'POST' and req.path == '/login':
                response = self.handle_login(req, resp)
            # Handle authentication check for protected routes (ƯU TIÊN 3)
            elif (req.path == '/index.html' or req.path == '/') and not is_public:
                response = self.handle_protected_route(req, resp)
            else:
                # Build normal response (public files)
                response = resp.build_response(req)
        except Exception as e:
            print("[HttpAdapter] Error processing request: {}".format(e))
            response = self.build_error_response(500, "Internal Server Error")

        #print(response)
        conn.sendall(response)
        conn.close()

    def extract_cookies(self, req):
        """
        Build cookies from the :class:`Request <Request>` headers.

        :param req:(Request) The :class:`Request <Request>` object.
        :rtype: cookies - A dictionary of cookie key-value pairs.
        """
        return req.cookies

    def build_response(self, req, resp):
        """Builds a :class:`Response <Response>` object 

        :param req: The :class:`Request <Request>` used to generate the response.
        :param resp: The  response object.
        :rtype: Response
        """
        response = Response()

        # Set encoding.
        response.encoding = 'utf-8'  # Default encoding
        response.raw = resp
        response.reason = getattr(response.raw, 'reason', 'OK')

        if isinstance(req.url, bytes):
            response.url = req.url.decode("utf-8")
        else:
            response.url = req.url

        # Add new cookies from the server.
        response.cookies = self.extract_cookies(req)

        # Give the Response some context.
        response.request = req
        response.connection = self

        return response

    # def get_connection(self, url, proxies=None):
        # """Returns a url connection for the given URL. 

        # :param url: The URL to connect to.
        # :param proxies: (optional) A Requests-style dictionary of proxies used on this request.
        # :rtype: int
        # """

        # proxy = select_proxy(url, proxies)

        # if proxy:
            # proxy = prepend_scheme_if_needed(proxy, "http")
            # proxy_url = parse_url(proxy)
            # if not proxy_url.host:
                # raise InvalidProxyURL(
                    # "Please check proxy URL. It is malformed "
                    # "and could be missing the host."
                # )
            # proxy_manager = self.proxy_manager_for(proxy)
            # conn = proxy_manager.connection_from_url(url)
        # else:
            # # Only scheme should be lower case
            # parsed = urlparse(url)
            # url = parsed.geturl()
            # conn = self.poolmanager.connection_from_url(url)

        # return conn


    def add_headers(self, request):
        """
        Add headers to the request.

        This method is intended to be overridden by subclasses to inject
        custom headers. It does nothing by default.

        
        :param request: :class:`Request <Request>` to add headers to.
        """
        pass

    def build_proxy_headers(self, proxy):
        """Returns a dictionary of the headers to add to any request sent
        through a proxy. 

        :class:`HttpAdapter <HttpAdapter>`.

        :param proxy: The url of the proxy being used for this request.
        :rtype: dict
        """
        headers = {}
        #
        # TODO: build your authentication here
        #       username, password =...
        # we provide dummy auth here
        #
        username, password = ("user1", "password")

        if username:
            headers["Proxy-Authorization"] = (username, password)

        return headers
    
    def handle_login(self, req, resp):
        """Handle login POST request with authentication."""
        form_data = req.parse_form_data()
        username = form_data.get('username', '')
        password = form_data.get('password', '')
        
        print("[HttpAdapter] Login attempt: username={}, password={}".format(username, password))
        
        # Check credentials (admin/password)
        if username == 'admin' and password == 'password':
            # Login successful - set cookie and serve index page
            resp.set_cookie('auth', 'true')
            resp.status_code = 200
            req.path = '/index.html'  # Serve index page
            return resp.build_response(req)
        else:
            # Login failed - return 401
            return self.build_error_response(401, "Unauthorized")
    
    def handle_protected_route(self, req, resp):
        """Handle protected routes that require authentication."""
        auth_cookie = req.cookies.get('auth', '')
        
        if auth_cookie == 'true':
            # Authenticated - serve the requested page
            if req.path == '/':
                req.path = '/index.html'
            return resp.build_response(req)
        else:
            # Not authenticated - return 401 or redirect to login
            return self.build_error_response(401, "Unauthorized - Please login first")
    
    def build_error_response(self, status_code, message):
        """Build error response."""
        if status_code == 401:
            response_body = """
            <html><body>
            <h1>401 Unauthorized</h1>
            <p>{}</p>
            <a href="/login.html">Login Here</a>
            </body></html>
            """.format(message)
        else:
            response_body = """
            <html><body>
            <h1>{} {}</h1>
            <p>An error occurred: {}</p>
            </body></html>
            """.format(status_code, message, message)
            
        response_text = """HTTP/1.1 {} {}
Content-Type: text/html
Content-Length: {}
Connection: close

{}""".format(status_code, message, len(response_body), response_body)
        
        return response_text.encode('utf-8')