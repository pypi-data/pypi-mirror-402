from sys import argv, exit
import signal
import os
from pyntcli.commands import pynt_cmd
from pyntcli.pynt_docker import pynt_container
from pyntcli.ui import ui_thread
from pyntcli.ui import pynt_errors
from pyntcli.auth import login
from pyntcli.analytics import send as analytics
from requests.exceptions import SSLError
from requests.exceptions import ProxyError
from pyntcli.transport.pynt_requests import InvalidPathException, InvalidCertFormat
from pyntcli.commands.util import HtmlReportNotCreatedException
from pyntcli.commands.util import SomeFindingsOrWarningsException, SeverityException
from pyntcli.commands.postman import PyntWebSocketException
from pyntcli import __version__

from pyntcli.store import CredStore


def shutdown_cli():
    analytics.stop()
    pynt_container.PyntContainerRegistry.instance().stop_all_containers()
    ui_thread.stop()


def signal_handler(signal_number, frame):
    ui_thread.print(ui_thread.PrinterText("Exiting..."))

    shutdown_cli()

    exit(0)

def print_header():
    ui_thread.print(ui_thread.PrinterText(*ui_thread.pynt_header())
                    .with_line(*ui_thread.pynt_version())
                    .with_line(""))


def start_analytics(user_id: str):
    if user_id:
        analytics.set_user_id(user_id)


def logout():
    creds_path = CredStore().get_path()
    try:
        if os.path.isfile(creds_path):
            os.remove(creds_path)
            ui_thread.print("you have successfully logged out")
            return
    except Exception:
        ui_thread.print(f"not able to log out - try to manually delete the {creds_path} file")

    ui_thread.print("you are not logged in. run pynt --help and choose the required command")


def main():
    print_header()
    try:
        if len(argv) == 1:
            pynt_cmd.root.usage()
            return

        if argv[1] == "logout":
            logout()
            return

        if "--verbose" in argv:
            ui_thread.VERBOSE = True

        ui_thread.print_verbose("Logging in...")
        user_id = login.user_id()
        start_analytics(user_id)
        ui_thread.print_verbose("Asserting docker is properly installed")
        platform_name = pynt_container.get_docker_platform_name()
        ui_thread.print_verbose("Docker platform: {}".format(platform_name))
        signal.signal(signal.SIGINT, signal_handler)
        cli = pynt_cmd.PyntCommand()
        cli.run_cmd(cli.parse_args(argv[1:]))
        analytics.stop()
    except pynt_cmd.PyntCommandException as e:
        pynt_cmd.root.usage()
    except pynt_container.DockerNotAvailableException as e:
        ui_thread.print(ui_thread.PrinterText("Docker was unavailable, please make sure docker is installed and running.", ui_thread.PrinterText.WARNING))
        analytics.emit(analytics.ERROR, {"error": "docker unavailable. e: {}".format(e)})
    except SSLError as e:
        ui_thread.print(
            ui_thread.PrinterText("We encountered SSL issues and could not proceed, this may be the cause of a VPN or a Firewall in place. Run again with --insecure", ui_thread.PrinterText.WARNING))
        analytics.emit(analytics.ERROR, {"error": "ssl error. e: {}".format(e)})
    except login.Timeout as e:
        ui_thread.print(ui_thread.PrinterText("Pynt CLI exited due to incomplete registration, please try again.", ui_thread.PrinterText.WARNING))
        analytics.emit(analytics.ERROR, {"error": "login timeout. e: {}".format(e)})
    except login.InvalidTokenInEnvVarsException as e:
        ui_thread.print(ui_thread.PrinterText("Pynt CLI exited due to malformed credentials provided in env vars.", ui_thread.PrinterText.WARNING))
        analytics.emit(analytics.ERROR, {"error": "invalid pynt cli credentials in env vars. e: {}".format(e)})
    except pynt_container.ImageUnavailableException as e:
        analytics.emit(analytics.ERROR, {"error": "Couldn't pull pynt image and no local image found. e: {}".format(e)})
        ui_thread.print(ui_thread.PrinterText("Error: Couldn't pull pynt image and no local image found.", ui_thread.PrinterText.WARNING))
    except HtmlReportNotCreatedException as e:
        analytics.emit(analytics.ERROR, {"error": "Html report was not created. e: {}".format(e)})
        ui_thread.print(ui_thread.PrinterText("Pynt CLI exited: Html report was not created.", ui_thread.PrinterText.WARNING))
    except InvalidPathException as e:
        ui_thread.print(ui_thread.PrinterText("Pynt CLI exited due to invalid host-CA path: {}".format(e), ui_thread.PrinterText.WARNING))
        analytics.emit(analytics.ERROR, {"error": "Host CA path provided was invalid. e: {}".format(e)})
    except InvalidCertFormat as e:
        ui_thread.print(ui_thread.PrinterText("Pynt CLI exited due to invalid host-CA. Please provide a file in PEM format: {}".format(e), ui_thread.PrinterText.WARNING))
        analytics.emit(analytics.ERROR, {"error": "Host CA provided was not in valid pem format. e: {}".format(e)})
    except PyntWebSocketException as e:
        analytics.emit(analytics.ERROR, {"error": "postman websocket failed to connect. e: {}".format(e)})
        ui_thread.print(ui_thread.PrinterText("Pynt CLI exited: postman websocket failed to connect", ui_thread.PrinterText.WARNING))
    except ProxyError as e:
        ui_thread.print(ui_thread.PrinterText("Pynt CLI exited due to a proxy error. check if your proxy is up", ui_thread.PrinterText.WARNING))
        analytics.emit(analytics.ERROR, {"error": "there was a proxy error. e: {}".format(e)})
    except pynt_container.PortInUseException as e:
        analytics.emit(analytics.ERROR, {"error": "port in use. e: {}".format(e)})
    except SomeFindingsOrWarningsException as e:
        exit(1)
    except SeverityException as e:
        exit(1)
    except Exception as e:
        analytics.emit(analytics.ERROR, {"error": "{}".format(e)})
        pynt_errors.unexpected_error(e)

    finally:
        shutdown_cli()


if __name__ == "__main__":
    main()
