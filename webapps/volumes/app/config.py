import os

PKI_DATA_DIR   = os.environ.get('PKI_DATA_DIR', '/data')
ADMIN_USER     = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'changeme')
SECRET_KEY     = os.environ.get('SECRET_KEY', 'dev-secret-key')
BASE_URL       = os.environ.get('BASE_URL', '').rstrip('/')

# Convenience: filesystem root for all CA directories
CA_BASE = os.path.join(PKI_DATA_DIR, 'ca')
DB_PATH = os.path.join(PKI_DATA_DIR, 'pki.db')
