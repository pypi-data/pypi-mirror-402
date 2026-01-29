import functools
import logging
import sys
import unittest
from threading import Thread
from typing import Any

logger = logging.getLogger(__name__)

class LoggedTestCase(unittest.TestCase):
  def setUp(self):
    logger = logging.getLogger('guirecognizerapp')
    logger.level = logging.DEBUG
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(fmt='%(levelname)s: %(message)s'))
    logger.addHandler(stream_handler)

# Taken and modified from https://stackoverflow.com/a/21861599 .
def timeout(timeout: int=5):
  def deco(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
      res: list[Any] = [TimeoutError('Function [%s] timeout [%s seconds]' % (func.__name__, timeout))]

      def newFunc():
        try:
          res[0] = func(*args, **kwargs)
        except Exception as e:
          res[0] = e

      thread = Thread(target=newFunc)
      thread.daemon = True
      try:
        thread.start()
        thread.join(timeout)
      except Exception as e:
        logger.error('Error starting thread.')
        raise e
      result = res[0]
      if isinstance(result, BaseException):
        raise result
      return result
    return wrapper
  return deco
