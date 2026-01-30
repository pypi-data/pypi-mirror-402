import argparse

from pyntcli.store.store import CredStore
from pyntcli.commands import sub_command
from pyntcli.ui import ui_thread


def pyntid_usage():
    return ui_thread.PrinterText("View your pynt-id to use when running pynt in CI pipeline") \
        .with_line("") \
        .with_line("Usage:", style=ui_thread.PrinterText.HEADER) \
        .with_line("\tpynt pynt-id")


class PyntShowIdCommand(sub_command.PyntSubCommand):
    def __init__(self, name) -> None:
        super().__init__(name)

    def usage(self, *args):
        ui_thread.print(pyntid_usage())

    def add_cmd(self, parent: argparse._SubParsersAction) -> argparse.ArgumentParser:
        cmd = parent.add_parser(self.name)
        cmd.print_usage = self.usage
        cmd.print_help = self.usage
        return cmd

    def run_cmd(self, args: argparse.Namespace):
        creds_path = CredStore().get_path()
        ui_thread.print(open(creds_path, "r").read())
