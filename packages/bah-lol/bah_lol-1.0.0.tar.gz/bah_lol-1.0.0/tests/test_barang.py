import unittest
from unittest.mock import Mock
from bah_lol.app import BahLol
from bah_lol.router import Router


class TestBarang(unittest.TestCase):
    def setUp(self):
        self.app = BahLol()
    
    def test_barang_decorator_registers_route(self):
        """Test that @app.barang registers a route correctly"""
        
        @self.app.barang("/test")
        def test_handler():
            return {"message": "test"}
        
        # Check that the route was added to the router
        handler, params = self.app.router.find_handler("GET", "/test")
        self.assertIsNotNone(handler)
        self.assertEqual(handler.__name__, "test_handler")
    
    def test_barang_with_post_method(self):
        """Test that @app.barang works with POST method"""
        
        @self.app.barang("/post-test", method="POST")
        def post_handler():
            return {"message": "post test"}
        
        handler, params = self.app.router.find_handler("POST", "/post-test")
        self.assertIsNotNone(handler)
        self.assertEqual(handler.__name__, "post_handler")
    
    def test_router_finds_correct_handler(self):
        """Test that router finds the correct handler for a path"""
        
        @self.app.barang("/users/<id>")
        def get_user(user_id):
            return {"user_id": user_id}
        
        handler, params = self.app.router.find_handler("GET", "/users/123")
        self.assertIsNotNone(handler)
        self.assertEqual(params, {"id": "123"})
    
    def test_router_returns_none_for_unregistered_path(self):
        """Test that router returns None for unregistered paths"""
        
        handler, params = self.app.router.find_handler("GET", "/nonexistent")
        self.assertIsNone(handler)
        self.assertIsNone(params)


if __name__ == '__main__':
    unittest.main()