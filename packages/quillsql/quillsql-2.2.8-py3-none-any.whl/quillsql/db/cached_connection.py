import psycopg2
import json
import redis
from quillsql.error import PgQueryError
from quillsql.db.db_helper import connect_to_db, run_query_by_db

# The TTL for new cache entries (default: 1h)
DEFAULT_CACHE_TTL = 24 * 60 * 60


class CachedConnection:
    def __init__(self, database_type, config, cache_config, using_connection_string):
        self.database_type = database_type
        self.using_connection_string = using_connection_string
        self.config = config
        self.connection = connect_to_db(database_type, config, using_connection_string)
        self.cache = self.get_cache(cache_config)
        self.ttl = cache_config and cache_config.get("ttl") or DEFAULT_CACHE_TTL
        self.orgId = None

    def get_cache(self, cache_config):
        cache_type = cache_config and cache_config.get("cache_type")
        if cache_type and cache_type == "redis" or cache_type == "rediss":
            return redis.Redis(
                host=cache_config.get("host", "localhost"),
                port=cache_config.get("port", 6379),
                username=cache_config.get("username", "default"),
                password=cache_config.get("password"),
            )
        return None

    def _is_connection_closed(self):
        return self.connection is None or getattr(self.connection, "closed", True)

    def _open_connection(self):
        self.connection = connect_to_db(
            self.database_type, self.config, self.using_connection_string
        )
        return self.connection

    def _close_connection(self):
        if self.connection is None:
            return
        try:
            self.connection.close()
        except Exception:
            pass
        finally:
            self.connection = None

    def exec_with_reconnect(self, sql):
        reconnect_count = 0
        last_error = None
        while reconnect_count < 10:
            try:
                if self._is_connection_closed():
                    self._open_connection()
                return run_query_by_db(self.database_type, sql, self.connection)
            except psycopg2.Error as err:
                last_error = err
                reconnect_count += 1
                self._close_connection()
            except Exception:
                self._close_connection()
                raise
        diag = getattr(last_error, "diag", None)
        position = getattr(diag, "statement_position", None)
        raise PgQueryError(last_error or "Failed to execute query", sql, position)

    def exec(self, sql):
        try:
            return self.exec_with_reconnect(sql)
        except psycopg2.Error as err:
            raise PgQueryError(err, sql, err.diag.statement_position)

    def query(self, sql):
        if not self.cache:
            return self.exec(sql)

        key = f"{self.orgId}:{self.sql}"
        cached_result = self.cache.get(key)
        if cached_result:
            cached = json.loads(cached_result)
            return {"rows": cached, "fields": cached["fields"]}
        else:
            new_result = self.exec(sql)
            new_result_string = json.dumps(new_result)
            self.cache.set(key, new_result_string, "EX", DEFAULT_CACHE_TTL)
            return {"rows": new_result, "fields": new_result["fields"]}
