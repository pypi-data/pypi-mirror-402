import argparse
import time
import os
from functools import partial
import webbrowser
from pyntcli.pynt_docker import pynt_container
from pyntcli.ui import ui_thread
from pyntcli.commands import sub_command, util


def har_usage():
    return (
        ui_thread.PrinterText("Integration with static har file testing")
        .with_line("")
        .with_line("Usage:", style=ui_thread.PrinterText.HEADER)
        .with_line("\tpynt har [OPTIONS]")
        .with_line("")
        .with_line("Options:", style=ui_thread.PrinterText.HEADER)
        .with_line("\t--har - Path to har file")
        .with_line(
            '\t--captured-domains - Pynt will scan only these domains and subdomains. For all domains write "*"'
        )
        .with_line("\t--reporters - Output results to json")
        .with_line(
            "\t--application-id - Attach the scan to an application, you can find the ID in your applications area at app.pynt.io"
        )
        .with_line("\t--application-name - Attach the scan to an application, application will be created automatically if it does not exist.")
        .with_line(
            "\t--host-ca - Path to the CA file in PEM format to enable SSL certificate verification for pynt when running through a VPN."
        )
        .with_line("\t--severity-level - 'all', 'medium', 'high', 'critical', 'none' (default) ")
        .with_line("\t--tag - Tag the scan. Repeat for multiple tags")
        .with_line("\t--verbose - Use to get more detailed information about the run")
        .with_line("")
    )


class HarSubCommand(sub_command.PyntSubCommand):
    def __init__(self, name) -> None:
        super().__init__(name)

    def usage(self, *args):
        ui_thread.print(har_usage())

    def add_cmd(self, parent: argparse._SubParsersAction) -> argparse.ArgumentParser:
        har_cmd = parent.add_parser(self.name)
        har_cmd.add_argument("--har", type=str, required=True)
        har_cmd.add_argument(
            "--captured-domains", nargs="+", help="", default="", required=True
        )
        har_cmd.add_argument("--reporters", action="store_true")
        har_cmd.add_argument("--severity-level", choices=["all", "medium", "high", "critical", "none"], default="none")
        har_cmd.print_usage = self.usage
        har_cmd.print_help = self.usage
        return har_cmd

    def run_cmd(self, args: argparse.Namespace):
        ui_thread.print_verbose("Building container")
        port = util.find_open_port()
        container_config = pynt_container.DockerContainerConfig(
            args,
            "har",
            pynt_container.api_port(port),
        )

        if not os.path.isfile(args.har) :
            ui_thread.print(
                ui_thread.PrinterText(
                    "Could not find the provided har path, please provide with a valid har path",
                    ui_thread.PrinterText.WARNING,
                )
            )
            return

        if os.path.getsize(args.har) == 0:
            ui_thread.print(
                ui_thread.PrinterText(
                    "The provided har file is empty, please provide a valid har file",
                    ui_thread.PrinterText.WARNING,
                )
            )
            return

        har_name = os.path.basename(args.har)
        container_config.docker_arguments += ["--har", har_name]
        container_config.mounts.append(
            pynt_container.create_mount(
                os.path.abspath(args.har), "/etc/pynt/{}".format(har_name)
            )
        )

        for host in args.captured_domains:
            container_config.docker_arguments += ["--host-targets", host]

        with util.create_default_file_mounts(args) as m:

            container_config.mounts += m

            har_docker = pynt_container.PyntContainerNative(container_config)

            har_docker.prepare_client()
            har_docker.pre_run_validation(port)
            har_docker.run()

            healthcheck = partial(
                util.wait_for_healthcheck, "http://localhost:{}".format(port)
            )

            healthcheck()
            ui_thread.print_verbose(util.GOT_INITIAL_HEALTHCHECK_MESSAGE)
            ui_thread.print(ui_thread.PrinterText(
                "Pynt docker is ready",
                ui_thread.PrinterText.INFO,
            ))

            ui_thread.print_generator(har_docker.stdout)

            scan_details_url = ""
            with ui_thread.progress(
                    "ws://localhost:{}/progress".format(port),
                    healthcheck,
                    "scan in progress...",
                    100,
            ):
                scan_details_url = self.get_scan_details_url(port)
                while har_docker.is_alive():
                    time.sleep(1)

            if scan_details_url:
                webbrowser.open(scan_details_url)
            else:
                app_provided = args.application_name or args.application_id

                if app_provided:
                    ui_thread.print_verbose(ui_thread.PrinterText(
                        "Could not get report url, trying to open report file",
                        ui_thread.PrinterText.INFO
                    ))
                util.open_report_from_file()
