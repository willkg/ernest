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

# This will fail if there's no SECRET_KEY in the environment.
# Either provide it there or add it to settings_local.py
SECRET_KEY = os.environ.get('SECRET_KEY')

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

# This imports settings_local.py thus everything in that file
# overrides what's in this file.
try:
    from ernest.settings_local import *  # noqa
except ImportError:
    pass
