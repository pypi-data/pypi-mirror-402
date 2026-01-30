from typing import Type
import os

from .json_connector import JsonStoreConnector
from .store_connector import StoreConnector


def get_default_store_dir():
    return os.path.join(os.path.expanduser("~"), ".pynt")


class Store():
    def __init__(self, file_location: str, connector_type: Type[StoreConnector]) -> None:
        self.file_location = file_location
        self.connector: StoreConnector = None
        self._file = None
        self._connector_type = connector_type

    def _get_file_data(self):
        if self.connector:
            return

        dirname = os.path.dirname(self.file_location)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        if not os.path.exists(self.file_location):
            with open(self.file_location, "w") as f:
                self.connector = self._connector_type(
                    self._connector_type.default_value())
                return

        with open(self.file_location, "r+") as f:
            self.connector = self._connector_type(f.read())

    def get(self, key):
        self._get_file_data()
        return self.connector.get(key)

    def put(self, key, value):
        self._get_file_data()
        self.connector.put(key, value)

    def get_path(self):
        return self.file_location

    def __enter__(self):
        self._get_file_data()
        return self

    def __exit__(self, type, value, traceback):
        with open(self.file_location, "w") as f:
            f.write(self.connector.dump())


class CredStore(Store):
    def __init__(self) -> None:
        pynt_dir = get_default_store_dir()
        super().__init__(file_location=os.path.join(pynt_dir, "creds.json"),
                         connector_type=JsonStoreConnector)

    def get_access_token(self):
        return self.get("token")["access_token"]

    def get_token_type(self):
        return self.get("token")["token_type"]

    def get_tokens(self):
        all_tokens = self.get("token")
        token_to_json_string = '{"token":' + \
            str(all_tokens).replace("\'", "\"") + "}"
        return token_to_json_string


class StateStore(Store):
    def __init__(self) -> None:
        pynt_dir = get_default_store_dir()
        super().__init__(file_location=os.path.join(pynt_dir, "state.json"),
                         connector_type=JsonStoreConnector)

    def get_prompts_history(self):
        return self.get("prompts_history") or {}

    def put_prompts_history(self, value):
        return self.put("prompts_history", value)
