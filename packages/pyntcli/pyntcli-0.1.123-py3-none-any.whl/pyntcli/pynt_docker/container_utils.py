import socket
import subprocess
import time
from typing import Optional, List

GRACEFUL_KILL_TIMEOUT_SECONDS = 10


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def list_running_containers(
    name: Optional[str] = None, container_id: Optional[str] = None
) -> List[str]:
    ps_filter = []
    if name is not None:
        ps_filter.extend(["-f", f"name={name}"])
    elif container_id is not None:
        ps_filter.extend(["-f", f"id={container_id}"])

    output = subprocess.check_output(
        ["docker", "ps", "-a", "-q", *ps_filter],
        text=True,
    )
    return output.splitlines()


def kill_container_gracefully(container_id: str):
    subprocess.run(
        ["docker", "kill", "--signal", "SIGINT", container_id],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(GRACEFUL_KILL_TIMEOUT_SECONDS):
        time.sleep(1)
        is_still_running = len(list_running_containers(container_id=container_id)) > 0
        if not is_still_running:
            return

    if len(list_running_containers(container_id=container_id)) > 0:
        kill_container_gracefully(container_id)


def kill_container(container_id: str):
    # `doccker remove -f` sends SIGKILL
    subprocess.run(
        ["docker", "remove", "-f", container_id],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
