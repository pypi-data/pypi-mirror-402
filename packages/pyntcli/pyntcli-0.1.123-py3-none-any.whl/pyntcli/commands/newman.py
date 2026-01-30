import argparse
import time
import os
import webbrowser
from functools import partial

from pyntcli.pynt_docker import pynt_container
from pyntcli.commands import sub_command, util
from pyntcli.ui import ui_thread


def newman_usage():
    return (
        ui_thread.PrinterText(
            "Integration with newman, run scan using postman collection from the CLI"
        )
        .with_line("")
        .with_line("Usage:", style=ui_thread.PrinterText.HEADER)
        .with_line("\tpynt newman [OPTIONS]")
        .with_line("")
        .with_line("Options:", style=ui_thread.PrinterText.HEADER)
        .with_line("\t--collection - Postman collection file name")
        .with_line("\t--environment - Postman environment file name")
        .with_line("\t--reporters Output results to json")
        .with_line(
            "\t--host-ca - Path to the CA file in PEM format to enable SSL certificate verification for pynt when running through a VPN."
        )
        .with_line(
            "\t--application-id - Attach the scan to an application, you can find the ID in your applications area at app.pynt.io"
        )
        .with_line(
            "\t--application-name - Attach the scan to an application, application will be created automatically if it does not exist."
        )
        .with_line("\t--severity-level - 'all', 'medium', 'high', 'critical', 'none' (default) ")
        .with_line("\t--tag - Tag the scan. Repeat for multiple tags")
        .with_line("\t--verbose - Use to get more detailed information about the run")
    )


class NewmanSubCommand(sub_command.PyntSubCommand):
    def __init__(self, name) -> None:
        super().__init__(name)

    def usage(self, *args):
        ui_thread.print(newman_usage())

    def add_cmd(self, parent: argparse._SubParsersAction) -> argparse.ArgumentParser:
        newman_cmd = parent.add_parser(self.name)
        newman_cmd.add_argument("--collection", type=str, required=True)
        newman_cmd.add_argument("--environment", nargs="+", required=False)
        newman_cmd.add_argument(
            "--reporters", action="store_true", default=False, required=False
        )
        newman_cmd.add_argument("--severity-level", choices=["all", "medium", "high", "critical", "none"], default="none")
        newman_cmd.print_usage = self.usage
        newman_cmd.print_help = self.usage
        return newman_cmd

    def run_cmd(self, args: argparse.Namespace):
        port = util.find_open_port()
        container_config = pynt_container.DockerContainerConfig(
            args,
            "newman",
            pynt_container.api_port(port),
        )

        if not os.path.isfile(args.collection):
            ui_thread.print(
                ui_thread.PrinterText(
                    "Could not find the provided collection path, please provide with a valid collection path",
                    ui_thread.PrinterText.WARNING,
                )
            )
            return

        collection_name = os.path.basename(args.collection)
        container_config.docker_arguments += ["-c", collection_name]
        container_config.mounts.append(
            pynt_container.create_mount(
                os.path.abspath(args.collection), "/etc/pynt/{}".format(collection_name)
            )
        )

        if "environment" in args and args.environment:
            env_names = []
            for environ in args.environment:
                if not os.path.isfile(environ):
                    ui_thread.print(
                        ui_thread.PrinterText(
                            f"Could not find the provided environment path: {environ}, please provide with a valid environment path",
                            ui_thread.PrinterText.WARNING,
                        )
                    )
                    return
                env_name = os.path.basename(environ)
                env_names.append(env_name)
                container_config.mounts.append(
                    pynt_container.create_mount(
                        os.path.abspath(environ), "/etc/pynt/{}".format(env_name)
                    )
                )
            container_config.docker_arguments += ["-e", ",".join(env_names)]

        with util.create_default_file_mounts(args) as m:
            container_config.mounts += m
            newman_docker = pynt_container.PyntContainerNative(container_config)

            newman_docker.prepare_client()
            newman_docker.pre_run_validation(port)
            newman_docker.run()

            healthcheck = partial(
                util.wait_for_healthcheck, "http://localhost:{}".format(port)
            )

            healthcheck()
            ui_thread.print_verbose(util.GOT_INITIAL_HEALTHCHECK_MESSAGE)
            ui_thread.print(ui_thread.PrinterText(
                "Pynt docker is ready",
                ui_thread.PrinterText.INFO,
            ))

            ui_thread.print_generator(newman_docker.stdout)

            with ui_thread.progress(
                    "ws://localhost:{}/progress".format(port),
                    healthcheck,
                    "scan in progress...",
                    100,
            ):
                scan_details_url = None
                while newman_docker.is_alive():
                    if not scan_details_url:
                        scan_details_url = self.get_scan_details_url(port)
                    time.sleep(1)

            if scan_details_url:
                webbrowser.open(scan_details_url)
            else:
                app_provided = args.application_name or args.application_id

                if app_provided:
                    ui_thread.print_verbose(ui_thread.PrinterText(
                        "Could not get report url, trying to open report file",
                        ui_thread.PrinterText.INFO,
                ))
                util.open_report_from_file()