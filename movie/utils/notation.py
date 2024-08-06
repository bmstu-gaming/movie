import logging

from movie.utils import constants
from movie.utils.logging_config import log

def validation(input_str: str) -> bool:
    numbers = set('0123456789')
    commas = set(',')
    hyphens = set('-')

    for char in input_str:
        if char not in numbers and char not in commas and char not in hyphens:
            return False
    return True


def recognition(input_str: str) -> list[int]:
    log.log_msg(constants.LOG_FUNCTION_START.format(name = 'notation recognition'))
    log.log_msg(f'{input_str = }')

    numbers = []
    try:
        for num in input_str.split(','):
            if '-' in num:
                start, end = num.split('-')
                for i in range(int(start), int(end) + 1):
                    numbers.append(i)
            else:
                numbers.append(int(num))
        for num in numbers:
            log.log_msg(f'{num = }')
    except Exception as e:
        log.log_msg(f'An error occurred: {e}', logging.ERROR)
    log.log_msg(constants.LOG_FUNCTION_END.format(name = 'notation recognition'))
    return numbers
