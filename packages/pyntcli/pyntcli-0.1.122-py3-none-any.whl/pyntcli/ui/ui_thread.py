from threading import Thread
import queue
import os
import time
from rich.text import Text
from rich.console import Console
from rich.status import Status
from rich.progress import Progress
from rich.markup import escape
from typing import Tuple

from pyntcli import __version__ as cli_version
from pyntcli.ui.progress import PyntProgress

VERBOSE = False


class PrinterText():
    DEFAULT = 0
    HEADER = 1
    INFO = 2
    WARNING = 3

    def __init__(self, text, style=DEFAULT):
        self.text = Text(text, PrinterText.get_style(style))

    @staticmethod
    def get_style(style):
        if style == PrinterText.INFO:
            return "bold blue"
        if style == PrinterText.WARNING:
            return "bold red"
        if style == PrinterText.HEADER:
            return "bold"
        if style == PrinterText.DEFAULT:
            return None

    def with_line(self, line, style=DEFAULT):
        self.text.append(os.linesep)
        self.text.append(Text(line, PrinterText.get_style(style)))
        return self


class AnsiText():
    def __init__(self, data) -> None:
        self.data = data

    @staticmethod
    def wrap_gen(gen):
        for v in gen:
            yield AnsiText(v)


class Spinner():
    def __init__(self, prompt, style) -> None:
        self.prompt = prompt
        self.style = style
        self.runnning = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.running = False


def pynt_version() -> Tuple[str, int]:
    return "Pynt CLI version " + cli_version, PrinterText.DEFAULT


def pynt_header() -> Tuple[str, int]:
    return "API Security testing autopilot", PrinterText.DEFAULT


def gen_func_loop(gen):
    for l in gen:
        data = l
        if type(data) == bytes:
            data = l.decode("utf-8")
        if not isinstance(data, AnsiText) and data and data[-1] == "\n":
            data = data[:-1]
        _print(data)


def print_generator(gen):
    if gen == None:
        return
    t = Thread(target=gen_func_loop, args=(gen,), daemon=True)
    t.start()


def _print(s):
    Printer.instance().print(s)


def print(s):
    if type(s) == bytes:
        s = s.decode("utf-8")
    _print(s)


def stop():
    Printer.instance().stop()


class Printer():
    _instace = None

    def __init__(self) -> None:
        self.running = False
        self.run_thread = Thread(target=self._print_in_loop, daemon=True)
        self.print_queue = queue.Queue()
        self.console = Console(tab_size=4)

    @staticmethod
    def instance():
        if not Printer._instace:
            Printer._instace = Printer()
            Printer._instace.start()

        return Printer._instace

    def start(self):
        self.running = True
        self.run_thread.start()

    def _handle_spinner(self, spinner):
        spinner.running = True
        s = Status(spinner.prompt, spinner=spinner.style, console=self.console)
        s.start()
        while spinner.running and self.running:
            time.sleep(0.5)
        s.stop()

    def _handle_progress(self, progress):
        if not progress.trackable:
            return
        progress.running = True
        with Progress(console=self.console, transient=True) as p:
            t = p.add_task(description=progress.description, total=progress.total)
            for update in progress.trackable:
                if not (progress.running and self.running):
                    return
                p.update(t, advance=update)
                time.sleep(0.5)

    def _print_in_loop(self):
        while self.running:
            try:
                data = self.print_queue.get(timeout=1)
                if isinstance(data, list):
                    data = data[0]
                if isinstance(data, Spinner):
                    self._handle_spinner(data)
                    continue
                if isinstance(data, PyntProgress):
                    self._handle_progress(data)
                    continue
                if isinstance(data, str):
                    self.console.print(escape(str(data)))
                    continue
                else:
                    self.console.print(data)
            except queue.Empty:
                pass

        while not self.print_queue.empty():
            self.console.print(self.print_queue.get(), end="")

    def print(self, data):
        if isinstance(data, PrinterText):
            data = data.text
        if isinstance(data, AnsiText):
            data = Text.from_ansi(data.data.decode())
        self.print_queue.put(data)

    def stop(self):
        self.running = False
        self.run_thread.join()


def spinner(prompt, style):
    s = Spinner(prompt, style)
    _print([s])
    return s


def progress(what_to_track, healthcheck, description, total=100):
    pointer_to_progress = [PyntProgress(what_to_track, healthcheck, total, description)]
    _print(pointer_to_progress)
    return pointer_to_progress[0]


def print_verbose(text: str):
    if VERBOSE:
        print(PrinterText(text, PrinterText.INFO))
