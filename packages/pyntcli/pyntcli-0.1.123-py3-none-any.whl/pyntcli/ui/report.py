import json
from rich.table import Table, Column
from pyntcli.ui import ui_thread



class PyntTable():
    def __init__(self, title) -> None:
        self.table = Table(title=title,title_style="bold")

    def set_columns(self, columns):
        for col in columns:
            self.table.add_column(col.header, style=col.style)

    def add_row(self, *values):
        self.table.add_row(*values)

    def print(self):
        ui_thread.print(ui_thread.PrinterText("").with_line(""))
        ui_thread.print(self.table)


class PyntReporter():
    def __init__(self,report_path) -> None:
        try:
            self.report = json.load(open(report_path))
        except json.JSONDecodeError:
            self.report = None
        
    def print_summary(self):
        if not self.report:
            return
        
        functional_tests = self.report["functionalTests"]
        functional_table = PyntTable("Functional Tests")
        
        functional_table.set_columns([
            Column(header="Endpoints"),
            Column(header="Requests")])
        
        functional_table.add_row(str(functional_tests["Endpoints"]),
                                 str(functional_tests["Requests"]))

        security_tests = self.report["securityTests"]
        security_table = PyntTable("Security Tests")
        
        security_table.set_columns([
            Column(header="Errors",style="red"),
            Column(header="Warnings",style="yellow"),
            Column(header="Passed",style="green",),
            Column(header="Did Not Run")])
        
        security_table.add_row(str(security_tests["Findings"]),
                                 str(security_tests["Warnings"]),
                                 str(security_tests["Passed"]),
                                 str(security_tests["DidNotRun"]))
        
        functional_table.print()
        security_table.print()
        
        
        