import logging
import logging.config

from movie.utils import constants


LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s [%(levelname)s]\t%(message)s'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': constants.LOG_FILE,
            'encoding': 'utf-8',
            'formatter': 'default'
        }
    },
    'loggers': {
        __name__: {
            'level': logging.DEBUG,
            'handlers': ['file'],
            'propagate': False
        }
    }
}
logging.config.dictConfig(LOG_CONFIG)
LOG = logging.getLogger(__name__)


class Logger:
    def __init__(self, logger):
        self.logger = logger

    def log_msg(self, message, level=logging.DEBUG):
        if level == logging.DEBUG:
            self.logger.debug(message)
        elif level == logging.INFO:
            self.logger.info(message)
        elif level == logging.WARNING:
            self.logger.warning(message)
        elif level == logging.ERROR:
            self.logger.error(message)
        elif level == logging.CRITICAL:
            self.logger.critical(message)

        if level >= logging.INFO:
            print(message)


log = Logger(LOG)
