import argparse
import ctypes
import logging
import sys
import webbrowser
from importlib.resources import files

import uvicorn
from fastapi.staticfiles import StaticFiles

from guirecognizerapp.server import createApp

# Make the icon of a tkinter window the icon in the taskbar instead of the default python icon.
# TODO: this code is certainly windows specific, test and fix it for linux (and mac)
# TODO: don't hardcode version number
myappid = u'python.guirecognizerapp.1.0.0'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

def main():
  logger = logging.getLogger('guirecognizerapp')
  logger.level = logging.DEBUG
  stream_handler = logging.StreamHandler(sys.stdout)
  stream_handler.setFormatter(logging.Formatter(fmt='%(levelname)s-%(asctime)s: %(message)s', datefmt='%H:%M:%S'))
  logger.addHandler(stream_handler)

  parser = argparse.ArgumentParser(description='Start the server of the companion application guirecognizerapp for guirecognizer.')
  parser.add_argument('-n', '--no-browser', action='store_true', help='Start the server without opening a browser window.')
  parser.add_argument('-p', '--port', type=int, default=8000, help='Port to run the server on (default: 8000).')
  args = parser.parse_args()

  app = createApp()
  app.mount('/', StaticFiles(directory=str(files('guirecognizerapp').joinpath('generated', 'client')), html=True), name='client')
  if not args.no_browser:
    webbrowser.open(f'http://127.0.0.1:{args.port}')
  uvicorn.run(app, host='127.0.0.1', port=args.port, ws_max_size=500 * 1024 * 1024)

if __name__ == '__main__':
  main()
