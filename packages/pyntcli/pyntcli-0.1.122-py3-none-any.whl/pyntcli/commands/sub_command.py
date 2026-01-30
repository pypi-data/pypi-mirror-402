import argparse
import os
import tempfile
import json
import time

from pyntcli.commands import util
from pyntcli.commands.util import build_scan_details_url
from pyntcli.transport import pynt_requests
from pyntcli.ui import report as cli_reporter

from http import HTTPStatus
from pyntcli.ui import ui_thread

class PyntSubCommand:
    def __init__(self, name) -> None:
        self.name = name
        self.scan_id = ""
        self.scan_id_url = "http://localhost:{}/scan/scan_id"
        self.app_id_url = "http://localhost:{}/scan/app_id?scanId={}"
        self.proxy_sleep_interval = 2
        self.proxy_healthcheck_buffer = 10
        self.proxy_server_base_url = "http://localhost:{}/api"
        pass 

    def get_scan_id(self, port):
        try:
            res_scan_id = pynt_requests.get(
                self.scan_id_url.format(port)
            )
            if res_scan_id.status_code == HTTPStatus.OK:
                return res_scan_id.json()["scan_id"]
            else:
                return None
        except Exception as e:
            ui_thread.print_verbose("Error in getting scan id: " + str(e))
            return None

    def get_app_id(self, port, scan_id):
        try:
            res_app_id = pynt_requests.get(
                self.app_id_url.format(port, scan_id)
            )
            if res_app_id.status_code == HTTPStatus.OK:
                return res_app_id.json()["app_id"]
            else:
                return None
        except Exception as e:
            ui_thread.print_verbose("Error in getting app id: " + str(e))
            return None

    def get_scan_details_url(self, port):
        try:
            scan_id = self.get_scan_id(port)
            if not scan_id:
                return None

            app_id = self.get_app_id(port, scan_id)
            if not app_id:
                return None

            scan_details_url = build_scan_details_url(scan_id, app_id)
            return scan_details_url
        except Exception as e:
            ui_thread.print_verbose("Error in getting report url: " + str(e))
            return None


    def handle_html_report(self, args):
        html_report = self._get_report(args, "html")
        if not html_report:
            return None
        else:
            html_report_path = os.path.join(
                tempfile.gettempdir(), "pynt_report_{}.html".format(int(time.time()))
            )

            if "report" in args and args.report:
                full_path = os.path.abspath(args.report)
                html_report_path = util.get_user_report_path(full_path, "html")

            with open(html_report_path, "w", encoding="utf-8") as html_file:
                html_file.write(html_report)
            return html_report_path


    def handle_json_report(self, args):
        json_report = self._get_report(args, "json")
        if json_report:
            json_report_path = os.path.join(
                tempfile.gettempdir(), "pynt_report_{}.json".format(int(time.time()))
            )

            if "report" in args and args.report:
                full_path = os.path.abspath(args.report)
                json_report_path = util.get_user_report_path(full_path, "json")

            with open(json_report_path, "w", encoding="utf-8") as json_file:
                json_file.write(json_report)
            reporter = cli_reporter.PyntReporter(json_report_path)
            reporter.print_summary()

            json_obj = json.loads(json_report)
            if json_obj:
                util.check_for_findings_or_warnings(args, json_obj)
                util.check_severity(args.severity_level, json_obj)

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
                return None
            ui_thread.print("Error in polling for scan report: {}".format(res.text))
            return None


    def get_name(self):
        return self.name
    
    def add_cmd(self, parent: argparse._SubParsersAction) -> argparse.ArgumentParser: 
        raise NotImplemented()
    
    def run_cmd(self, args: argparse.Namespace):
        raise NotImplemented()
