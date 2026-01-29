import typing

class QueryBuilder:
    """
    Stores the state of a query refinement chain.
    """
    def __init__(self):
        self.selected_fields: typing.List[str] = []
        self.filters: typing.Dict[str, typing.Any] = {}
        self.params: typing.Dict[str, typing.Any] = {}
        self.sorts: typing.List[str] = []
        self.limit_val: typing.Optional[int] = None

    def fields(self, *fields: str):
        self.selected_fields.extend(fields)
        return self

    def filter(self, **kwargs):
        """
        Adds generic filters. 
        For complex operators (e.g. price__gt), the interpolator/compiler will handle them.
        """
        self.filters.update(kwargs)
        return self

    def set_params(self, **kwargs):
        """
        Sets values for custom $variables.
        """
        self.params.update(kwargs)
        return self

    def asc(self, field: str):
        self.sorts.append(f"{field} ASC")
        return self

    def desc(self, field: str):
        self.sorts.append(f"{field} DESC")
        return self

    def limit(self, val: int):
        self.limit_val = val
        return self

class QueryWrapper:
    """
    Wraps a Model instance and a QueryBuilder to provide a fluent refinement API.
    Does not mutate the original instance.
    """
    def __init__(self, model_instance):
        self.model = model_instance
        self.qb = QueryBuilder()

    def fields(self, *fields: str):
        self.qb.fields(*fields)
        return self

    def filter(self, **kwargs):
        self.qb.filter(**kwargs)
        return self

    def asc(self, field: str):
        self.qb.asc(field)
        return self

    def desc(self, field: str):
        self.qb.desc(field)
        return self
        
    def limit(self, val: int):
        self.qb.limit(val)
        return self

    def set_params(self, **kwargs):
        self.qb.set_params(**kwargs)
        return self

    async def find(self):
        """
        Executes the query by calling back into the model.
        """
        return await self.model._find_with_builder(self.qb)
