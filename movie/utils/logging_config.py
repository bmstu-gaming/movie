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