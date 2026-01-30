import tempfile
import pytest
import shutil

import sys 
sys.path.append("../")

@pytest.fixture
def mock_expanduser( mocker):
    dir = tempfile.mkdtemp() 
    try:
        mocker.patch("os.path.expanduser", return_value=dir)
        yield
    finally:
        shutil.rmtree(dir)

@pytest.fixture
def mock_sleep( mocker):
    try:
        mocker.patch("time.sleep", return_value=None)
        yield
    finally:
        pass

