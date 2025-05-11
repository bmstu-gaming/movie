import subprocess
from typing import List

from movie.utils import constants
from movie.utils.logging_config import LOG


def execute(command: List[str]) -> subprocess.CompletedProcess:
    LOG.debug(constants.LOG_FUNCTION_START.format(name = 'COMMAND EXECUTION'))
    command_str = ' '.join(command)
    LOG.debug(f'{command_str = }')

    try:
        stdout = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True)
    except subprocess.CalledProcessError as exc:
        LOG.debug(f'{exc.returncode = }')
        LOG.debug(f'{exc.stderr = }')
        LOG.debug(f'{exc.output = }')
        raise RuntimeError(f'''Command
{command_str}
returned non-zero exit status {exc.returncode}.
More information in movie.log''') from exc

    LOG.debug(f'{stdout.args = }')
    LOG.debug(f'{stdout.returncode = }')
    LOG.debug(f'{stdout.stderr = }')
    LOG.debug(f'{stdout.stdout = }')
    LOG.debug(constants.LOG_FUNCTION_END.format(name = 'COMMAND EXECUTION'))

    return stdout
