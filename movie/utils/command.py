import subprocess

from movie.utils import constants
from movie.utils.logging_config import LOG


def execute(command: list[str]) -> subprocess.CompletedProcess[str]:
    LOG.debug(f'╔{constants.EQUALS} COMMAND EXECUTION {constants.EQUALS}╗')
    command_str = ' '.join(command)
    LOG.debug(f'{command_str = }')

    stdout = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True)

    LOG.debug(f'{stdout.args = }')
    LOG.debug(f'{stdout.returncode = }')
    LOG.debug(f'{stdout.stderr = }')
    LOG.debug(f'{stdout.stdout = }')
    LOG.debug(f'╚{constants.EQUALS} COMMAND EXECUTION {constants.EQUALS}╝')

    return stdout
