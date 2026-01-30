import tempfile
import shutil
import pytest

from pyntcli.store import CredStore

class TestCredStore():
    def test_get_credentials(self, mock_expanduser):
        c = CredStore()
        c.put("data", "value")
        assert c.get("data") == "value" 
