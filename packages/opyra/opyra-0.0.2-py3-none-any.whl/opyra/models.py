import msgspec
import typing
# from .core import Operation # Circular dep likely if core imports models? No, core uses TypeVar.
# But models imports core.
if typing.TYPE_CHECKING:
    from .core import Operation
from .interpolator import Interpolator
from .exceptions import QueryError
from .utils import HybridMethod
from .query import QueryBuilder, QueryWrapper
from .hydrator import Hydrator

class ModelMeta(type(msgspec.Struct)):
    def __new__(mcs, name, bases, namespace, **kwargs):
        # 1. Capture Annotations
        annotations = namespace.get('__annotations__', {})
        
        # 2. Identify and Relax Required Fields
        required_fields = set()
        new_annotations = {}
        
        # We also need to inherit required fields from bases if we want strictness,
        # but for now we just handle the current class's definitions.
        # msgspec merges fields, so we only see 'local' annotations here?
        # Yes, __annotations__ are local.
        
        for k, v in annotations.items():
            new_annotations[k] = typing.Optional[v]
            
            # If no default value provided in class body, it's required
            if k not in namespace:
                required_fields.add(k)
                namespace[k] = None # Relax it to None
                
        namespace['__annotations__'] = new_annotations
        
        # 3. Store metadata
        # We merge with base 'required' if exists
        # Actually bases are not fully formed when inspecting strict fields?
        # Simpler: Just store local required. validate() can walk MRO.
        namespace['_local_required_fields'] = required_fields
        
        return super().__new__(mcs, name, bases, namespace, **kwargs)

class Table(msgspec.Struct, kw_only=True, metaclass=ModelMeta):
    """
    Base class for SQL Models.
    """
    # Internal Registry/Engine State
    _engine: typing.Optional[typing.Any] = None
    _changes: typing.Optional[typing.Set[str]] = None

    # id field is expected to be defined by subclass
    # id: typing.Optional[int] = None

    def __setattr__(self, key: str, value: typing.Any):
        # Allow setting internal fields without tracking
        # Just check if it handles it?
        track = True
        if key.startswith('_'):
            track = False

        if track and hasattr(self, '_changes') and self._changes is not None:
             self._changes.add(key)
        
        # Delegate to descriptor to avoid infinite recursion or object.__setattr__ error
        # Msgspec structs usually have descriptors for fields.
        cls = type(self)
        if hasattr(cls, key):
            desc = getattr(cls, key)
            if hasattr(desc, '__set__'):
                desc.__set__(self, value)
                return
        
        # Fallback (e.g. if __dict__ is somehow enabled or external attr?)
        # For msgspec, this usually will fail if not a field, unless dict=True matches?
        # Let's try object.__setattr__ as last resort, unlikely to work per test.
        # But if we are here, we might be setting something not in fields.
        super().__setattr__(key, value)

    @classmethod
    def table_name(cls) -> str:
        """Defaults to class name lowercase + 's'. Override if needed."""
        return cls.__name__.lower() + "s"

    @classmethod
    def _analyze_fields(cls) -> list[dict]:
        """
        Inspects fields to find relationships (Blueprint Path).
        """
        relations = []
        for name in cls.__struct_fields__:
            typ = cls.__annotations__.get(name)
            if not typ: continue
            
            target_cls = None
            # Unwrap Optional[Table] or just Table
            origin = typing.get_origin(typ)
            args = typing.get_args(typ)
            
            if origin is typing.Union:
                for arg in args:
                    if isinstance(arg, type) and issubclass(arg, Table) and arg is not cls:
                        target_cls = arg
                        break
            elif isinstance(typ, type) and issubclass(typ, Table):
                 target_cls = typ
            
            if target_cls:
                relations.append({
                    "field": name,
                    "model": target_cls,
                    "kind": "fk" # Assumption: User.profile -> users.profile_id
                })
        return relations

    @classmethod
    def _build_select_sql(cls, conditions: list[str], sorts: list[str], limit: int | None, fields: list[str] = None, schema: str = None) -> str:
        """
        Constructs SELECT ... JOIN ... WHERE ...
        """
        t_main = cls.table_name()
        if schema:
            t_main = f"{schema}.{t_main}"
        
        if fields:
            cols = []
            for f in fields:
                if "." not in f:
                    cols.append(f"{t_main}.{f}")
                else:
                    cols.append(f)
        else:
            relations = cls._analyze_fields()
            rel_names = {r['field'] for r in relations}
            
            cols = []
            for f in cls.__struct_fields__:
                if f in ('_engine', '_changes'): continue
                if f not in rel_names:
                    cols.append(f"{t_main}.{f}")

        joins = []
        
        if not fields:
             if 'relations' not in locals():
                  relations = cls._analyze_fields()
             
             for rel in relations:
                t_join = rel['model'].table_name()
                if schema:
                    t_join = f"{schema}.{t_join}"
                
                fk_col = f"{rel['field']}_id" 
                
                joins.append(f"LEFT JOIN {t_join} ON {t_main}.{fk_col} = {t_join}.id")
                
                for f in rel['model'].__struct_fields__:
                    cols.append(f"{t_join}.{f} AS {rel['field']}__{f}")
                
        sql = f"SELECT {', '.join(cols)} FROM {t_main} {' '.join(joins)}"
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
            
        if sorts:
            sql += " ORDER BY " + ", ".join(sorts)
            
        if limit and limit > 0:
            sql += f" LIMIT {limit}"
            
        return sql

    # --- Refinement Path ---
    def fields(self, *fields: str):
        return QueryWrapper(self).fields(*fields)

    def filter(self, **kwargs):
        return QueryWrapper(self).filter(**kwargs)

    def asc(self, field: str):
        return QueryWrapper(self).asc(field)

    def desc(self, field: str):
        return QueryWrapper(self).desc(field)
        
    def limit(self, val: int):
        return QueryWrapper(self).limit(val)

    def set_params(self, **kwargs):
        return QueryWrapper(self).set_params(**kwargs)

    # --- Hybrid Find ---
    @classmethod
    async def find_class(cls, pk: typing.Any, engine: typing.Optional["Operation"] = None) -> typing.Optional["Table"]:
        """
        Class Method: Finds a record by ID.
        Must be called via repository: await op.user.find(1) (which passes engine).
        """
        if not engine:
            raise RuntimeError(f"Cannot find {cls.__name__} without an engine. Use 'await op.{cls._analyze_fields.__name__}.find()' or similar.")
        
    @classmethod
    async def find_class(cls, pk: typing.Any, engine: typing.Optional["Operation"] = None) -> typing.Optional["Table"]:
        """
        Class Method: Finds a record by ID.
        Must be called via repository: await op.user.find(1) (which passes engine).
        """
        if not engine:
            raise RuntimeError(f"Cannot find {cls.__name__} without an engine. Use 'await op.{cls._analyze_fields.__name__}.find()' or similar.")
        
        db = await engine.adapter
        if db.type != 'sql':
            raise TypeError(f"Cannot use Table {cls.__name__} with a NoSQL connection.")

        # Re-use the smart builder
        schema = getattr(engine, '_schema', None)
        t_name = cls.table_name()
        if schema:
            t_name = f"{schema}.{t_name}"
            
        sql = cls._build_select_sql([f"{t_name}.id = $pk"], [], 1, schema=schema)
        clean_sql, params = Interpolator.parse_sql(sql, {"pk": pk}, db.param_style)
        
        rows = await db.fetch_all(clean_sql, params)
        if rows:
            # Hydrate and INJECT ENGINE
            obj = Hydrator.hydrate_row(rows[0], cls)
            # Use property setter now that __setattr__ handles it
            obj._engine = engine
            obj._changes = set()
            return obj
        return None

    async def find_instance(self) -> typing.List["Table"]:
        """
        Instance Method: Executes search based on template.
        """
        return await self._find_with_builder(None)

    async def _find_with_builder(self, qb: typing.Optional[QueryBuilder]) -> typing.List["Table"]:
        """
        Internal: Executes search combining template + builder.
        """
        if not self._engine:
            raise RuntimeError("Cannot query with detached instance. Create via 'op.user(...)'")
        
        db = await self._engine.adapter
        schema = getattr(self._engine, '_schema', None)
        
        t_name = self.table_name()
        if schema:
            t_name = f"{schema}.{t_name}"

        # Build dictionary of all params (template + explicit)
        all_params = {}
        conditions = []
        
        # 1. Template Params
        # Exclude _engine to avoid serialization error
        raw_data = {f: getattr(self, f) for f in self.__struct_fields__ if f not in ('_engine', '_changes')}
        data = msgspec.to_builtins(raw_data)
        for k, v in data.items():
            if k == 'id' and v is None: continue
            if v is not None:
                # Disambiguate column with table name
                conditions.append(f"{t_name}.{k} = $t_{k}")
                all_params[f"t_{k}"] = v

        # 2. Builder Params
        qs_limit = None
        qs_sorts = []
        
        if qb:
            for k, v in qb.filters.items():
                # If key doesn't have a dot, assume main table
                col = k if "." in k else f"{t_name}.{k}"
                conditions.append(f"{col} = $f_{k}")
                all_params[f"f_{k}"] = v
                
            all_params.update(qb.params)
            qs_limit = qb.limit_val
            qs_sorts = qb.sorts

        # 3. Build SQL with Joins
        qs_fields = qb.selected_fields if qb else None
        
        sql = self._build_select_sql(conditions, qs_sorts, qs_limit, qs_fields, schema=schema)

        clean_sql, params = Interpolator.parse_sql(sql, all_params, db.param_style)
        rows = await db.fetch_all(clean_sql, params)
        
        return Hydrator.hydrate_collection(rows, self.__class__)

    # The Descriptor
    find = HybridMethod(find_class, find_instance)

    # --- Hydration Path ---
    async def load(self):
        """
        Reloads the object from the database using its ID.
        """
        if not self.id:
            raise ValueError("Cannot load object without an ID")
            
        fresh = await self.find_class(self.id)
        if fresh:
            # Update self in-place
            for f in self.__struct_fields__:
                val = getattr(fresh, f)
                setattr(self, f, val)

    @classmethod
    async def query(cls, sql: str, engine: typing.Optional["Operation"] = None, **kwargs) -> typing.List["Table"]:
        """
        Execute raw SQL and return a list of typed Table instances.
        Usage: await op.user.query("SELECT ...") -- wait, repo needs to expose this.
        Or directly: await Table.query("...", engine=op)
        """
        if not engine:
             raise RuntimeError("Engine required for raw query.")
        
        db = await engine.adapter
        clean_sql, params = Interpolator.parse_sql(sql, kwargs, db.param_style)
        
        rows = await db.fetch_all(clean_sql, params)
        # Hydrate manually to inject engine
        results = Hydrator.hydrate_collection(rows, cls)
        for r in results:
             r._engine = engine
             r._changes = set()
        return results

    async def execute(self, sql: str):
        """
        Execute SQL using THIS instance as the variable source.
        Usage: user.execute("UPDATE users SET name = 'New' WHERE id = $id")
        """
        if not self._engine:
             raise RuntimeError("Detached instance.")
        
        db = await self._engine.adapter
        clean_sql, params = Interpolator.parse_sql(sql, self, db.param_style)
        await db.execute(clean_sql, params)

    async def save(self):
        """
        Smart Insert/Update logic.
        """
        self.validate()
        if not self._engine:
             raise RuntimeError("Cannot save detached instance. Use 'op.user(...)' to create.")
        
        db = await self._engine.adapter
        
    async def save(self):
        """
        Smart Insert/Update logic.
        """
        self.validate()
        if not self._engine:
             raise RuntimeError("Cannot save detached instance. Use 'op.user(...)' to create.")
        
        db = await self._engine.adapter
        schema = getattr(self._engine, '_schema', None)
        
        # DIRTY TRACKING OPTIMIZATION
        # If we have an ID (Update), only update changed fields!
        # If no ID (Insert), insert all fields (except default nones).
        
        # DIRTY TRACKING OPTIMIZATION
        # If we have an ID (Update), only update changed fields!
        # If no ID (Insert), insert all fields (except default nones).
        
        # Exclude _engine to avoid serialization error
        raw_data = {f: getattr(self, f) for f in self.__struct_fields__ if f not in ('_engine', '_changes')}
        data = msgspec.to_builtins(raw_data)
        
        f_table = self.table_name()
        if schema:
            f_table = f"{schema}.{f_table}"
        
        if self.id is None:
            # INSERT
            # Remove 'id' so DB auto-increments it
            data.pop('id', None)
            cols = ", ".join(data.keys())
            
            # Temporary syntax $key which Interpolator fixes per driver
            vals = ", ".join([f"${k}" for k in data.keys()])
            
            sql = f"INSERT INTO {f_table} ({cols}) VALUES ({vals})"
            
            # Note: Getting the ID back is driver-specific (RETURNING vs cursor.lastrowid).
            # We now use db.insert() which handles this abstraction.
            clean_sql, params = Interpolator.parse_sql(sql, data, db.param_style)
            self.id = await db.insert(clean_sql, params)
            
            # Reset changes to clean
            if self._changes is not None: self._changes.clear()
            
        else:
            # UPDATE
            # Only update changed fields if tracking is active
            if self._changes:
                updates = ", ".join([f"{k} = ${k}" for k in self._changes if k != 'id'])
                if not updates:
                     return # Nothing to update
                
                sql = f"UPDATE {f_table} SET {updates} WHERE id = $id"
                
                # We need data for the changed keys + id
                update_data = {k: getattr(self, k) for k in self._changes}
                update_data['id'] = self.id
                
                clean_sql, params = Interpolator.parse_sql(sql, update_data, db.param_style)
                await db.execute(clean_sql, params)
                self._changes.clear()
            else:
                # No changes detected, maybe we should just return?
                # Or fallback to full update if _changes is None?
                # Assuming full update if _changes is unexpectedly empty/None but user called save?
                # No, if _changes is empty set, we do nothing.
                pass

    def validate(self):
        """
        Ensures all required fields are present (not None).
        Traverses MRO to find all _local_required_fields.
        """
        # Walk MRO to find all _local_required_fields
        for cls in self.__class__.__mro__:
            req = getattr(cls, '_local_required_fields', set())
            for f in req:
                if getattr(self, f) is None:
                     # Check if it's 'id'. 'id' is special, handled by DB (auto-increment).
                     if f == 'id': continue
                     raise ValueError(f"Missing required field: {f}")


class Document(msgspec.Struct, kw_only=True, metaclass=ModelMeta):
    """
    Base class for NoSQL (MongoDB) Models.
    """
    # Internal Registry/Engine State
    _engine: typing.Optional[typing.Any] = None
    _changes: typing.Optional[typing.Set[str]] = None

    # id field is expected to be defined by subclass
    # id: typing.Optional[str] = None
    
    def __setattr__(self, key: str, value: typing.Any):
        track = True
        if key.startswith('_'): track = False

        if track and hasattr(self, '_changes') and self._changes is not None:
            self._changes.add(key)
        
        cls = type(self)
        if hasattr(cls, key):
            desc = getattr(cls, key)
            if hasattr(desc, '__set__'):
                desc.__set__(self, value)
                return
        super().__setattr__(key, value)
    # id field is expected to be defined by subclass
    # id: typing.Optional[str] = None

    # --- Refinement Path ---
    def fields(self, *fields: str):
        return QueryWrapper(self).fields(*fields)

    def filter(self, **kwargs):
        return QueryWrapper(self).filter(**kwargs)

    def asc(self, field: str):
        return QueryWrapper(self).asc(field)

    def desc(self, field: str):
        return QueryWrapper(self).desc(field)
        
    def limit(self, val: int):
        return QueryWrapper(self).limit(val)

    def set_params(self, **kwargs):
        return QueryWrapper(self).set_params(**kwargs)

    @classmethod
    def collection_name(cls) -> str:
        return cls.__name__.lower() + "s"

    @classmethod
    async def find_class(cls, pk: str, engine: typing.Optional["Operation"] = None) -> typing.Optional["Document"]:
        if not engine:
            raise RuntimeError(f"Engine required. Use 'op.{cls.collection_name()}.find()'.")

        db = await engine.adapter
        if db.type != 'nosql':
            raise TypeError(f"Cannot use Document {cls.__name__} with a SQL connection.")

        rows = await db.mongo_find(cls.collection_name(), {"filter": {"_id": pk}})
        if rows:
            obj = Hydrator.hydrate_row(rows[0], cls)
            obj._engine = engine
            obj._changes = set()
            return obj
        return None

    async def find_instance(self) -> typing.List["Document"]:
        """
        Instance Method for Template Search (Mongo).
        """
        return await self._find_with_builder(None)

    async def _find_with_builder(self, qb: typing.Optional[QueryBuilder]) -> typing.List["Document"]:
        """
        Internal: Executes search combining template + builder.
        """
        if not self._engine:
             raise RuntimeError("Detached instance.")
        db = await self._engine.adapter
        
        # 1. Build Filter 
        filter_doc = {}
        
        # Template fields 
        # Exclude _engine to avoid serialization error
        raw_data = {f: getattr(self, f) for f in self.__struct_fields__ if f not in ('_engine', '_changes')}
        data = msgspec.to_builtins(raw_data)
        for k, v in data.items():
            if k == 'id': continue
            if v is not None:
                filter_doc[k] = v 

        qs_limit = 0
        
        if qb:
            # Explicit filters
            for k, v in qb.filters.items():
                filter_doc[k] = v
            qs_limit = qb.limit_val or 0

        # 2. Build Query Payload
        query = {"filter": filter_doc}
        
        if qs_limit:
            query["limit"] = qs_limit
            
        rows = await db.mongo_find(self.collection_name(), query)
        results = Hydrator.hydrate_collection(rows, self.__class__)
        for r in results:
             r._engine = self._engine
             r._changes = set()
        return results

    # The Descriptor
    find = HybridMethod(find_class, find_instance)

    # --- Hydration Path ---
    async def load(self):
        """
        Reloads the object from the database using its ID.
        """
        if not self.id:
            raise ValueError("Cannot load object without an ID")
            
        fresh = await self.find_class(self.id)
        if fresh:
            for f in self.__struct_fields__:
                val = getattr(fresh, f)
                setattr(self, f, val)

    async def execute(self, command: dict):
        """
        Run a Mongo command dict with variable injection.
        Usage: 
        user.execute({
            "update_one": {
                "filter": {"_id": "$id"}, 
                "update": {"$set": {"status": "active"}}
            }
        })
        """
        if not self._engine:
             raise RuntimeError("Detached instance.")
        db = await self._engine.adapter
        
        # Inject variables from 'self'
        clean_cmd = Interpolator.parse_mongo(command, self)
        
        # Command structure: { "op_name": { ...payload... } }
        if not clean_cmd: return
        
        op = list(clean_cmd.keys())[0]
        payload = clean_cmd[op]
        
        await db.mongo_exec(self.collection_name(), op, payload)

    async def save(self):
        """
        Upsert logic for Mongo.
        """
        self.validate()
        if not self._engine:
             raise RuntimeError("Detached instance.")
        db = await self._engine.adapter
        
        db = await self._engine.adapter
        
        # Exclude _engine to avoid serialization error
        raw_data = {f: getattr(self, f) for f in self.__struct_fields__ if f not in ('_engine', '_changes')}
        data = msgspec.to_builtins(raw_data)
        
        # We need to ensure 'id' is treated as '_id' for Mongo
        if self.id:
            oid = data.pop('id')
            
            # Optimization: Only update changed fields if tracking active
            if self._changes:
                # Build $set payload
                update_fields = {k: getattr(self, k) for k in self._changes if k != 'id'}
                if not update_fields:
                     return # No changes
                
                await db.mongo_exec(self.collection_name(), "update_one", {
                    "filter": {"_id": oid},
                    "update": {"$set": update_fields}
                })
                self._changes.clear()
            else:
                 # Fallback/pass if no changes?
                 pass
                 
        else:
            # Insert new
            if 'id' in data: data.pop('id') # Let Mongo generate _id
            
            # For a real lib, you'd want the new _id back.
            # Here we wrap it in a generic insert_one op and capture the result
            new_id = await db.mongo_exec(self.collection_name(), "insert_one", {
                "document": data
            })
            self.id = str(new_id)
            if self._changes is not None: self._changes.clear()

    def validate(self):
        for cls in self.__class__.__mro__:
            req = getattr(cls, '_local_required_fields', set())
            for f in req:
                if getattr(self, f) is None:
                     if f == 'id': continue
                     raise ValueError(f"Missing required field: {f}")
