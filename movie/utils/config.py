import configparser
import os
import re
import sys
from typing import List
from typing import Tuple

from movie.utils import command
from movie.utils import constants
from movie.utils.logging_config import LOG
from movie.utils.movie import Movie


def _config_load(config_path: str = constants.CONFIG_PATH) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    return config


def _config_get_values(movie_config: configparser.ConfigParser) -> Tuple[List[str]]:
    return (str(movie_config.get('Config', 'FFMPEG_PATH', fallback=None)),
            str(movie_config.get('Config', 'FFPROBE_PATH', fallback=None)),
            str(movie_config.get('Config', 'MOVIES_FOLDER', fallback=None)),
            str(movie_config.get('Config', 'NAME_TEMPLATE', fallback=None)))


def _config_validate(movie_config: configparser.ConfigParser) -> Tuple[dict, bool]:
    config_statuses = {}
    is_valid = True

    ffmpeg_path, ffprobe_path, movies_folder, name_template = _config_get_values(movie_config)

    result, message = _verification_ffmpeg_path(ffmpeg_path)
    is_valid = is_valid and result
    config_statuses['FFMPEG_PATH'] = f'"{ffmpeg_path}" {constants.CHECK if result else constants.CROSS} {message}'
    
    result, message = _verification_ffprobe_path(ffprobe_path)
    is_valid = is_valid and result
    config_statuses['FFPROBE_PATH'] = f'"{ffprobe_path}" {constants.CHECK if result else constants.CROSS} {message}'

    result, message = _verification_movies_folder(movies_folder)
    is_valid = is_valid and result
    config_statuses['MOVIES_FOLDER'] = f'"{movies_folder}" {constants.CHECK if result else constants.CROSS} {message}'

    result, message = _verification_name_template(name_template)
    is_valid = is_valid and result
    config_statuses['NAME_TEMPLATE'] = f'"{name_template}" {constants.CHECK if result else constants.CROSS} {message}'

    return config_statuses, is_valid


def _verification_ffmpeg_path(ffmpeg_path: str) -> Tuple[bool, str]:
    if not ffmpeg_path:
        return False, 'not set'

    if not os.path.isfile(ffmpeg_path):
        return False, 'file not found'

    run_cmd = [ffmpeg_path, '-version']
    try:
        command.execute(run_cmd)
    except Exception as exc:
        return False, str(exc)

    return True, ''


def _verification_ffprobe_path(ffprobe_path: str) -> Tuple[bool, str]:
    if not ffprobe_path:
        return False, 'not set'

    if not os.path.isfile(ffprobe_path):
        return False, 'file not found'

    run_cmd = [ffprobe_path, '-version']
    try:
        command.execute(run_cmd)
    except Exception as exc:
        return False, str(exc)

    return True, ''


def _verification_movies_folder(movies_folder: str) -> Tuple[bool, str]:
    if not movies_folder:
        return False, 'not set'

    if not os.path.isdir(movies_folder):
        return False, 'folder not found'

    return True, ''


def _verification_name_template(name_template: str) -> Tuple[bool, str]:
    if not name_template:
        return False, 'not set'

    if not re.match(constants.NAME_TEMPLATE_VERIFICATION_REGEX, name_template):
        return False, 'contains special characters'

    return True, ''


def _load_and_validate_config(config_path: str = constants.CONFIG_PATH) -> configparser.ConfigParser:
    config = _config_load(config_path)
    config_statuses, is_valid = _config_validate(config)

    for key, message in config_statuses.items():
        LOG.info(f"{key}: {message}")

    if not is_valid:
        print(f'logs in {constants.LOG_FILE}')
        print(f'Config not valid. Program exit. {constants.CROSS}')
        LOG.error('Config not valid. Program exit.')
        sys.exit(1)

    return config


def apply_config(config_path: str = constants.CONFIG_PATH) -> Movie:
    config = _load_and_validate_config(config_path)
    return Movie(*_config_get_values(config))


def update_config(obj: Movie, config_path: str = constants.CONFIG_PATH) -> None:
    config = _load_and_validate_config(config_path)
    obj.ffmpeg_path, obj.movies_folder, obj.name_template = _config_get_values(config)
