log_conf = {
    "version": 1,
    "formatters": {
        "tcp_info": {
            # "format": "%(asctime)s - %(pathname)s - %(lineno)s - %(name)s - %(levelname)s - %(message)s"
            "format": "%(lineno)s - %(message)s"
            # "format": "%(asctime)s - %(message)s"
        },
        "tcp_debug": {
            # "format": "%(asctime)s - %(pathname)s - %(lineno)s - %(name)s - %(levelname)s - %(message)s",
            "format": "%(lineno)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "filters": {},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "tcp_debug",
            "level": "DEBUG"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False
        }
    }
}
