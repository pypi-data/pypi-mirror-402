import typing
from .base import AbstractAdapter
from ..exceptions import ConfigurationError, ConnectivityError, QueryError

class MongoAdapter(AbstractAdapter):
    type = "nosql"
    param_style = "dict" # Not really used, but good for consistency

    @classmethod
    async def connect(cls, url: str) -> "MongoAdapter":
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
        except ImportError:
            raise ConfigurationError("pip install motor to use MongoDB")

        try:
            client = AsyncIOMotorClient(url)
            # Extract DB name from URL path, default to 'test' if missing
            db_name = url.split("/")[-1].split("?")[0] or "test"
            db_instance = client[db_name]
        except Exception as e:
            raise ConnectivityError(f"Could not connect to Mongo: {e}")
            
        return cls(db_instance)

    def __init__(self, db_instance):
        self.db = db_instance

    async def mongo_find(self, collection: str, query: dict) -> list[dict]:
        """
        Generic find wrapper.
        query is expected to be: {"filter": {...}, "sort": ...}
        """
        try:
            coll = self.db[collection]
            
            # Extract standard Mongo arguments
            filter_doc = query.get("filter", {})
            limit = query.get("limit", 0)
            
            cursor = coll.find(filter_doc)
            if limit:
                cursor = cursor.limit(limit)
                
            results = []
            async for doc in cursor:
                results.append(doc)
            return results
            
        except Exception as e:
            raise QueryError(f"Mongo Find failed: {e}") from e

    async def mongo_exec(self, collection: str, op: str, payload: dict) -> typing.Any:
        """
        Executes write operations.
        op: 'insert_one', 'update_many', 'delete_one', etc.
        """
        try:
            coll = self.db[collection]
            
            if op == "insert_one":
                res = await coll.insert_one(payload["document"])
                return res.inserted_id
                
            elif op == "update_one":
                await coll.update_one(payload["filter"], payload["update"])
                
            elif op == "update_many":
                await coll.update_many(payload["filter"], payload["update"])
                
            elif op == "delete_one":
                await coll.delete_one(payload["filter"])
                
            elif op == "replace_one":
                await coll.replace_one(payload["filter"], payload["replacement"])
                
            else:
                raise QueryError(f"Unsupported Mongo operation: {op}")
                
        except Exception as e:
            raise QueryError(f"Mongo Exec failed: {e}") from e

    # Conform to AbstractAdapter interface (stubs)
    async def fetch_all(self, *args, **kwargs): raise NotImplementedError
    async def execute(self, *args, **kwargs): raise NotImplementedError

    async def disconnect(self):
        """
        Closes the MongoDB client.
        """
        self.db.client.close()


# MongoConnection removed (Legacy Context Manager)

