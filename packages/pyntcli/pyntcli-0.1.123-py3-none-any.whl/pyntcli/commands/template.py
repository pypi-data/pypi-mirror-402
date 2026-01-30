import argparse
import os
import json
import tempfile
import time
from functools import partial

from pyntcli.pynt_docker import pynt_container
from pyntcli.ui import ui_thread
from pyntcli.commands import sub_command, util

PYNT_CONTAINER_INTERNAL_PORT = "5001"


def template_usage():
    return (
        ui_thread.PrinterText("Integration with template testing")
        .with_line("")
        .with_line("Usage:", style=ui_thread.PrinterText.HEADER)
        .with_line("\tpynt template [OPTIONS]")
        .with_line("")
        .with_line("Options:", style=ui_thread.PrinterText.HEADER)
        .with_line("\t--template-file / -tf - Path to the template file")
        .with_line("\t--template-paths-file / -tpf - Path to the file containing the template paths (with new line separator) for the attacks")
        .with_line("\t--url - Base URL for the attacks")
        .with_line("\t--urls - Path to the file containing the base URLs (with new line separator) for the attacks")
        .with_line("\t--reporters - Output results to json")
        .with_line("\t--severity-level - 'all', 'medium', 'high', 'critical', 'none' (default)")
        .with_line("\t--tag - Tag the scan. Repeat for multiple tags")
        .with_line("\t--verbose - Use to get more detailed information about the run")
        .with_line("")
    )


class TemplateSubCommand(sub_command.PyntSubCommand):
    def __init__(self, name) -> None:
        super().__init__(name)

    def usage(self, *args):
        ui_thread.print(template_usage())

    def add_cmd(self, parent: argparse._SubParsersAction) -> argparse.ArgumentParser:
        template_cmd = parent.add_parser(self.name)
        template_cmd.add_argument("--template-file", "-tf", type=str, help="Path to the template file")
        template_cmd.add_argument("--template-paths-file", "-tpf", type=str, help="Path to the file containing the template paths (with new line separator) for the attacks")
        template_cmd.add_argument("--url", "-u", type=str, help="Base URL for the attacks")
        template_cmd.add_argument("--urls", type=str, help="Path to the file containing the base URLs (with new line separator) for the attacks")
        template_cmd.add_argument("--reporters", action="store_true")
        template_cmd.add_argument("--severity-level", choices=["all", "medium", "high", "critical", "none"], default="none")
        template_cmd.print_usage = self.usage
        template_cmd.print_help = self.usage
        return template_cmd

    def run_cmd(self, args: argparse.Namespace):
        pynt_folder_path = "/etc/pynt"
        templates_folder_path = f"{pynt_folder_path}/templates"
        ui_thread.print_verbose("Building container")
        port = util.find_open_port()
        container_config = pynt_container.DockerContainerConfig(
            args,
            "template",
            pynt_container._PyntDockerPort(port=port, name="--port")
        )

        try:
            validate_args(args)
        except ValueError as e:
            ui_thread.print(
                ui_thread.PrinterText(
                    str(e),
                    ui_thread.PrinterText.WARNING,
                )
            )
            return

        if args.template_file:
            if not os.path.isfile(args.template_file):
                ui_thread.print(
                    ui_thread.PrinterText(
                        "Could not find the provided path, please provide a valid path",
                        ui_thread.PrinterText.WARNING,
                    )
                )
                return
            template_name = os.path.basename(args.template_file)
            full_template_path = f"{templates_folder_path}/{template_name}"
            container_config.mounts.append(
                pynt_container.create_mount(
                    os.path.abspath(args.template_file), full_template_path
                )
            )
            container_config.docker_arguments += ["--template-file", full_template_path]

        if args.template_paths_file:
            if not os.path.isfile(args.template_paths_file):
                ui_thread.print(
                    ui_thread.PrinterText(
                        "Could not find the provided paths file, please provide a valid paths file",
                        ui_thread.PrinterText.WARNING,
                    )
                )
                return

            # read the file, mount each uncommented file to /etc/pynt/templates, create a temp file with the paths as they are in the container (in /etc/pynt) and mount it to /etc/pynt/paths.txt
            with open(args.template_paths_file, "r") as f:
                paths = [line.strip() for line in f if not (line.strip().startswith("#") or line.startswith("//"))]
                for path in paths:
                    container_config.mounts.append(
                        pynt_container.create_mount(
                            os.path.abspath(path), f"{templates_folder_path}/{os.path.basename(path)}"
                        )
                    )

            container_config.docker_arguments += ["--templates-folder", templates_folder_path]

        if args.url:
            container_config.docker_arguments += ["--url", args.url]

        if args.urls and not os.path.isfile(args.urls):
            ui_thread.print(
                ui_thread.PrinterText(
                    "Could not find the provided urls file, please provide a valid urls file",
                    ui_thread.PrinterText.WARNING,
                )
            )
            return

        if args.urls:
            base_urls_path = f"{pynt_folder_path}/base_urls.txt"
            container_config.docker_arguments += ["--urls", base_urls_path]
            container_config.mounts.append(
                pynt_container.create_mount(
                    os.path.abspath(args.urls), base_urls_path
                )
            )

        with util.create_default_file_mounts(args) as m:
            container_config.mounts += m

            template_docker = pynt_container.PyntContainerNative(container_config)

            template_docker.prepare_client()
            template_docker.pre_run_validation(port)
            template_docker.run()

            healthcheck = partial(
                util.wait_for_healthcheck, "http://localhost:{}".format(port)
            )

            healthcheck()
            ui_thread.print_verbose(util.GOT_INITIAL_HEALTHCHECK_MESSAGE)
            ui_thread.print(ui_thread.PrinterText(
                "Pynt docker is ready",
                ui_thread.PrinterText.INFO,
            ))

            ui_thread.print_generator(template_docker.stdout)

            with ui_thread.progress(
                    "ws://localhost:{}/progress".format(port),
                    healthcheck,
                    "scan in progress...",
                    100,
            ):
                while template_docker.is_alive():
                    time.sleep(1)


def validate_args(args: argparse.Namespace):
    if not args.template_file and not args.template_paths_file:
        raise ValueError("Please provide either a template file or a template paths file")
    if args.template_file and args.template_paths_file:
        raise ValueError("Please provide either a template file or a template paths file, not both")
    if not args.url and not args.urls:
        raise ValueError("Please provide either a url or a urls file")
    if args.url and args.urls:
        raise ValueError("Please provide either a url or a urls file, not both")
    if args.urls and not os.path.isfile(args.urls):
        raise ValueError("Could not find the provided urls file, please provide a valid urls file")
    if args.template_file and not os.path.isfile(args.template_file):
        raise ValueError("Could not find the provided path, please provide a valid path")
    if args.template_paths_file and not os.path.isfile(args.template_paths_file):
        raise ValueError("Could not find the provided paths file, please provide a valid paths file")
