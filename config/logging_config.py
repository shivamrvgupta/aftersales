import logging
from logging.handlers import TimedRotatingFileHandler

def setup_logging(app):
    handler = TimedRotatingFileHandler(app.config['LOG_FILENAME'], when="midnight", interval=1)
    handler.suffix = "%Y%m%d"
    logger = logging.getLogger('tdm')
    logger.setLevel(app.config['LOG_LEVEL'])
    logger.addHandler(handler)
