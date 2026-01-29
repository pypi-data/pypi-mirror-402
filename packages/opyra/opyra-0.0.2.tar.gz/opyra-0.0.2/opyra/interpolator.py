import re
import typing

class Interpolator:
    """
    Parses strings (SQL) and dictionaries (NoSQL) to inject values 
    from a source object (like a Table/Document instance).
    """
    # Matches $var, @var, or :var
    _sql_pattern = re.compile(r'[\$@:]([a-zA-Z_]\w*)')

    @classmethod
    def parse_sql(cls, sql: str, source: typing.Any, style: str) -> typing.Tuple[str, typing.Any]:
        """
        :param style: 'numeric' (Postgres $1) or 'named' (SQLite :key)
        """
        vals = []
        found = {}
        
        # Helper to get value from dict or object
        def get_val(k):
            if isinstance(source, dict):
                return source.get(k)
            return getattr(source, k, None)

        def repl(match):
            key = match.group(1)
            val = get_val(key)
            
            if val is None:
                raise ValueError(f"Found '${key}' in SQL, but attribute is None or missing.")

            if style == 'numeric': 
                # Postgres: Replace $name with $1, $2... and build a list
                vals.append(val)
                return f"${len(vals)}"
            else: 
                # SQLite: Replace $name with :name and build a dict
                found[key] = val
                return f":{key}"
        
        clean_sql = cls._sql_pattern.sub(repl, sql)
        params = vals if style == 'numeric' else found
        return clean_sql, params

    @classmethod
    def parse_mongo(cls, data: typing.Any, source: typing.Any) -> typing.Any:
        """
        Recursively walks a dict/list. If a string starts with $,
        it replaces it with the attribute from source.
        """
        if isinstance(data, dict):
            return {k: cls.parse_mongo(v, source) for k, v in data.items()}
        
        elif isinstance(data, list):
            return [cls.parse_mongo(v, source) for v in data]
        
        elif isinstance(data, str) and data.startswith("$"):
            # The variable injection logic
            key = data[1:]
            # Check if source has this attribute
            if hasattr(source, key):
                return getattr(source, key)
            elif isinstance(source, dict) and key in source:
                return source[key]
            # If not found, return original string (might be a mongo operator like $set)
            return data
            
        return data

