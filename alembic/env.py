import os
import re
import sys
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))
sys.path.append(BASE_DIR)

config = context.config

config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

fileConfig(config.config_file_name)

import models

target_metadata = models.Base.metadata

exclude_tables = config.get_section("alembic:exclude").get("tables", "").split(",")


def include_object(object, name, type_, *args, **kwargs):
    return not (type_ == "table" and name in exclude_tables)


def run_migrations_offline():

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        include_object=include_object,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
