from urllib.parse import urlparse
import json
from _pytest.monkeypatch import monkeypatch
import pytest
import requests
import requests_mock
import datetime
import jwt
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from pyntcli.auth.login import Login, Timeout, InvalidTokenInEnvVarsException, is_jwt_expired, should_login, PYNT_ID, PYNT_CREDENTIALS
from pyntcli.store import CredStore


class TestLogin():
    @pytest.fixture
    def mock_webbrowser(self, mocker):
        try:
            mocker.patch("webbrowser.open", return_value=None)
            yield
        finally:
            pass

    def get_request_url_parameters(self, req: requests.PreparedRequest):
        u = req.url
        parsed_url = urlparse(u)
        return parsed_url.query

    def poll_matcher(self, request: requests.PreparedRequest):
        assert "request_id" in self.get_request_url_parameters(request)

        resp = requests.Response()
        self.login_request_cnt += 1
        if self.login_request_cnt < 2:
            resp.status_code = 404
            return resp

        resp.status_code = 200
        resp._content = json.dumps({"token": "testToken"}).encode()
        return resp

    def test_login(self, mock_webbrowser, mock_sleep, mock_expanduser):
        l = Login()
        self.login_request_cnt = 0
        with requests_mock.mock() as m:
            m.add_matcher(self.poll_matcher)
            l.login()

        assert self.login_request_cnt == 2
        c = CredStore()
        assert c.get("token") == {"token": "testToken"}

    def test_login_timeout(self, mock_webbrowser, mock_sleep, mock_expanduser):
        l = Login()
        l.login_wait_period = 0
        self.login_request_cnt = 0
        with pytest.raises(Timeout):
            with requests_mock.mock() as m:
                m.add_matcher(self.poll_matcher)
                l.claim_token_using_device_code("some_id")

    def test_is_jwt_expired(self):

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        ).private_bytes(encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption())

        token_data = {
            "exp": int((datetime.datetime.now() - datetime.timedelta(days=1)).timestamp())
        }

        token = jwt.encode(token_data, private_key.decode(),
                           algorithm="RS256").decode("utf-8")
        assert is_jwt_expired(token) == True

        token_data = {
            "exp": int((datetime.datetime.now() + datetime.timedelta(days=1)).timestamp())
        }

        token = jwt.encode(token_data, private_key.decode(),
                           algorithm="RS256").decode("utf-8")
        assert is_jwt_expired(token) == False

    def test_login_using_pynt_id_env_vars(self, mocker, mock_expanduser):
        creds = json.dumps({"token": {"refresh_token": "some data"}})
        mocker.patch.dict(os.environ, {PYNT_ID: creds})
        assert should_login() == False

        os.environ[PYNT_ID] = "some bad credentials"
        with pytest.raises(InvalidTokenInEnvVarsException):
            should_login()

    def test_login_using_pynt_cred_env_vars(self, mocker, mock_expanduser):
        creds = json.dumps({"token": {"refresh_token": "some data"}})
        mocker.patch.dict(os.environ, {PYNT_CREDENTIALS: creds})
        assert should_login() == False

        os.environ[PYNT_CREDENTIALS] = "some bad credentials"
        with pytest.raises(InvalidTokenInEnvVarsException):
            should_login()

    def test_should_login_no_env_var(self, mocker, mock_expanduser):
        assert should_login() == True
