import random
import string
from base64 import b64decode
import webbrowser
import urllib.parse
import datetime
import time
import json
import os

from pyntcli.ui import ui_thread
from pyntcli.store import CredStore
from pyntcli.transport import pynt_requests


class LoginException(Exception):
    pass


class Timeout(LoginException):
    pass


class InvalidTokenInEnvVarsException(LoginException):
    pass


PYNT_ID = "PYNT_ID"
PYNT_CREDENTIALS = "PYNT_CREDENTIALS"
PYNT_SAAS = os.environ.get("PYNT_SAAS_URL") if os.environ.get(
    "PYNT_SAAS_URL") else "https://api.pynt.io/v1"
PYNT_APP_URL = os.environ.get("PYNT_APP_URL") if os.environ.get(
    "PYNT_APP_URL") else "https://app.pynt.io"

def generate_device_code() -> str:
    """
    Generates a random 8 alphanumeric string of pattern `XXXX-XXXX`
    """
    part_one = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    part_two = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
    return f"{part_one}-{part_two}"


class Login():
    def __init__(self) -> None:
        self.delay = 5
        self.login_wait_period = (60 * 3)  # 3 minutes

    def create_login_request(self) -> str:
        device_code = generate_device_code()
        request_url = f"{PYNT_APP_URL}/login?" + urllib.parse.urlencode(
            {"device_code": device_code, "utm_source": "cli"})
        webbrowser.open(request_url)

        ui_thread.print(ui_thread.PrinterText("To continue, you need to log in to your account.")
                        .with_line("You will now be redirected to the login page.")
                        .with_line("")
                        .with_line("If you are not automatically redirected, please click on the link provided below (or copy to your web browser)")
                        .with_line(request_url))
        return device_code

    def claim_token_using_device_code(self, device_code: str):
        poll_url = f"{PYNT_SAAS}/auth/device-code/{device_code}"
        with ui_thread.spinner("Waiting...", "point"):
            start = time.time()
            while start + self.login_wait_period > time.time():
                response = pynt_requests.get(poll_url)
                if response.status_code == 200:
                    return response.json()
                time.sleep(self.delay)
            raise Timeout()

    def login(self):
        device_code = self.create_login_request()
        token = self.claim_token_using_device_code(device_code)
        with CredStore() as store:
            store.put("token", token)


def refresh_request(refresh_token):
    return pynt_requests.post(PYNT_SAAS + "/auth/refresh", json={"refresh_token": refresh_token})


def refresh_token():
    token = None
    with CredStore() as store:
        token = store.get("token")

    if not token:
        ui_thread.print_verbose("Token not found, logging in")
        Login().login()

    access_token = token.get("access_token")
    if access_token and not is_jwt_expired(access_token):
        return

    refresh = token.get("refresh_token", None)
    if not refresh:
        ui_thread.print_verbose("Refresh token not found, logging in")
        Login().login()
        return

    refresh_response = refresh_request(refresh)
    if refresh_response.status_code != 200:
        ui_thread.print_verbose("Failed to refresh token, logging in")
        Login().login()
        return

    with CredStore() as store:
        token["access_token"] = refresh_response.json()["token"]
        store.put("token", token)


def decode_jwt(jwt_token):
    splited = jwt_token.split(".")
    if len(splited) != 3:
        return None

    return json.loads(b64decode(splited[1] + '=' * (-len(splited[1]) % 4)))


def user_id():
    with CredStore() as store:
        token = store.get("token")
        if not token:
            return None

        decoded = decode_jwt(token["access_token"])
        if not decoded:
            return None

        return decoded.get("sub", None)

    return None


def is_jwt_expired(jwt_token):
    decoded = decode_jwt(jwt_token)
    if not decoded:
        return True

    exp = decoded.get("exp", None)
    if not exp:
        return True

    return datetime.datetime.fromtimestamp(exp) < datetime.datetime.now() + datetime.timedelta(minutes=1)


def validate_creds_structure(data):
    try:
        creds = json.loads(data.replace("\n", ""))
        token = creds.get("token", None)
        if not token:
            raise InvalidTokenInEnvVarsException()
        if not isinstance(token, dict):
            raise InvalidTokenInEnvVarsException()

        refresh_token = token.get("refresh_token", None)
        if not refresh_token:
            raise InvalidTokenInEnvVarsException()

        return token
    except json.JSONDecodeError:
        raise InvalidTokenInEnvVarsException()


def should_login():
    env_creds = os.environ.get(PYNT_ID, None)
    if not env_creds:
        env_creds = os.environ.get(PYNT_CREDENTIALS, None)
    if env_creds:
        validated_creds = validate_creds_structure(env_creds)
        with CredStore() as store:
            store.put("token", validated_creds)

    with CredStore() as store:
        token = store.get("token")

        if not token or token == store.connector.default_value:
            ui_thread.print_verbose("Token is default or not found")
            return True

        if not token.get("refresh_token"):
            ui_thread.print_verbose("Refresh token not found")
            return True

        return False
