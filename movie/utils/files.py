import logging
import os
import time

from movie.utils import constants
from movie.utils.logging_config import log


def remove(file_path: str) -> None:
    while True:
        log.log_msg(f'trying to remove: {file_path}')
        try:
            os.remove(file_path)
            break
        except OSError as e:
            if e.winerror == 32:
                err_str = f'Error accessing file {file_path}: the file is using by another process. Please close the program that is using the file.'
                log.log_msg(err_str, logging.ERROR)
                time.sleep(5)
            else:
                err_str = f'Error deleting file {file_path}: {e}'
                log.log_msg(err_str, logging.ERROR)
                break
        except Exception as e:
            err_str = f'Error while removing: {str(e)}'
            log.log_msg(err_str, logging.ERROR)
            break


def rename(old_path, new_path):
    while True:
        log.log_msg(f'trying to rename: {old_path}')
        try:
            os.rename(old_path, new_path)
            break
        except OSError as e:
            if e.winerror == 32:
                err_str = f'Error accessing file {old_path}: the file is using by another process. Please close the program that is using the file.'
                log.log_msg(err_str, logging.ERROR)
                time.sleep(5)
            else:
                err_str = f'Error renaming file {old_path}: {e}'
                log.log_msg(err_str, logging.ERROR)
                break
        except Exception as e:
            err_str = f'Error while renaming file {old_path}: {str(e)}'
            log.log_msg(err_str, logging.ERROR)
            break


def restoring_target_filename_to_source(path_target: str, path_source: str):
    log.log_msg(constants.LOG_FUNCTION_START.format(name='restoring target filename to source filename'))
    remove(path_source)
    rename(path_target, path_source)
    log.log_msg(constants.LOG_FUNCTION_END.format(name='restoring target filename to source filename'))
