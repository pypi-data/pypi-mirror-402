import os

from alembic.config import Config
from alembic import command

# Upgrade migration
# see https://alembic.sqlalchemy.org/en/latest/api/config.html
def launch_migration_upgrade(alembic_config_path, db_url):
    alembic_cfg = Config(alembic_config_path)
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")
