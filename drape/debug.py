''' module for debug '''
import os
import logging
import datetime

from . import util

_logger = None


def get_logger():
    global _logger
    if _logger is None:
        from . import application
        dirpath = os.path.join(
            application.instance.root_dir,
            'data/log'
        )
        util.mkdir_not_existing(dirpath)

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
