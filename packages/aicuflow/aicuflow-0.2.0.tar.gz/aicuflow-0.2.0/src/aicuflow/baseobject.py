class AicuBaseObject:
    """
    Base object for easy handling like a dict or simplenamespace
    
    o = AicuBaseObject()
    o.a = "b"
    o["c"] = "d"
    o # AicuBaseObject(a='b', c='d')
    dict(o) # {'a': 'b', 'c': 'd'}
    """
    __hidden_slots__ = {"_client"}

    def __init__(self, _client=None, **kwargs):
        object.__setattr__(self, "_data", {})
        object.__setattr__(self, "_client", _client)
        for k, v in kwargs.items():
            self._data[k] = v

    # attribute access
    def __getattr__(self, item):
        if item in self.__hidden_slots__:
            return object.__getattribute__(self, item)
        try:
            return self._data[item]
        except KeyError:
            raise AttributeError(item)

    def __setattr__(self, key, value):
        if key in self.__hidden_slots__:
            object.__setattr__(self, key, value)
        else:
            self._data[key] = value

    def __delattr__(self, item):
        if item in self.__hidden_slots__:
            raise AttributeError(f"cannot delete hidden attribute {item}")
        del self._data[item]

    # dict-style access (never exposes hidden props)
    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
    
    def __contains__(self, key):
        return key in self._data

    def __delitem__(self, key):
        del self._data[key]

    def items(self):
        return self._data.items()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def __repr__(self):
        args = ", ".join(f"{k}={v!r}" for k, v in self._data.items())
        return f"{self.__class__.__name__}({args})"

    __str__ = __repr__

base = AicuBaseObject