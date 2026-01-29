from typing import Any, Type, Dict, Optional, TypeVar
import inflection
from .adapters.base import AbstractAdapter

# T = TypeVar("T", bound="Schema") but we optimize for circular imports
T = TypeVar("T")

class Repository:
    """
    The 'bound' interface for a model.
    Accessed via op.user
    """
    def __init__(self, op: 'Operation', model: Type[T], name: str):
        self._op = op
        self.model = model
        self.name = name

    async def find(self, pk: Any) -> Optional[T]:
        """
        Finds a record by primary key (ID).
        Delegate to the model's find_class but injecting the engine.
        """
        # We need to use the model's logic but ensure it uses OUR engine.
        # This calls Table.find_class(pk, engine=self._op)
        # Note: We need to update Table/Document to accept engine override.
        return await self.model.find_class(pk, engine=self._op)

    def __call__(self, **kwargs) -> T:
        """
        Factory method: op.user(name='alice')
        Creates an instance and binds it to the operation.
        """
        # Instantiate the model (msgspec struct)
        instance = self.model(**kwargs)
        
        # Inject the engine ("The Bloodline")
        # Note: Model must support this attribute assignment via descriptor/setattr logic
        instance._engine = self._op
        instance._changes = set()
        
        return instance

class Operation:
    """
    The orchestrator.
    """
    def __init__(self, url: str, schema: str = None):
        self.url = url
        self._schema = schema
        self._registry: Dict[str, Repository] = {}
        self._adapter: Optional[AbstractAdapter] = None

    @property
    async def adapter(self) -> AbstractAdapter:
        """
        Lazy loaded adapter
        """
        if self._adapter is None:
             self._adapter = await self._connect(self.url)
        return self._adapter

    async def connect(self):
        """
        Explicitly connect to the database.
        """
        if self._adapter is None:
            self._adapter = await self._connect(self.url)
        return self

    async def disconnect(self):
        """
        Explicitly disconnect from the database.
        """
        if self._adapter:
            await self._adapter.disconnect()
            self._adapter = None

    def schema(self, name: str) -> 'Operation':
        """
        Returns a lightweight clone of this Operation bound to a specific schema.
        """
        # Create a new instance
        new_op = Operation(self.url, schema=name)
        # Share the adapter and registry to avoid re-connection/re-registration
        new_op._adapter = self._adapter
        # We share the registry so 'op.schema('x').user' works if 'user' was registered on 'op'
        new_op._registry = self._registry
        return new_op

    async def _connect(self, url):
        if url.startswith("postgres") or url.startswith("sqlite"):
            from .adapters.sql import SQLAdapter
            return await SQLAdapter.connect(url)
        elif url.startswith("mongodb"):
            from .adapters.mongo import MongoAdapter
            return await MongoAdapter.connect(url)
        raise ValueError(f"Unsupported scheme: {url}")

    def register(self, model: Type[T], name: str = None) -> 'Operation':
        """
        Register a model (Table/Document) with this operation.
        """
        if name is None:
            # User -> user, CustomOrder -> custom_order
            name = inflection.underscore(model.__name__)
        
        repo = Repository(self, model, name)
        self._registry[name] = repo
        return self

    def __getattr__(self, name: str) -> Repository:
        if name in self._registry:
            return self._registry[name]
        # For nice error messages
        raise AttributeError(f"Model '{name}' not registered. Registered: {list(self._registry.keys())}")

    def __getitem__(self, name: str) -> Repository:
        return self.__getattr__(name)
