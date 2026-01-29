import ctypes
import logging
import sys

from guirecognizerapp.server import createApp

# TODO: refactor with __main__.py
myappid = u'python.guirecognizerapp.1.0.0'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

logger = logging.getLogger('guirecognizerapp')
logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter(fmt='%(levelname)s-%(asctime)s: %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(stream_handler)

app = createApp()
