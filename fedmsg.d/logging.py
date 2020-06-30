# Setup fedmsg logging.
# See the following for constraints on this format http://bit.ly/Xn1WDn
bare_format = "[%(asctime)s][%(name)10s %(levelname)7s] %(message)s"

config = {
    'logging': {
        'version': 1,
        'formatters': {
            'bare': {
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "format": bare_format
            },
        },
        'handlers': {
            'console': {
                "class": "logging.StreamHandler",
                "formatter": "bare",
                "level": "DEBUG",
                "stream": "ext://sys.stdout",
            }
        },
        'loggers': {
            'fedmsg': {
                "level": "DEBUG",
                "propagate": False,
                "handlers": ["console"],
            },
            'moksha': {
                "level": "DEBUG",
                "propagate": False,
                "handlers": ["console"],
            },
            'pkgdb2client': {
                "level": "INFO",
                "propagate": False,
                "handlers": ["console"],
            },
            'modules': {
                "level": "DEBUG",
                "propagate": False,
                "handlers": ["console"],
            },
            'pdcupdater': {
                "level": "DEBUG",
                "propagate": False,
                "handlers": ["console"],
            },
        },
    },
}
