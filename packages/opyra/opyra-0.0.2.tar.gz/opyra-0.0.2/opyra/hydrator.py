import msgspec
import typing

class Hydrator:
    @classmethod
    def hydrate_row(cls, row: dict, model_cls: typing.Type[msgspec.Struct]) -> msgspec.Struct:
        """
        Takes a flat dict: {"name": "Alice", "group__name": "Admins"}
        Turns it into: {"name": "Alice", "group": {"name": "Admins"}}
        Then converts to the Model Struct.
        """
        nested_data = {}
        
        for key, value in row.items():
            if "__" in key:
                # Handle nested attributes (e.g., 'group__name')
                parts = key.split("__")
                current = nested_data
                for part in parts[:-1]:
                    # Create sub-dicts as we go down the path
                    current = current.setdefault(part, {})
                current[parts[-1]] = value
            else:
                # Handle root attributes
                nested_data[key] = value
                
        # Use msgspec's ultra-fast conversion to turn the dict into the Struct tree
        return msgspec.convert(nested_data, type=model_cls)

    @classmethod
    def hydrate_collection(cls, rows: list[dict], model_cls: typing.Type[msgspec.Struct]) -> list:
        return [cls.hydrate_row(row, model_cls) for row in rows]
