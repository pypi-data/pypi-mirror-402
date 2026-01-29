import datetime


class Logger:
    def __init__(self):
        pass
    
    def log_server_start(self, port):
        """
        Log when server starts
        """
        print(f"🔥 GAS dibuka, server jalan di :{port}")
    
    def log_request_received(self, path, method):
        """
        Log incoming requests
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"⛽ [{timestamp}] Request masuk ke {method} {path}, BBM aman")
    
    def log_barang_registered(self, path, method):
        """
        Log when a new endpoint is registered
        """
        print(f"📦 BARANG siap: {method} {path}")
    
    def log_error(self, message):
        """
        Log error messages
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"⚠️  [{timestamp}] ERROR: {message}")
    
    def log_warning(self, message):
        """
        Log warning messages
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"⚠️  [{timestamp}] WARNING: {message}")
    
    def log_info(self, message):
        """
        Log info messages
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"ℹ️  [{timestamp}] INFO: {message}")