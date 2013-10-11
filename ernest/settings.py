import os

from ernest.utils import truthiness


# Whether or not we're in DEBUG mode. DEBUG mode is good for
# development and BAD BAD BAD for production.
DEBUG = truthiness(os.environ.get('DEBUG', True))


# ------------------------------------------------
# Required things to set
# ------------------------------------------------

# Set the SECRET_KEY in your settings_local.py file.
# e.g. SECRET_KEY = 'ou812'

# Set the Bugzilla url for logging in via http post.
BUGZILLA_LOGIN_URL = 'https://bugzilla.mozilla.org/index.cgi'

# Set the Bugzilla API url.
BUGZILLA_API_URL = 'https://api-dev.bugzilla.mozilla.org/latest'

# List of Bugzilla logins that are also considered Ernest admin. These
# people can create new projects, sprints, etc.
ADMIN = []

# ------------------------------------------------
# Database
# ------------------------------------------------

# This is the url to the database.
# For a sqlite file-based database, use sqlite:///path/to/db
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'SQLALCHEMY_DATABASE_URI',
    'sqlite:///{0}/ernest_app.db'.format(
        os.path.join(os.path.dirname(__file__), '..'))
)


# ------------------------------------------------
# Ernest supports several different cache systems.
# ------------------------------------------------

# Memcache setup
# MEMCACHE_URL = os.environ.get('MEMCACHE_URL', '127.0.0.1:11211')
# MEMCACHE_PREFIX = os.environment.get('MEMCACHE_PREFIX', 'ernest:')

# NullCache
# NULLCACHE = True


# This imports settings_local.py thus everything in that file
# overrides what's in this file.
try:
    from ernest.settings_local import *
except ImportError:
    pass
