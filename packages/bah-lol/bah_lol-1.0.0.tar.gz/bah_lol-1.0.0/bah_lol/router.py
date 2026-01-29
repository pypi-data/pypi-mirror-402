import json
import re
from urllib.parse import urlparse, parse_qs


class Route:
    def __init__(self, method, path, handler):
        self.method = method.upper()
        self.path = path
        self.handler = handler
        self.param_pattern = re.compile(r'<(\w+)>')
        self.regex_pattern = self._compile_path(path)
    
    def _compile_path(self, path):
        # Convert path like "/users/<id>" to regex pattern
        regex_path = re.sub(r'<(\w+)>', r'(?P<\1>[^/]+)', path)
        return re.compile(f'^{regex_path}$')
    
    def matches(self, request_path):
        return self.regex_pattern.match(request_path)
    
    def extract_params(self, request_path):
        match = self.regex_pattern.match(request_path)
        if match:
            return match.groupdict()
        return None


class Router:
    def __init__(self):
        self.routes = []
    
    def add_route(self, method, path, handler):
        route = Route(method, path, handler)
        self.routes.append(route)
    
    def find_handler(self, method, path):
        for route in self.routes:
            if route.method == method.upper() and route.matches(path):
                params = route.extract_params(path)
                return route.handler, params
        return None, None
    
    def get_routes_info(self):
        routes_info = []
        for route in self.routes:
            routes_info.append({
                'method': route.method,
                'path': route.path
            })
        return routes_info