# coding=utf-8
import logging.config
from log_config import log_conf

logging.config.dictConfig(log_conf)
logger = logging.getLogger("tcp")

if __name__ == '__main__':
    logger.info("INFO信息")
    logger.debug("debug信息")
