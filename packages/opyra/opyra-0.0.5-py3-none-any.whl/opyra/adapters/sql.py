import typing
from .base import AbstractAdapter
from ..exceptions import ConfigurationError, ConnectivityError, QueryError

class SQLAdapter(AbstractAdapter):
    type = "sql"

    @classmethod
    async def connect(cls, url: str) -> "SQLAdapter":
        driver_name = ""
        conn = None
        
        if url.startswith("postgres://") or url.startswith("postgresql://"):
            driver_name = "postgres"
            try:
                import asyncpg
            except ImportError:
                raise ConfigurationError("pip install asyncpg to use Postgres")
            try:
                conn = await asyncpg.connect(url)
            except Exception as e:
                raise ConnectivityError(f"Could not connect to Postgres: {e}")

        elif url.startswith("sqlite://"):
            driver_name = "sqlite"
            try:
                import aiosqlite
                import sqlite3
            except ImportError:
                raise ConfigurationError("pip install aiosqlite to use SQLite")
            
            sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
            path = url.replace("sqlite://", "")
            conn = await aiosqlite.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
            conn.row_factory = aiosqlite.Row
            
        else:
            raise ConfigurationError(f"Unknown SQL scheme: {url}")
            
        return cls(driver_name, conn)

    def __init__(self, driver_name: str, connection: typing.Any):
        self.driver_name = driver_name
        self.conn = connection
        
        # Define parameter style for the Interpolator
        if driver_name == "postgres":
            self.param_style = "numeric" # uses $1, $2
        else:
            self.param_style = "named"   # uses :key

    async def fetch_all(self, sql: str, params: typing.Any) -> list[dict]:
        try:
            if self.driver_name == "postgres":
                # asyncpg params is a list/tuple
                rows = await self.conn.fetch(sql, *params)
                return [dict(r) for r in rows]
            
            elif self.driver_name == "sqlite":
                # aiosqlite params is a dict
                async with self.conn.execute(sql, params) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(r) for r in rows]
                    
        except Exception as e:
            raise QueryError(f"SQL Fetch failed: {e}") from e

    async def execute(self, sql: str, params: typing.Any) -> None:
        try:
            if self.driver_name == "postgres":
                await self.conn.execute(sql, *params)
            
            elif self.driver_name == "sqlite":
                await self.conn.execute(sql, params)
                await self.conn.commit() # SQLite requires explicit commit usually
                
        except Exception as e:
            raise QueryError(f"SQL Execute failed: {e}") from e


    async def insert(self, sql: str, params: typing.Any) -> typing.Any:
        """
        Executes INSERT and returns the new primary key.
        """
        try:
            if self.driver_name == "postgres":
                # We automatically append RETURNING id for PG
                # Assumption: PK is named 'id' or we need to pass it
                if "RETURNING" not in sql.upper():
                    sql += " RETURNING id"
                return await self.conn.fetchval(sql, *params)
            
            elif self.driver_name == "sqlite":
                cursor = await self.conn.execute(sql, params)
                await self.conn.commit()
                last_id = cursor.lastrowid
                await cursor.close()
                return last_id
                
        except Exception as e:
            raise QueryError(f"SQL Insert failed: {e}") from e

    async def disconnect(self):
        """
        Closes the database connection.
        """
        try:
            if self.driver_name == "postgres":
                 await self.conn.close()
            elif self.driver_name == "sqlite":
                 await self.conn.close()
        except Exception as e:
            # We log but generally don't raise here as shutdown should be graceful
            print(f"Error disconnecting: {e}")

# SQLConnection removed (Legacy Context Manager)
