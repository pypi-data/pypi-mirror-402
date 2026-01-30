class StoreConnector():
    def __init__(self, data) -> None:
        self._data = data 

    def get(self, key):
        raise NotImplemented()

    def put(self, key, value):
        raise NotImplementedError()
    
    def dump(self):
        raise NotImplementedError()

    @classmethod
    def default_value(cls):
        raise NotImplementedError()

