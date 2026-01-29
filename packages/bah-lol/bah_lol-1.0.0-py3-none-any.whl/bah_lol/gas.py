import socket
import threading
import json
from io import BytesIO


def run_server(router, middleware_manager, logger, host="127.0.0.1", port=8000):
    """
    Simple HTTP server implementation for Bah Lol
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(5)
    
    print(f"🔥 GAS dibuka, server jalan di :{port}")
    
    try:
        while True:
            client_socket, addr = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, router, middleware_manager, logger)
            )
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server_socket.close()


def handle_client(client_socket, router, middleware_manager, logger):
    """
    Handle individual client requests
    """
    try:
        request_data = client_socket.recv(1024).decode('utf-8')
        if not request_data:
            return
        
        # Parse the request
        request_lines = request_data.split('\n')
        request_line = request_lines[0].strip()
        method, path, protocol = request_line.split()
        
        # Extract path and query parameters
        path_parts = path.split('?', 1)
        path = path_parts[0]
        query_params = {}
        if len(path_parts) > 1:
            query_string = path_parts[1]
            pairs = query_string.split('&')
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    query_params[key] = value
                else:
                    query_params[pair] = ''
        
        # Log request received
        logger.log_request_received(path, method)
        
        # Find handler for the route
        handler, path_params = router.find_handler(method, path)
        
        if handler:
            # Prepare request object
            request = {
                'method': method,
                'path': path,
                'query_params': query_params,
                'path_params': path_params or {},
                'headers': {}
            }
            
            # Extract headers
            for line in request_lines[1:]:
                if ':' in line:
                    header_name, header_value = line.split(':', 1)
                    request['headers'][header_name.strip()] = header_value.strip()
            
            # Extract body if present
            body_start = request_data.find('\r\n\r\n')
            if body_start != -1:
                body = request_data[body_start + 4:]
                if body:
                    try:
                        request['body'] = json.loads(body)
                    except json.JSONDecodeError:
                        request['body'] = body
            
            # Apply middlewares
            processed_request = middleware_manager.process_request(request)
            
            # Call the handler
            if hasattr(processed_request, 'get') and 'body' in processed_request:
                response_data = handler(processed_request['body']) if processed_request['method'] in ['POST', 'PUT', 'PATCH'] else handler()
            else:
                response_data = handler()
            
            # Convert response to JSON if needed
            if not isinstance(response_data, str):
                response_body = json.dumps(response_data, ensure_ascii=False)
                content_type = 'application/json'
            else:
                response_body = response_data
                content_type = 'text/html'
            
            # Create response
            response_headers = [
                f"HTTP/1.1 200 OK",
                f"Content-Type: {content_type}",
                f"Content-Length: {len(response_body.encode('utf-8'))}",
                "Connection: close",
                ""
            ]
            
            response = "\r\n".join(response_headers) + "\r\n" + response_body
            
            client_socket.send(response.encode('utf-8'))
        else:
            # 404 response
            response_body = json.dumps({"error": "Not Found"}, ensure_ascii=False)
            response_headers = [
                "HTTP/1.1 404 Not Found",
                "Content-Type: application/json",
                f"Content-Length: {len(response_body.encode('utf-8'))}",
                "Connection: close",
                ""
            ]
            response = "\r\n".join(response_headers) + "\r\n" + response_body
            client_socket.send(response.encode('utf-8'))
    
    except Exception as e:
        # Error response
        error_response = json.dumps({"error": "Internal Server Error"}, ensure_ascii=False)
        response_headers = [
            "HTTP/1.1 500 Internal Server Error",
            "Content-Type: application/json",
            f"Content-Length: {len(error_response.encode('utf-8'))}",
            "Connection: close",
            ""
        ]
        response = "\r\n".join(response_headers) + "\r\n" + error_response
        client_socket.send(response.encode('utf-8'))
    finally:
        client_socket.close()