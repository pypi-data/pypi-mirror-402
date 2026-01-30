import time
import socket
import os
from contextlib import contextmanager
from pathlib import Path
import webbrowser
import json
import pyntcli.log.log as log
import pyntcli.store.store as store
from pyntcli.auth.login import PYNT_APP_URL

from pyntcli.commands.static_file_extensions import STATIC_FILE_EXTENSIONS
from pyntcli.pynt_docker import pynt_container
from pyntcli.ui import report, ui_thread
from pyntcli.transport import pynt_requests

logger = log.get_logger()


def is_http_handler(url):
    path = url.split("/")[-1]
    for ext in STATIC_FILE_EXTENSIONS:
        if ext in path:
            return False

    return True


def find_open_port() -> int:
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]


HEALTHCHECK_TIMEOUT = 60
HEALTHCHECK_INTERVAL = 0.1
GOT_INITIAL_HEALTHCHECK_MESSAGE = "Got initial pynt server health check"


def wait_for_healthcheck(address):
    ui_thread.print_verbose("Waiting for healthcheck...")
    start = time.time()
    while start + HEALTHCHECK_TIMEOUT > time.time():
        try:
            res = pynt_requests.get(address + "/healthcheck")

            logger.debug("Health check response: {}".format(res.status_code))
            if res.status_code == 418:
                return
        except:
            time.sleep(HEALTHCHECK_INTERVAL)

    logger.debug("Health check timed out!")
    ui_thread.print_verbose(f"Request to {address}/healthcheck timed out")
    raise TimeoutError()


def get_user_report_path(path, file_type):
    path = Path(path)
    if path.is_dir():
        return os.path.join(path, "pynt_results_{}.{}".format(int(time.time()), file_type))

    return os.path.join(str(path.parent), path.stem + ".{}".format(file_type))


class HtmlReportNotCreatedException(Exception):
    pass


class SomeFindingsOrWarningsException(Exception):
    pass


class SeverityException(Exception):
    pass


@contextmanager
def create_default_file_mounts(args):
    html_report_path = os.path.join(store.get_default_store_dir(), "results.html")
    json_report_path = os.path.join(store.get_default_store_dir(), "results.json")

    if "reporters" in args and args.reporters:
        html_report_path = os.path.join(os.getcwd(), "pynt_results.html")
        json_report_path = os.path.join(os.getcwd(), "pynt_results.json")

    mounts = []
    with open(html_report_path, "w", encoding="utf-8"), open(json_report_path, "w", encoding="utf-8"):
        mounts.append(pynt_container.create_mount(json_report_path, "/etc/pynt/results/results.json"))
        mounts.append(pynt_container.create_mount(html_report_path, "/etc/pynt/results/results.html"))

    yield mounts

    if os.stat(html_report_path).st_size == 0:
        raise HtmlReportNotCreatedException()

    if os.stat(html_report_path).st_size > 0:
        report.PyntReporter(json_report_path).print_summary()

    check_for_findings_or_warnings(args, json.load(open(json_report_path)))
    check_severity(args.severity_level, json.load(open(json_report_path)))


def open_report_from_file():
    html_report_path = os.path.join(store.get_default_store_dir(), "results.html")
    if not os.path.exists(html_report_path):
        raise FileNotFoundError(f"Report file not found: {html_report_path}")
    webbrowser.open("file://{}".format(html_report_path))


def build_scan_details_url(scan_id, app_id):
    if not scan_id or not app_id:
        return None
    return "{}/dashboard/application/{}/{}".format(PYNT_APP_URL,  app_id, scan_id)


# Deprecate - keep it for backward customers that use it
def check_for_findings_or_warnings(args, json_report):
    security_tests = json_report.get("securityTests", {})
    findings = security_tests.get("Findings", 0)
    warnings = security_tests.get("Warnings", 0)

    if "return_error" in args and args.return_error != "never" and findings != 0:
        raise SomeFindingsOrWarningsException()

    if "return_error" in args and args.return_error == "all-findings" and warnings != 0:
        raise SomeFindingsOrWarningsException()


def check_severity(severity_flag, json_report):
    severity_levels = ['medium', 'high', 'critical']

    if severity_flag is None or severity_flag.lower() == "none":
        return

    risk_data = json_report.get("securityTests", {})

    # Normalize all te keys to lower to reduce the risk that user input is diff then what we have internally
    risks_counter = {key.lower(): value for key, value in risk_data['RisksCounter'].items()}

    severity_filter = severity_flag.lower()

    if severity_filter == "all":
        severities_to_check = severity_levels
    else:
        if severity_filter not in severity_levels:
            raise ValueError(f"Invalid user filter for severity level: {severity_filter}")

        flag_index = severity_levels.index(severity_filter)
        severities_to_check = severity_levels[flag_index:]

    for severity in severities_to_check:
        if risks_counter.get(severity, 0) > 0:
            raise SeverityException(f"Severity '{severity}' has a count greater than 0.")
