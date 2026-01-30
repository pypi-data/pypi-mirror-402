import argparse
from os import environ

from pyntcli.auth import login
from pyntcli.ui import ui_thread
from pyntcli.analytics import send as analytics


def root_usage():
    return (
        ui_thread.PrinterText("Usage:", style=ui_thread.PrinterText.HEADER)
        .with_line("\tpynt [COMMAND] [OPTIONS]")
        .with_line("")
        .with_line("Commands:", style=ui_thread.PrinterText.HEADER)
        .with_line("\tpostman   -   integration with postman, run scan from pynt postman collection")
        .with_line("\tnewman    -   run postman collection from the CLI")
        .with_line("\thar       -   run scan on static har file")
        .with_line("\tcommand   -   run scan with a given command")
        .with_line("\tlisten    -   run scan with a routed traffic")
        .with_line("\tburp      -   run scan on a burp xml output file")
        .with_line("\tpynt-id   -   view your pynt-id to use when running pynt in CI pipeline")
        .with_line("\tlogout    -   log out from your user")
        .with_line("")
        .with_line("Run pynt [COMMAND] -h to get help on a specific command", style=ui_thread.PrinterText.INFO, )
    )


def usage(*args):
    ui_thread.print(root_usage())


def check_cicd_context():
    if environ.get("GITHUB_ACTION") is not None:
        analytics.emit(analytics.CICD, {"env": "GitHub"})
        return
    if environ.get("GITLAB_USER_ID") is not None:
        analytics.emit(analytics.CICD, {"env": "GitLab"})
        return
    if environ.get("JENKINS_HOME") is not None:
        analytics.emit(analytics.CICD, {"env": "Jenkins"})


class BaseCommand:
    def __init__(self) -> None:
        self.base: argparse.ArgumentParser = None
        self.subparser: argparse._SubParsersAction = None

    def cmd(self):
        if self.base:
            return self.base

        self.base = argparse.ArgumentParser(prog="pynt")
        self.base.print_usage = usage
        self.base.print_help = usage
        return self.base

    def add_base_arguments(self, parser):
        parser.add_argument(
            "--insecure",
            default=False,
            required=False,
            action="store_true",
            help="use when target uses self signed certificates",
        )
        parser.add_argument("--dev-flags", type=str,
                            default="", help=argparse.SUPPRESS)
        parser.add_argument("--host-ca", type=str, default="")
        parser.add_argument("--application-id", type=str,
                            default="", required=False)
        parser.add_argument("--application-name", type=str,
                            default="", required=False)
        parser.add_argument("--proxy", type=str, default="", required=False)
        parser.add_argument(
            "--yes",
            "-y",
            default=False,
            required=False,
            action="store_true",
            help="Automatically answer yes to all prompts and run non-interactively ",
        )
        parser.add_argument(
            "--verbose",
            default=False,
            required=False,
            action="store_true",
            help="Use to get more detailed execution information",
        )
        parser.add_argument(
            "--use-docker-native",
            action="store_true",
            help=argparse.SUPPRESS,
        )
        parser.add_argument(
            "--pynt-image",
            default="",
            required=False,
            type=str,
            help=argparse.SUPPRESS,
        )
        parser.add_argument(
            "--tag",
            default=[],
            required=False,
            nargs="+",
            action="append",
            help=argparse.SUPPRESS,
        )

    def get_subparser(self) -> argparse._SubParsersAction:
        if self.subparser is None:
            self.subparser = self.base.add_subparsers(help="", dest="command")

        return self.subparser

    def run_cmd(self, args: argparse.Namespace):
        analytics.emit(analytics.LOGIN_START)

        if login.should_login():
            ui_thread.print_verbose("User should login")
            l = login.Login().login()
        else:
            login.refresh_token()

        analytics.emit(analytics.LOGIN_DONE)
        user_id = login.user_id()
        if user_id:
            analytics.set_user_id(user_id)

        check_cicd_context()
