import argparse
import sys
import os
from pathlib import Path


def create_barang(name):
    """
    Create a new endpoint template
    """
    template = f'''def {name}(request):
    """
    BARANG: {name}
    Generated endpoint
    """
    return {{
        "status": "success",
        "message": "{name} endpoint is ready",
        "data": {{}}
    }}
'''
    print(template)
    return template


def create_oplos(name):
    """
    Create a new middleware template
    """
    template = f'''def {name}_middleware(request):
    """
    OPLOS: {name}
    Custom middleware
    """
    # Add your middleware logic here
    print(f"Processing with {name} middleware")
    return request
'''
    print(template)
    return template


def main():
    parser = argparse.ArgumentParser(description='Bah Lol CLI - Framework untuk API yang jelas dan langsung jalan')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # gas command - run server
    gas_parser = subparsers.add_parser('gas', help='Jalankan server')
    gas_parser.add_argument('--port', type=int, default=8000, help='Port untuk server (default: 8000)')
    gas_parser.add_argument('--host', default='127.0.0.1', help='Host untuk server (default: 127.0.0.1)')

    # barang command - create endpoint
    barang_parser = subparsers.add_parser('barang', help='Generate endpoint')
    barang_parser.add_argument('name', help='Nama endpoint')

    # oplos command - create middleware
    oplos_parser = subparsers.add_parser('oplos', help='Tambah middleware')
    oplos_parser.add_argument('name', help='Nama middleware')

    # bbm command - inspect payload
    bbm_parser = subparsers.add_parser('bbm', help='Inspect request payload')

    # bahenol command - enable plugin
    bahenol_parser = subparsers.add_parser('bahenol', help='Enable plugin')

    args = parser.parse_args()

    if args.command == 'gas':
        print(f"🔥 GAS dibuka di port {args.port}")
        # Note: Actual server startup would happen here
        print("TIPS: Untuk menjalankan server, gunakan app.gas() di kode Anda")
        
    elif args.command == 'barang':
        print(f"Membuat BARANG: {args.name}")
        create_barang(args.name)
        
    elif args.command == 'oplos':
        print(f"Membuat OPLOS: {args.name}")
        create_oplos(args.name)
        
    elif args.command == 'bbm':
        print("🔍 Inspeksi BBM (payload) akan muncul di log saat request diterima")
        
    elif args.command == 'bahenol':
        print("🔌 Plugin BAHENOL diaktifkan")
        
    elif args.command is None:
        parser.print_help()
        
    else:
        print(f"Perintah tidak dikenali: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    main()