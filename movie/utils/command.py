import subprocess

from movie.utils import constants
from movie.utils.logging_config import log


def execute(command: list[str]) -> subprocess.CompletedProcess[str]:
    log.log_msg(constants.LOG_FUNCTION_START.format(name = 'COMMAND EXECUTION'))
    command_str = ' '.join(command)
    log.log_msg(f'{command_str = }')

    stdout = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True)

    log.log_msg(f'{stdout.args = }')
    log.log_msg(f'{stdout.returncode = }')
    log.log_msg(f'{stdout.stderr = }')
    log.log_msg(f'{stdout.stdout = }')
    log.log_msg(constants.LOG_FUNCTION_END.format(name = 'COMMAND EXECUTION'))

    return stdout
