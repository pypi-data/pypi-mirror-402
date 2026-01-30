import platform
import shutil
import subprocess
import os
import json
import argparse
import threading
from datetime import datetime
from typing import List

from . import container_utils

from pyntcli.ui import ui_thread
from pyntcli.analytics import send as analytics
from pyntcli.store import CredStore
from pyntcli.auth.login import PYNT_ID, PYNT_SAAS

PYNT_DOCKER_IMAGE = "ghcr.io/pynt-io/pynt"


def create_mount(src, destination, mount_type="bind"):
    return {
        'Target': destination,
        'Source': src,
        'Type': mount_type,
        'ReadOnly': False,
        'NoCopy': False,
    }


class DockerNotAvailableException(Exception):
    pass


class DockerNativeUnavailableException(Exception):
    pass


class ImageUnavailableException(Exception):
    pass


class PortInUseException(Exception):
    def __init__(self, port=""):
        self.message = ui_thread.print(
            ui_thread.PrinterText(f"Port: {port} already in use, please use a different one", ui_thread.PrinterText.WARNING))
        super().__init__(self.message)


def get_docker_platform_name():
    try:
        version_data = json.loads(subprocess.check_output(["docker", "version", "--format", "{{json .}}"], text=True))
        platform = version_data.get("Server", {}).get("Platform", {})
        analytics.deferred_emit(analytics.DOCKER_PLATFORM, platform)
        return platform.get("Name", "")
    except Exception:
        raise DockerNotAvailableException()


class PyntBaseContainer():
    def __init__(self, docker_type, docker_arguments, mounts, environment={}) -> None:
        self.docker_type = docker_type
        self.docker_arguments = docker_arguments
        self.mounts = mounts
        self.environment = environment


class _PyntDockerPort:
    def __init__(self, port: int, name: str) -> None:
        self.port = port
        self.name = name


def api_port(port: int) -> _PyntDockerPort:
    return _PyntDockerPort(port=port, name="--port")


def proxy_port(port: int) -> _PyntDockerPort:
    return _PyntDockerPort(port=port, name="--proxy-port")


class PyntDockerImage:
    def __init__(self, name, is_self_managed) -> None:
        self.name = name
        self.is_self_managed = is_self_managed


class DockerContainerConfig:
    def __init__(self, args: argparse.Namespace, integration_name: str, *port_args: _PyntDockerPort):
        self.image = get_image_config(args)
        self.is_detach = True
        self.ports: List[int] = [port_arg.port for port_arg in port_args]
        self.docker_arguments = build_docker_args(integration_name, args, port_args)
        self.mounts = get_docker_mounts(args)
        self.env_vars = {PYNT_ID: CredStore().get_tokens(), "PYNT_SAAS_URL": PYNT_SAAS}
        otel_endpoint = os.environ.get("OTEL_COLLECTOR_ENDPOINT")
        if otel_endpoint:
            self.env_vars["OTEL_COLLECTOR_ENDPOINT"] = otel_endpoint


def get_image_config(args: argparse.Namespace) -> PyntDockerImage:
    default_image = f'{PYNT_DOCKER_IMAGE}:v1-latest'
    if "pynt_image" in args and args.pynt_image:
        return PyntDockerImage(args.pynt_image, True)
    env_name = value_from_environment_variable("IMAGE")
    env_tag = value_from_environment_variable("TAG")
    if env_name:
        return PyntDockerImage(f'{env_name}:{env_tag}', True)

    return PyntDockerImage(default_image, False)


def is_network_host() -> bool:
    platform_sys_name = platform.system()
    if platform_sys_name == "Windows" or platform_sys_name == "Darwin":
        return False
    else:
        docker_platform_name = get_docker_platform_name().lower()
        if "desktop" in docker_platform_name:
            return False
        return True


def value_from_environment_variable(key):
    e = os.environ.get(key)

    if e:
        ui_thread.print_verbose(f"Using environment variable {key}={e}")
        return e

    return None


def build_docker_args(integration_name: str, args: argparse.Namespace, port_args: List[_PyntDockerPort]) -> List[str]:
    docker_arguments = [integration_name]

    if "insecure" in args and args.insecure:
        docker_arguments.append("--insecure")

    if "application_id" in args and args.application_id:
        docker_arguments += ["--application-id", args.application_id]

    if "application_name" in args and args.application_name:
        docker_arguments += ["--application-name", args.application_name]

    if "proxy" in args and args.proxy:
        docker_arguments += ["--proxy", args.proxy]

    if "dev_flags" in args:
        docker_arguments += args.dev_flags.split(" ")

    if "host_ca" in args and args.host_ca:
        ca_name = os.path.basename(args.host_ca)
        docker_arguments += ["--host-ca", ca_name]

    if "verbose" in args and args.verbose:
        docker_arguments.append("--verbose")

    if "tag" in args and args.tag:
        for tag in args.tag:
            docker_arguments += ["--tag", tag[0]]
            
    for port_arg in port_args:
        docker_arguments += [port_arg.name, str(port_arg.port)]

    return docker_arguments


def get_docker_mounts(args: argparse.Namespace) -> list:
    mounts = []
    if "host_ca" in args and args.host_ca:
        ca_name = os.path.basename(args.host_ca)
        mounts.append(create_mount(os.path.abspath(args.host_ca), "/etc/pynt/{}".format(ca_name)))
        mounts.append(create_mount(os.path.abspath(args.host_ca),
                                   "/usr/local/share/ca-certificates/pynt_ca.crt:ro"))

    return mounts


class DockerLogFollower(threading.Thread):
    def __init__(self, docker_exec: str, container_id: str):
        super().__init__(target=self._run, name="docker logs follower")
        self.docker_exec = docker_exec
        self.container_id = container_id

    def _run(self):
        logs_process = subprocess.Popen(
            [self.docker_exec, "logs", "-f", self.container_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        while True:
            line = logs_process.stdout.readline()
            if not line:
                break

            now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
            log_line = ui_thread.Text(f"{now} [container]", "default on grey53")
            log_line.append(f" {line}", "bold yellow on default")

            ui_thread.print(log_line)



        logs_process.wait()

class PyntContainerNative:
    def __init__(self, container_config: DockerContainerConfig):
        self.config = container_config
        self.container_name = "pynt_engine"
        self.system = platform.system().lower()
        self.stdout = None
        self.running = False

        creds_path = os.path.dirname(CredStore().file_location)
        mitm_cert_path = os.path.join(creds_path, "cert")
        os.makedirs(mitm_cert_path, exist_ok=True)
        self.config.mounts.append(create_mount(mitm_cert_path, "/root/.mitmproxy"))

    def is_alive(self):
        command = ["docker", "ps", "--filter", f"name={self.container_name}", "--filter", "status=running"]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        return len(result.stdout.splitlines()) > 1

    def prepare_client(self):
        pass

    def run(self):
        self.running = True

        self.fetch_and_validate_image()
        args = self.config.docker_arguments if self.config.docker_arguments else None
        docker_exec = shutil.which("docker")
        docker_command = [docker_exec, "run", "--rm", "-d", "--name", self.container_name]

        mounts = []
        for mount in self.config.mounts:
            mounts.extend(["-v", f"{mount['Source']}:{mount['Target']}"])

        env_vars = []
        for key, value in self.config.env_vars.items():
            env_vars.extend(["-e", f"{key}={value}"])

        if is_network_host():
            ports_exposure = ["--network=host"]
        else:
            ports_exposure = []
            for port in self.config.ports:
                ports_exposure.extend(["-p", f"{port}:{port}"])

        docker_command += mounts
        docker_command += env_vars
        docker_command += ports_exposure
        docker_command += [f"{self.config.image.name}"]
        docker_command += args

        ui_thread.print_verbose(f"Running command (contains sensitive user secrets, do not paste outside this machine!):\n"
                                f"#########################\n {' '.join(docker_command)}\n#########################\n")

        PyntContainerRegistry.instance().register_container(self)
        process = subprocess.Popen(docker_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        container_id = stdout.strip()

        if process.returncode and process.returncode != 0:
            formatted_response = f"Unable to perform docker run command, return code: {process.returncode}"
            if ui_thread.VERBOSE:
                if stderr is not None and len(stderr) > 0:
                    formatted_response += f"\nstderr\n---\n\n{stderr}"
                if stdout is not None and len(stdout) > 0:
                    formatted_response += f"\nstdout\n---\n\n{stdout}"
            raise DockerNativeUnavailableException(formatted_response)

        if ui_thread.VERBOSE:
            # Start log streaming in a separate thread
            DockerLogFollower(docker_exec, container_id).start()

    def kill_other_instances(self, gracefully: bool) -> int:
        ui_thread.print_verbose("Killing other pynt containers if such exist")
        killed_containers = 0
        try:
            container_ids = container_utils.list_running_containers(name=self.container_name)
            for container_id in container_ids:
                if gracefully:
                    container_utils.kill_container_gracefully(container_id)
                else:
                    container_utils.kill_container(container_id)
                killed_containers += 1
        except subprocess.CalledProcessError:
            analytics.emit(analytics.ERROR, {"error": "Unable to kill other pynt containers"})
            ui_thread.print(ui_thread.PrinterText("Error: Unable to kill other pynt containers", ui_thread.PrinterText.WARNING))

        return killed_containers

    def fetch_and_validate_image(self):
        try:
            ui_thread.print(ui_thread.PrinterText("Pulling latest docker image", ui_thread.PrinterText.INFO))
            pull_command = ['docker', 'pull', self.config.image.name]
            get_image_command = ['docker', 'images', '-q', f'{self.config.image.name}']
            ui_thread.print_verbose(f"Docker pull command:\n{' '.join(pull_command)}")
            pull_process = subprocess.Popen(pull_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, pull_stderr = pull_process.communicate()
            get_process = subprocess.Popen(get_image_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            get_stdout, _ = get_process.communicate()
            local_image_id = get_stdout.decode('utf-8')
            if self.config.image.is_self_managed and local_image_id:
                ui_thread.print_verbose(f"Using local image {local_image_id}")
                return local_image_id.strip()
            elif local_image_id == "":
                ui_thread.print(ui_thread.PrinterText(f"Error: the image {self.config.image.name} not found",
                                                      ui_thread.PrinterText.WARNING))
                raise ImageUnavailableException("Failed to find local image")
            if pull_stderr and local_image_id == "":
                ui_thread.print(ui_thread.PrinterText(f"Error: {pull_stderr}", ui_thread.PrinterText.WARNING))
                raise ImageUnavailableException("Failed to pull image")

            if pull_process.returncode != 0:
                raise ImageUnavailableException("Failed to pull image")

            ui_thread.print_verbose("Image pulled successfully")

        except Exception as e:
            raise ImageUnavailableException(f"An error occurred: {str(e)}")

    def stop(self):
        if not self.running:
            return
        self.kill_other_instances(gracefully=True)
        self.running = False

    def pre_run_validation(self, port):
        killed_containers = self.kill_other_instances(gracefully=False)
        if killed_containers > 0:
            ui_thread.print(
                ui_thread.PrinterText(
                    "Another Pynt container was running, killed it",
                    ui_thread.PrinterText,
                )
            )

        ui_thread.print_verbose("Checking if port is in use")
        if container_utils.is_port_in_use(int(port)):
            ui_thread.print_verbose(f"Port {port} is in use")
            raise PortInUseException(port)

        ui_thread.print_verbose("Port is not in use")


class PyntContainerRegistry:
    _instance = None

    def __init__(self) -> None:
        self.containers: List[PyntContainerNative] = []

    @staticmethod
    def instance():
        if not PyntContainerRegistry._instance:
            PyntContainerRegistry._instance = PyntContainerRegistry()

        return PyntContainerRegistry._instance

    def register_container(self, c: PyntContainerNative):
        ui_thread.print_verbose("Registering container")
        self.containers.append(c)

    def stop_all_containers(self):
        ui_thread.print_verbose("Stopping all containers")
        for c in self.containers:
            c.stop()
