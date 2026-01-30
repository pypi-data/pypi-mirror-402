import json

from .store_connector import StoreConnector

class JsonStoreConnector(StoreConnector):
    def __init__(self, data) -> None:
        if not data:
            data = JsonStoreConnector.default_value()
        super().__init__(data)
        self.json = json.loads(self._data)

    def get(self, key):
        return self.json.get(key, None)

    def put(self, key, value):
       self.json[key] = value
    
    def dump(self):
        return json.dumps(self.json, indent=2)

    @staticmethod
    def default_value():
        return json.dumps({})
