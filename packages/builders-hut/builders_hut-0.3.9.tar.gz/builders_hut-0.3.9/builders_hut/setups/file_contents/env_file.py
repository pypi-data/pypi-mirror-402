from textwrap import dedent

ENV_FILE_CONTENT = dedent("""
# Project
TITLE="{title}"
DESCRIPTION="{description}"
VERSION="{version}"

# Debugging
DEBUG=True

# Server
PORT=8000
HOST="0.0.0.0"

# Database
DB_USER=""
DB_PASS=""
DB_HOST=""
DB_PORT=
DB_NAME=""
DB_TYPE=""
""")
