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

# This is the url to the database. If you're using Heroku, then it'll
# populate this with DATABASE_URL from the environment.
#
# if you don't like what that's doing, you can set it explicitly
# here.
#
# Looks at SQLALCHEMY_DATABASE_URI then defaults to sqlite.
# For a sqlite file-based database, use sqlite:///path/to/db
# SQLALCHEMY_DATABASE_URI = os.environ.get(
#     'SQLALCHEMY_DATABASE_URI',
#     'sqlite:///{0}/ernest_app.db'.format(
#         os.path.join(os.path.dirname(__file__), '..')
#     )
# )


# ------------------------------------------------
# Ernest supports several different cache systems.
# ------------------------------------------------

# Ernest uses Flask-Cache.
# http://pythonhosted.org/Flask-Cache/

# Default to the simple cache type. In production environments, you
# should be using 'saslmemcached'.
CACHE_TYPE = 'simple'

# Cache key prefix to differentiate between other things that might be
# using the same cache.
CACHE_KEY_PREFIX = 'ernest:'

# Note: If you're using Heroku and Memcachier, these will get pulled
# from the environment automatically---you don't need to set them
# manually.

# list of memcached servers
# CACHE_MEMCACHED_SERVERS = ['127.0.0.1:11211']

# memcached username (if any)
# CACHE_MEMCACHED_USERNAME = 'joe'

# memcached password (if any)
# CACHE_MEMCACHED_PASSWORD = 'password'

# This imports settings_local.py thus everything in that file
# overrides what's in this file.
try:
    from ernest.settings_local import *
except ImportError:
    pass
