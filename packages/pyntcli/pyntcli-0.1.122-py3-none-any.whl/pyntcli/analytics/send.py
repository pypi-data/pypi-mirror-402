import time
import platform
import socket
import subprocess

from pyntcli import __version__
from pyntcli.transport import pynt_requests
import pyntcli.log.log as log


PYNT_DEFAULT_USER_ID = "d9e3b82b-2900-43bf-8c8f-7ffe2f0cda36"
MIXPANEL_TOKEN = "05c26edb86084bbbb803eed6818cd8aa"
MIXPANEL_DOMAIN = "api-eu.mixpanel.com"
MIXPANEL_URL = f"https://{MIXPANEL_DOMAIN}/track?ip=1"

logger = log.get_logger()


def stop():
    if not AnalyticsSender._instance:
        return
    AnalyticsSender.instance().done()


def emit(event, properties=None):
    AnalyticsSender.instance().emit(event, properties)


def deferred_emit(event, properties=None):
    AnalyticsSender.instance().deferred_emit(event, properties)


def set_user_id(user_id):
    AnalyticsSender.instance().set_user_id(user_id)


CLI_START = "cli_start"
LOGIN_START = "cli_login_start"
LOGIN_DONE = "cli_login_done"
DOCKER_NATIVE_FLAG = "docker_native_flag"
CICD = "CI/CD"
ERROR = "error"
DOCKER_PLATFORM = "platform"


class AnalyticsSender():
    _instance = None

    def __init__(self, user_id=PYNT_DEFAULT_USER_ID) -> None:
        self.user_id = user_id
        self.version = __version__
        self.events = []
        self.disable_analytics = False

    @staticmethod
    def instance():
        if not AnalyticsSender._instance:
            AnalyticsSender._instance = AnalyticsSender()
            AnalyticsSender._instance.check_network_restrictions()

        return AnalyticsSender._instance

    def check_network_restrictions(self):
        try:
            result = subprocess.run(["ping", "-c", "1", MIXPANEL_DOMAIN], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            if result.returncode != 0:
                self.set_disable_analytics("ping return code not 0")
        except (socket.gaierror, subprocess.TimeoutExpired):
            self.set_disable_analytics("timeout")

    def set_disable_analytics(self, reason: str):
        self.disable_analytics = True
        logger.debug(f"Disabling analytics due to : {reason}")

    def base_event(self, event_type):
        return {
            "event": event_type,
            "properties": {
                "time": time.time(),
                "distinct_id": self.user_id,
                "$os": platform.platform(),
                "cli_version": self.version,
                "token": MIXPANEL_TOKEN
            }
        }

    def emit(self, event, properties):
        base_event = self.base_event(event)

        if properties:
            for k, v in properties.items():
                base_event["properties"][k] = v

        if self.user_id != PYNT_DEFAULT_USER_ID:
            if self.disable_analytics:
                logger.info(f"Analytics disabled, not sending: {base_event}")
            else:
                try:
                    pynt_requests.post(MIXPANEL_URL, json=[base_event])
                except Exception as e:
                    logger.error(f"Failed to send analytics event: {base_event}, error: {e}")
                    pass
        else:
            self.events.append(base_event)

    def deferred_emit(self, event, properties):
        base_event = self.base_event(event)

        if properties:
            for k, v in properties.items():
                base_event["properties"][k] = v

        self.events.append(base_event)

    def set_user_id(self, user_id):
        self.user_id = user_id
        for i, _ in enumerate(self.events):
            self.events[i]["properties"]["distinct_id"] = user_id
        self.done()

    def done(self):
        if self.events and not self.disable_analytics:
            try:
                pynt_requests.post(MIXPANEL_URL, json=self.events)
            except Exception as e:
                logger.error(f"Failed to send analytics events. error: {e}")
                pass

        self.events = []
