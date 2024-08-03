import os
import time

from movie.utils.logging_config import LOG


def remove(file_path: str) -> None:
    while True:
        LOG.debug(f'trying to remove: {file_path}')
        try:
            os.remove(file_path)
            break
        except OSError as e:
            if e.winerror == 32:
                err_str = f'Error accessing file {file_path}: the file is using by another process. Please close the program that is using the file.'
                LOG.error(err_str)
                print(err_str)
                time.sleep(5)
            else:
                err_str = f'Error deleting file {file_path}: {e}'
                LOG.error(err_str)
                print(err_str)
                break
        except Exception as e:
            LOG.error(f'Error while removing: {str(e)}')
            print(err_str)
            break
