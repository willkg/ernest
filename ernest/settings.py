import os

from ernest.utils import truthiness


# Whether or not we're in DEBUG mode. DEBUG mode is good for
# development and BAD BAD BAD for production.
DEBUG = truthiness(os.environ.get('DEBUG', True))

# This is the url to the database.
# For a sqlite file-based database, use sqlite:///path/to/db
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'SQLALCHEMY_DATABASE_URI', 'sqlite:///../ernest_app.db')

# Memcache setup
MEMCACHE_URL = os.environ.get('MEMCACHE_URL', '127.0.0.1:11211')

# Set the SECRET_KEY in your settings_local.py file.

# TODO: Add project settings here..

# This imports settings_local.py thus everything in that file
# overrides what's in this file.
try:
    from ernest.settings_local import *
except ImportError:
    pass
