import logging
import logging.config

from movie.utils import constants


LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'file_log': {
            'format': '%(asctime)s [%(levelname)s]\t%(message)s'
        },
        'console_log': {
            'format': '%(message)s'
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': constants.LOG_FILE,
            'encoding': 'utf-8',
            'formatter': 'file_log',
            'level': logging.DEBUG,
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console_log',
            'level': logging.INFO,
        },
    },
    'loggers': {
        __name__: {
            'level': logging.DEBUG,
            'handlers': ['file', 'console'],
            'propagate': False
        }
    }
}
logging.config.dictConfig(LOG_CONFIG)
LOG = logging.getLogger(__name__)
