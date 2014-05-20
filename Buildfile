#!/usr/bin/env bash

# This file is used as an extension to the Heroku Buildpack to complete project
# specific build-related tasks. Please ignore it.

# Include utils from buildpack
# source $BIN_DIR/utils

# Bundle assets using Flask-Funnel
# puts-step "Compress/minify assets"
# python $BUILD_DIR/manage.py funnel bundle_assets | indent

# Run migrations
# FIXME: Commented this out because when we run this here, it doesn't
# have DATABASE_URL available, so the db gets created wrong.
# puts-step "Run migrations"
# python $BUILD_DIR/manage.py db_create | indent
