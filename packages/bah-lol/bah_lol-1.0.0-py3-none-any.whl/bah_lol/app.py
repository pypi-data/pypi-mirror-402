import asyncio
from .router import Router
from .gas import run_server
from .logger import Logger
from .oplos import MiddlewareManager


class BahLol:
    def __init__(self):
        self.router = Router()
        self.middleware_manager = MiddlewareManager()
        self.logger = Logger()
        
    def barang(self, path, method="GET"):
        """
        Decorator to register a new endpoint (BARANG)
        """
        def decorator(func):
            self.router.add_route(method, path, func)
            self.logger.log_barang_registered(path, method)
            return func
        return decorator
        
    def use_middleware(self, middleware_func):
        """
        Register a middleware (OPLOS)
        """
        self.middleware_manager.add_middleware(middleware_func)
        
    def gas(self, host="127.0.0.1", port=8000):
        """
        Start the server (GAS)
        """
        self.logger.log_server_start(port)
        run_server(self.router, self.middleware_manager, self.logger, host, port)