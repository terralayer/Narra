#!/bin/sh
set -eu

python - <<'PY'
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from narra.db import engine

config = Config("alembic.ini")
inspector = inspect(engine)

# Narra 0.1.0-alpha originally created tables directly with SQLAlchemy and did
# not maintain Alembic's version table. Preserve those databases by marking
# the initial schema as applied, then run all later migrations normally.
if not inspector.has_table("alembic_version") and inspector.has_table("releases"):
    command.stamp(config, "0001")

command.upgrade(config, "head")
PY

exec uvicorn narra.app:app --host 0.0.0.0 --port 8000
