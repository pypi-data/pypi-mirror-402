import argparse
import websocket
import webbrowser
import os
import tempfile
import time

import pyntcli.log.log as log

from http import HTTPStatus
from . import sub_command, util
from pyntcli.pynt_docker import pynt_container
from pyntcli.ui import ui_thread
from pyntcli.transport import pynt_requests
from .util import build_scan_details_url


class PyntPostmanException(Exception):
    pass


class PyntWebSocketException(PyntPostmanException):
    pass


logger = log.get_logger()


def postman_usage():
    return ui_thread.PrinterText("Integration with postman, run scan from pynt postman collection") \
        .with_line("") \
        .with_line("Usage:", style=ui_thread.PrinterText.HEADER) \
        .with_line("\tpynt postman [OPTIONS]") \
        .with_line("") \
        .with_line("Options:", style=ui_thread.PrinterText.HEADER) \
        .with_line("\t--port - set the port pynt will listen to (DEFAULT: 5001)") \
        .with_line("\t--insecure - use when target uses self signed certificates") \
        .with_line("\t--host-ca - path to the CA file in PEM format to enable SSL certificate verification for pynt when running through a VPN.") \
        .with_line("\t--tag - Tag the scan. Repeat for multiple tags") \
        .with_line("\t--verbose - Use to get more detailed information about the run")


class PostmanSubCommand(sub_command.PyntSubCommand):
    def __init__(self, name) -> None:
        super().__init__(name)
        self.server_base_url = "http://localhost:{}/api"

    def usage(self, *args):
        ui_thread.print(postman_usage())

    def add_cmd(self, parent_command: argparse._SubParsersAction) -> argparse.ArgumentParser:
        postman_cmd = parent_command.add_parser(self.name)
        postman_cmd.add_argument("--port", "-p", help="set the port pynt will listen to (DEFAULT: 5001)", type=int, default=5001)
        postman_cmd.print_usage = self.usage
        postman_cmd.print_help = self.usage
        return postman_cmd

    def scan_id_generator(self, port):
        try:
            ws = websocket.WebSocket()
            ws.connect("ws://localhost:{}/api/scan_id".format(port))

            while ws.connected:
                scan_id = ws.recv()
                yield scan_id

        except websocket.WebSocketConnectionClosedException:
            logger.error("web socket closed unexpectedly")
            return None
        except Exception as e:
            logger.error("web socket failed to connect: {}".format(e))
            raise PyntWebSocketException()
        finally:
            ws.close()

    def get_report(self, port, report_format, scan_id):
        while True:
            res = pynt_requests.get(self.server_base_url.format(port) + "/report?format={}".format(report_format), params={"scanId": scan_id})
            if res.status_code == HTTPStatus.OK:
                return res.text
            if res.status_code == HTTPStatus.ACCEPTED:
                time.sleep(2)
                continue
            if res.status_code == HTTPStatus.BAD_REQUEST:
                return
            if res.status_code == 517:  # pynt did not recieve any requests
                ui_thread.print(ui_thread.PrinterText(res.json()["message"], ui_thread.PrinterText.WARNING))
                return
            ui_thread.print("Error in polling for scan report: {}".format(res.text))
            return

    def run_cmd(self, args: argparse.Namespace):
        if "application_id" in args and args.application_id:
            ui_thread.print("application-id is not supported in postman integration, use the collection variables to set application id.")
            args.application_id = ""

        container_config = pynt_container.DockerContainerConfig(
            args,
            "postman",
            pynt_container.api_port(args.port),
        )

        postman_docker = pynt_container.PyntContainerNative(container_config)
        postman_docker.prepare_client()
        postman_docker.pre_run_validation(args.port)
        postman_docker.run()

        ui_thread.print_generator(postman_docker.stdout)

        util.wait_for_healthcheck("http://localhost:{}".format(args.port))
        ui_thread.print_verbose(util.GOT_INITIAL_HEALTHCHECK_MESSAGE)
        ui_thread.print(ui_thread.PrinterText(
            "Pynt docker is ready",
            ui_thread.PrinterText.INFO,
        ))

        for scan_id in self.scan_id_generator(args.port):
            html_report = self.get_report(args.port, "html", scan_id)
            html_report_path = os.path.join(tempfile.gettempdir(), "pynt_report_{}.html".format(int(time.time())))

            app_id = self.get_app_id(args.port, scan_id)
            scan_details_url = build_scan_details_url(scan_id, app_id)

            if scan_details_url:
                webbrowser.open(scan_details_url)
            elif html_report:
                with open(html_report_path, "w", encoding="utf-8") as html_file:
                    html_file.write(html_report)
                webbrowser.open("file://{}".format(html_report_path))

        if not postman_docker.is_alive():
            ui_thread.print(ui_thread.PrinterText("Pynt container is not available", ui_thread.PrinterText.WARNING))
