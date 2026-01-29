import logging
import sys
import unittest


class LoggedTestCase(unittest.TestCase):
  def setUp(self):
    logger = logging.getLogger('guirecognizer')
    logger.level = logging.DEBUG
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(fmt='%(levelname)s: %(message)s'))
    logger.addHandler(stream_handler)
