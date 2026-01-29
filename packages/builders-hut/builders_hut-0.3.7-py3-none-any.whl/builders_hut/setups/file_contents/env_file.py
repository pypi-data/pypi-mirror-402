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
DB_USER="postgres"
DB_PASS="postgres"
DB_HOST="localhost"
DB_PORT=5432
DB_NAME="postgres"
DB_TYPE="postgres"
""")
