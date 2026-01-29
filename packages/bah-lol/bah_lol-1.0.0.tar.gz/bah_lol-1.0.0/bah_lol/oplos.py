class MiddlewareManager:
    def __init__(self):
        self.middlewares = []
    
    def add_middleware(self, middleware_func):
        """
        Add a middleware function to the chain
        """
        self.middlewares.append(middleware_func)
    
    def process_request(self, request):
        """
        Process the request through all registered middlewares
        """
        processed_request = request.copy()  # Shallow copy to avoid modifying original
        
        for middleware in self.middlewares:
            try:
                # Middleware can modify the request
                processed_request = middleware(processed_request) or processed_request
            except Exception as e:
                print(f"Error in middleware: {e}")
                # Continue with the request even if middleware fails
        
        return processed_request


def cors_middleware(request):
    """
    Example CORS middleware
    """
    request['cors_enabled'] = True
    return request


def logging_middleware(request):
    """
    Example logging middleware
    """
    print(f"OPLOS: Processing request to {request.get('path', 'unknown')}")
    return request