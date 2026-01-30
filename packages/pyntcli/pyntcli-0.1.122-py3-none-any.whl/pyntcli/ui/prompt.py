from sys import stdin
from pyntcli.ui import ui_thread
from timedinput import timedinput


class TimeoutExpired(Exception):
    pass


def _timeout_handler(signum, frame):
    raise TimeoutExpired


def confirmation_prompt_with_timeout(question, default, timeout=10):
    """Prompt the user with a confirmation question (Yes/No) and return True for 'yes' or False for 'no'.

    Args:
        question (str): The question to present to the user.
        default (str): The default answer if the user just presses Enter. It should be 'yes' or 'no'.
        timeout (int): The timeout in seconds. If the user doesn't respond within the timeout, the default answer will be selected.

    Returns:
        bool: True if the answer is 'yes', False if the answer is 'no'.
    """
    valid = {"yes": True, "y": True, "no": False, "n": False}

    # If stdin isn't a tty, we can't prompt the user
    if not stdin.isatty():
        return valid[default]

    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError(f"Invalid default answer: '{default}'")

    while True:
        choice = timedinput(question + prompt, timeout=timeout, default=default).strip().lower()

        if choice == "" and default:  # Only 'Enter' with default will continue
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            ui_thread.print("Please respond with 'yes' or 'no' (or 'y' or 'n').")

