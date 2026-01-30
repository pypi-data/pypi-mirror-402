import os
from datetime import datetime, timezone, date

import sqlalchemy as sa
import sqlalchemy.types as types
from dataclasses_json import dataclass_json
from dataclasses_json.mm import TYPES, _IsoField
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_scoped_session
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker, scoped_session

LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo
# See : https://mike.depalatis.net/blog/sqlalchemy-timestamps.html
class Timestamp(sa.types.TypeDecorator):
    impl = sa.types.DateTime

    cache_ok = True

    def process_bind_param(self, value: datetime, dialect):
        if value is None:
            return None

        if value.tzinfo is None:
            value = value.astimezone(LOCAL_TIMEZONE)

        value = value.astimezone(timezone.utc)

        if self.timezone:
            return value
        else:
            return value.replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)


# Customize encoder/decoder to use isoformat to store datetime objects (See : https://github.com/lidatong/dataclasses-json/issues/332)
TYPES[datetime] = _IsoField

def JSONBDataclass(cls, many=False):
    serializable_cls = dataclass_json(cls)
    schema = serializable_cls.schema(many=many)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value

        return schema.dump(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value

        return schema.load(value)

    def coerce_compared_value(self, op, value):
        return self.impl.coerce_compared_value(op, value)

    return type(cls.__name__, (types.TypeDecorator,), {
        "impl": JSONB,
        "process_bind_param": process_bind_param,
        "process_result_value": process_result_value,
        "cache_ok": True,
        "coerce_compared_value": coerce_compared_value,
    })

import json
def json_serializer(x):
    def default(obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))

    return json.dumps(x, default=default)

class PostgresConnector(object):
    def __init__(self, host, db_name, username, password,
                 pool_size=None,
                 max_overflow=None,
                 pool_timeout=None,
                 pool_recycle=None):
        """
        Args:
            host: Database host
            db_name: Database name
            username: Database username
            password: Database password
            pool_size: Number of permanent connections (env: DB_POOL_SIZE, default: 5)
                HikariCP equivalent: minimumIdle = 5
            max_overflow: Max additional connections beyond pool_size (env: DB_MAX_OVERFLOW, default: 5)
                HikariCP equivalent: maximumPoolSize - minimumIdle = 10 - 5 = 5
            pool_timeout: Seconds to wait for a connection (env: DB_POOL_TIMEOUT, default: 30)
                HikariCP equivalent: connectionTimeout (not set in current config, recommended: 30000ms)
            pool_recycle: Seconds before recycling a connection (env: DB_POOL_RECYCLE, default: 480)
                HikariCP equivalent: maxLifetime = 480000ms (8 minutes)
        """
        self.host = host
        self.username = username
        self.password = password
        self.db_name = db_name
        self.pool_size = pool_size if pool_size is not None else int(os.getenv('DB_POOL_SIZE', '5'))
        self.max_overflow = max_overflow if max_overflow is not None else int(os.getenv('DB_MAX_OVERFLOW', '5'))
        self.pool_timeout = pool_timeout if pool_timeout is not None else int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.pool_recycle = pool_recycle if pool_recycle is not None else int(os.getenv('DB_POOL_RECYCLE', '480'))
        self._engine = None
        self._session_factory = None

    def get_engine(self):
        if not self._engine:
            # https://docs.sqlalchemy.org/en/14/core/pooling.html#dealing-with-disconnects
            self._engine = create_engine(self.get_url(),
                                         pool_pre_ping=True,
                                         pool_size=self.pool_size,
                                         max_overflow=self.max_overflow,
                                         pool_timeout=self.pool_timeout,
                                         pool_recycle=self.pool_recycle,
                                         pool_use_lifo=True,
                                         connect_args={},
                                         json_serializer=json_serializer
                                         )

        return self._engine

    def get_scoped_session(self, _ident_func):
        return scoped_session(self.get_session_factory(), scopefunc=_ident_func)

    def get_session_factory(self):
        if not self._session_factory:
            self._session_factory = sessionmaker(bind=self.get_engine())
        return self._session_factory

    def get_url(self) -> str:
        return "postgresql+psycopg2://{}:{}@{}/{}".format(
            self.username,
            self.password,
            self.host,
            self.db_name
        )


class AsyncPostgresConnector(object):
    def __init__(self, host, db_name, username, password,
                 pool_size=None,
                 max_overflow=None,
                 pool_timeout=None,
                 pool_recycle=None):
        """
        Args:
            host: Database host
            db_name: Database name
            username: Database username
            password: Database password
            pool_size: Number of permanent connections (env: DB_POOL_SIZE, default: 5)
                HikariCP equivalent: minimumIdle = 5
            max_overflow: Max additional connections beyond pool_size (env: DB_MAX_OVERFLOW, default: 5)
                HikariCP equivalent: maximumPoolSize - minimumIdle = 10 - 5 = 5
            pool_timeout: Seconds to wait for a connection (env: DB_POOL_TIMEOUT, default: 30)
                HikariCP equivalent: connectionTimeout (not set in current config, recommended: 30000ms)
            pool_recycle: Seconds before recycling a connection (env: DB_POOL_RECYCLE, default: 480)
                HikariCP equivalent: maxLifetime = 480000ms (8 minutes)
        """
        self.host = host
        self.username = username
        self.password = password
        self.db_name = db_name
        self.pool_size = pool_size if pool_size is not None else int(os.getenv('DB_POOL_SIZE', '5'))
        self.max_overflow = max_overflow if max_overflow is not None else int(os.getenv('DB_MAX_OVERFLOW', '5'))
        self.pool_timeout = pool_timeout if pool_timeout is not None else int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.pool_recycle = pool_recycle if pool_recycle is not None else int(os.getenv('DB_POOL_RECYCLE', '480'))
        self._engine = None
        self._session_factory = None

    def get_engine(self):
        if not self._engine:
            # https://docs.sqlalchemy.org/en/14/core/pooling.html#dealing-with-disconnects
            self._engine = create_async_engine(self.get_url(),
                                               pool_pre_ping=True,
                                               pool_size=self.pool_size,
                                               max_overflow=self.max_overflow,
                                               pool_timeout=self.pool_timeout,
                                               pool_recycle=self.pool_recycle,
                                               pool_use_lifo=True,
                                               connect_args={},
                                               json_serializer=json_serializer
                                               )

        return self._engine

    def get_scoped_session(self, _ident_func):
        return async_scoped_session(self.get_session_factory(), scopefunc=_ident_func)

    def get_session_factory(self):
        if not self._session_factory:
            self._session_factory = async_sessionmaker(bind=self.get_engine())
        return self._session_factory

    def get_url(self) -> str:
        return "postgresql+asyncpg://{}:{}@{}/{}".format(
            self.username,
            self.password,
            self.host,
            self.db_name
        )
