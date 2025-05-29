from typing import List

from movie.utils import constants
from movie.utils.logging_config import LOG

def validation(input_str: str) -> bool:
    numbers = set('0123456789')
    commas = set(',')
    hyphens = set('-')

    for char in input_str:
        if char not in numbers and char not in commas and char not in hyphens:
            return False
    return True


def recognition(input_str: str) -> List[int]:
    LOG.debug(constants.LOG_FUNCTION_START.format(name = 'notation recognition'))
    LOG.debug(f'{input_str = }')

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
            LOG.debug(f'{num = }')
    except Exception:
        LOG.exception('Error while running program')
    LOG.debug(constants.LOG_FUNCTION_END.format(name = 'notation recognition'))
    return numbers
