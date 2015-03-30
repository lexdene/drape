''' module for debug '''
import os
import logging
import datetime

from . import util, config

_logger = None


def get_logger():
    global _logger
    if _logger is None:
        util.mkdir_not_existing(config.LOGFILE_DIR)

        now = datetime.datetime.now()
        filepath = dirpath + '/%s.log' % (
            now.strftime('%Y-%m-%d'),
        )
        logging.basicConfig(
            filename=filepath,
            level=logging.DEBUG,
            format=(
                '[%(asctime)s] [%(levelname)s] '
                '[%(name)s:%(lineno)d] '
                '[%(funcName)s]\n'
                '%(message)s'
            )
        )

        _logger = logging.getLogger()

    return _logger
