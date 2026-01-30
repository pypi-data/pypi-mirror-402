import argparse
from copy import deepcopy
import os
import webbrowser
from http import HTTPStatus
import time
import tempfile
import json
from subprocess import Popen, PIPE
from functools import partial
import xmltodict
import base64

from pyntcli.store import store

import pyntcli.log.log as log
from xml.parsers.expat import ExpatError

from pyntcli.pynt_docker import pynt_container
from pyntcli.ui import ui_thread
from pyntcli.commands import util, sub_command
from pyntcli.ui import report as cli_reporter
from pyntcli.transport import pynt_requests

methods = [
    "get",
    "post",
    "put",
    "delete",
    "patch",
    "options",
    "head",
    "trace",
    "connect",
]

logger = log.get_logger()
supported_encoding = ["utf-8", "latin1", "utf-16", "cp1252"]


def is_valid_method(method: str):
    if method.lower() in methods:
        return True
    return False


def decode_request(item) -> str:
    error = None
    for encoding in supported_encoding:
        try:
            return base64.b64decode(item["request"]["#text"]).decode(encoding)
        except UnicodeDecodeError as e:
            error = e
            ui_thread.print_verbose(f"Error decoding request: {e}, skipping...")
            continue
        except Exception as e:
            error = e
            ui_thread.print_verbose(f"Error decoding request: {e}, breaking...")
            break

    ui_thread.print(
        ui_thread.PrinterText(
            f"Error decoding request: {error}"),
        ui_thread.PrinterText.WARNING)
    logger.error(f"Error decoding request: {error}")

    raise e


def replay_req(item, proxy_port):
    url = item["url"]
    if not util.is_http_handler(url):
        return None

    decoded_req = decode_request(item)

    method = decoded_req.split("\r\n")[0].split(" ")[0]

    if not is_valid_method(method):
        return

    lines = decoded_req.split("\r\n")
    if len(lines) < 2:
        return

    headers = {}

    for line in lines[1:]:
        if not line:
            break

        if ": " not in line:
            break

        key, value = line.split(": ")
        headers[key] = value

    body = decoded_req.split("\r\n\r\n")[1]
    if body:
        body = body.encode("utf-8")
    resp = pynt_requests.request_from_xml(
        method=method,
        url=url,
        headers=headers,
        data=body,
        proxies={
            "http": "127.0.0.1:{}".format(proxy_port),
            "https": "127.0.0.1:{}".format(proxy_port),
        },
    )
    ui_thread.print(ui_thread.PrinterText(resp))


def run_burp_xml(doc, proxy_port):
    items = doc["items"]["item"]
    ui_thread.print(ui_thread.PrinterText("Creating traffic from xml file"))
    if isinstance(items, dict):
        replay_req(item=items, proxy_port=proxy_port)
    else:
        [replay_req(i, proxy_port=proxy_port) for i in doc["items"]["item"]]


def parse_xml(xml_path):
    try:
        with open(xml_path) as fd:
            return xmltodict.parse(fd.read())
    except ExpatError:
        return None


def is_valid_xml(doc) -> bool:
    return "items" in doc


def burp_usage():
    return (
        ui_thread.PrinterText(
            "Burp integration to Pynt. Run a security scan with a given burp xml output file."
        )
        .with_line("")
        .with_line("Usage:", style=ui_thread.PrinterText.HEADER)
        .with_line("\tpynt burp [OPTIONS]")
        .with_line("")
        .with_line("Options:", style=ui_thread.PrinterText.HEADER)
        .with_line("\t--xml - Path to the xml to run tests on")
        .with_line('\t--captured-domains - Pynt will scan only these domains and subdomains. For all domains write "*"')
        .with_line("\t--port - Set the port pynt will listen to (DEFAULT: random)")
        .with_line("\t--ca-path - The path to the CA file in PEM format")
        .with_line("\t--report - If present will save the generated report in this path.")
        .with_line("\t--insecure - Use when target uses self signed certificates")
        .with_line("\t--application-id - Attach the scan to an application, you can find the ID in your applications area at app.pynt.io")
        .with_line("\t--application-name - Attach the scan to an application, application will be created automatically if it does not exist.")
        .with_line("\t--host-ca - Path to the CA file in PEM format to enable SSL certificate verification for pynt when running through a VPN.")
        .with_line("\t--severity-level - 'all', 'medium', 'high', 'critical', 'none' (default) ")
        .with_line("\t--tag - Tag the scan. Repeat for multiple tags")
        .with_line("\t--verbose - Use to get more detailed information about the run")
    )


class BurpCommand(sub_command.PyntSubCommand):
    def __init__(self, name) -> None:
        super().__init__(name)
        self.scan_id = ""
        self.proxy_sleep_interval = 2
        self.proxy_healthcheck_buffer = 10
        self.proxy_server_base_url = "http://localhost:{}/api"

    def print_usage(self, *args):
        ui_thread.print(burp_usage())

    def add_cmd(self, parent: argparse._SubParsersAction) -> argparse.ArgumentParser:
        burp_cmd = parent.add_parser(self.name)
        burp_cmd.add_argument("--port", "-p", help="", type=int, default=util.find_open_port())
        burp_cmd.add_argument("--xml", help="", default="", required=True)
        burp_cmd.add_argument("--ca-path", type=str, default="")
        burp_cmd.add_argument("--report", type=str, default="")
        burp_cmd.add_argument("--save-collection", action="store_true", help="Get postman collection")
        burp_cmd.add_argument("--captured-domains", nargs="+", help="", default="")
        burp_cmd.add_argument("--severity-level", choices=["all", "medium", "high", "critical", "none"], default="none")
        burp_cmd.print_usage = self.print_usage
        burp_cmd.print_help = self.print_usage
        return burp_cmd

    def _updated_environment(self, proxy_port: int):
        env_copy = deepcopy(os.environ)
        return env_copy.update(
            {
                "HTTP_PROXY": "http://localhost:{}".format(proxy_port),
                "HTTPS_PROXY": "http://localhost:{}".format(proxy_port),
            }
        )

    def _start_proxy(self, args):
        res = pynt_requests.put(
            self.proxy_server_base_url.format(args.port) + "/proxy/start"
        )
        res.raise_for_status()
        self.scan_id = res.json()["scanId"]

    def _stop_proxy(self, args):
        start = time.time()
        while start + self.proxy_healthcheck_buffer > time.time():
            res = pynt_requests.put(
                self.proxy_server_base_url.format(args.port) + "/proxy/stop",
                json={"scanId": self.scan_id},
            )
            if res.status_code == HTTPStatus.OK:
                return
            time.sleep(self.proxy_sleep_interval)
        raise TimeoutError()

    def _get_report(self, args, report_format):
        while True:
            res = pynt_requests.get(
                self.proxy_server_base_url.format(args.port)
                + "/report?format={}".format(report_format),
                params={"scanId": self.scan_id},
            )
            if res.status_code == HTTPStatus.OK:
                return res.text
            if res.status_code == HTTPStatus.ACCEPTED:
                time.sleep(self.proxy_sleep_interval)
                continue
            if res.status_code == 517:  # pynt did not recieve any requests
                ui_thread.print(
                    ui_thread.PrinterText(
                        res.json()["message"], ui_thread.PrinterText.WARNING
                    )
                )
                return
            ui_thread.print("Error in polling for scan report: {}".format(res.text))
            return

    def _get_postman_collection(self, args):
        while True:
            res = pynt_requests.get(
                self.proxy_server_base_url.format(args.port)
                + "/collection",
                params={"scanId": self.scan_id},
            )
            if res.status_code == HTTPStatus.OK:
                return res.text
            if res.status_code == HTTPStatus.ACCEPTED:
                time.sleep(self.proxy_sleep_interval)
                continue
            if res.status_code == 517:  # pynt did not recieve any requests
                ui_thread.print(
                    ui_thread.PrinterText(
                        res.json()["message"], ui_thread.PrinterText.WARNING
                    )
                )
                return
            if res.status_code == 404:
                ui_thread.print(
                    ui_thread.PrinterText(
                        "No collection found", ui_thread.PrinterText.WARNING
                    )
                )
                return
            ui_thread.print("Error in polling for scan report: {}".format(res.text))
            return

    def run_cmd(self, args: argparse.Namespace):
        proxy_port = util.find_open_port()

        container_config = pynt_container.DockerContainerConfig(
            args,
            "proxy",
            pynt_container.api_port(args.port),
            pynt_container.proxy_port(proxy_port),
        )

        for host in args.captured_domains:
            container_config.docker_arguments += ["--host-targets", host]

        if "ca_path" in args and args.ca_path:
            if not os.path.isfile(args.ca_path):
                ui_thread.print(
                    ui_thread.PrinterText(
                        "Could not find the provided ca path, please provide with a valid path",
                        ui_thread.PrinterText.WARNING,
                    )
                )
                return

            ca_name = os.path.basename(args.ca_path)
            container_config.docker_arguments += ["--ca-path", ca_name]
            container_config.mounts.append(
                pynt_container.create_mount(
                    os.path.abspath(args.ca_path), "/etc/pynt/{}".format(ca_name)
                )
            )

        container_config.docker_arguments += ["--test-name", os.path.basename(args.xml)]

        if not os.path.isfile(args.xml):
            ui_thread.print(
                ui_thread.PrinterText(
                    "Could not find the provided xml path, please provide with a valid xml path",
                    ui_thread.PrinterText.WARNING,
                )
            )
            return

        ui_thread.print_verbose("Parsing burp xml")
        doc = parse_xml(args.xml)
        if not doc:
            ui_thread.print(
                ui_thread.PrinterText(
                    "Invalid file format. please provide a valid xml",
                    ui_thread.PrinterText.WARNING,
                )
            )
            return

        if not is_valid_xml(doc):
            ui_thread.print(
                ui_thread.PrinterText(
                    "Invalid xml file. please provide a valid xml output generated from burp",
                    ui_thread.PrinterText.WARNING,
                )
            )
            return

        proxy_docker = pynt_container.PyntContainerNative(container_config)

        proxy_docker.prepare_client()
        proxy_docker.pre_run_validation(args.port)
        proxy_docker.run()

        ui_thread.print_generator(proxy_docker.stdout)

        util.wait_for_healthcheck("http://localhost:{}".format(args.port))
        ui_thread.print_verbose(util.GOT_INITIAL_HEALTHCHECK_MESSAGE)
        ui_thread.print(ui_thread.PrinterText(
            "Pynt docker is ready",
            ui_thread.PrinterText.INFO,
        ))

        self._start_proxy(args)

        run_burp_xml(doc, proxy_port)

        self._stop_proxy(args)

        ui_thread.print(
            ui_thread.PrinterText(
                "Please wait while we scan and generate the report, it may take a few minutes...",
                ui_thread.PrinterText.INFO,
            )
        )

        with ui_thread.progress(
                "ws://localhost:{}/progress?scanId={}".format(args.port, self.scan_id),
                partial(lambda *args: None),
                "scan in progress...",
                100,
        ):
            html_report = self._get_report(args, "html")
            html_report_path = os.path.join(
                tempfile.gettempdir(), "pynt_report_{}.html".format(int(time.time()))
            )

            json_report = self._get_report(args, "json")
            json_report_path = os.path.join(
                tempfile.gettempdir(), "pynt_report_{}.json".format(int(time.time()))
            )

            collection = self._get_postman_collection(args) if args.save_collection else None
            collection_path = os.path.join(
                store.get_default_store_dir(), "postman_collection_{}.json".format(int(time.time()))
            )

            if "report" in args and args.report:
                full_path = os.path.abspath(args.report)
                html_report_path = util.get_user_report_path(full_path, "html")
                json_report_path = util.get_user_report_path(full_path, "json")

            if html_report:
                with open(html_report_path, "w", encoding="utf-8") as html_file:
                    html_file.write(html_report)
                webbrowser.open("file://{}".format(html_report_path))

            if json_report:
                with open(json_report_path, "w", encoding="utf-8") as json_file:
                    json_file.write(json_report)
                reporter = cli_reporter.PyntReporter(json_report_path)
                reporter.print_summary()

            if collection:
                with open(collection_path, "w", encoding="utf-8") as collection_file:
                    collection_file.write(collection)
                ui_thread.print(
                    ui_thread.PrinterText(
                        "Postman collection saved at: {}".format(collection_path),
                        ui_thread.PrinterText.INFO,
                    )
                )

            if json_report:
                json_obj = json.loads(json_report)
                if json_obj:
                    util.check_for_findings_or_warnings(args, json_obj)
                    util.check_severity(args.severity_level, json_obj)
