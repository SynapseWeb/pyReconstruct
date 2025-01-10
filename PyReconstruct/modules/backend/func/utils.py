import subprocess
import uuid


def make_unique_id() -> int:
    """Return a uuid."""

    return uuid.uuid4().int


def run_command(cmd):
    """Run a command and return output."""

    return subprocess.run(cmd, capture_output=True, text=True, shell=True)


def get_stdout(cmd):
    """Get stdout from a command."""

    return run_command(                 cmd).stdout
