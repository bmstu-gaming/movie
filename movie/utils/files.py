import os
import time

from movie.utils import constants
from movie.utils.logging_config import LOG


def _is_file_exists(file_path: str) -> bool:
    return os.path.isfile(file_path)


def remove(file_path: str) -> None:
    while True:
        LOG.debug(f'trying to remove: {file_path}')
        if not _is_file_exists(file_path):
            return
        try:
            os.remove(file_path)
            break
        except OSError as exc:
            err_str = f'Error deleting file {file_path}: {exc}'
            LOG.error(err_str)
            time.sleep(5)
        except Exception as exc:
            LOG.exception('Error while running program')
            err_str = f'Error while removing: {str(exc)}'
            LOG.error(err_str)
            break


def rename(old_path, new_path):
    while True:
        LOG.debug(f'trying to rename: {old_path}')
        if not _is_file_exists(old_path):
            return
        try:
            os.rename(old_path, new_path)
            break
        except OSError as exc:
            err_str = f'Error renaming file {old_path}: {exc}'
            LOG.error(err_str)
            time.sleep(5)
        except Exception as exc:
            LOG.exception('Error while running program')
            err_str = f'Error while renaming file {old_path}: {str(exc)}'
            LOG.error(err_str)
            break


def restoring_target_filename_to_source(path_target: str, path_source: str):
    LOG.debug(
        constants.LOG_FUNCTION_START.format(name='Restoring TARGET filename to SOURCE filename'))
    remove(path_source)
    rename(path_target, path_source)
    LOG.debug(
        constants.LOG_FUNCTION_END.format(name='restoring TARGET filename to SOURCE filename'))
