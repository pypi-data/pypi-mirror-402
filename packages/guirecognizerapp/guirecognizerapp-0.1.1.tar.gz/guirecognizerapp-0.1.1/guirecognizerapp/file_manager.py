import json
import os
from tkinter.filedialog import askopenfile, asksaveasfile
from typing import TYPE_CHECKING, Any

from showinfm.showinfm import show_in_file_manager

from guirecognizerapp.screen_helper import getTkinterWindow
from guirecognizerapp.server_client_interface import ServerResponseType

if TYPE_CHECKING:
  from guirecognizerapp.cache_manager import CacheDataManager
  from guirecognizerapp.call_manager import CallManager

class FileManager():
  def __init__(self, callManager: 'CallManager', cacheManager: 'CacheDataManager') -> None:
    self.callManager = callManager
    self.cacheManager = cacheManager

  async def initClient(self) -> None:
    await self.sendRecentFiles()

  async def sendRecentFiles(self) -> None:
    response = {'type': ServerResponseType.RECENT_FILES, 'files': self.cacheManager.getRecentFiles()}
    await self.callManager.sendResponse(response)

  async def clearRecentFiles(self) -> None:
    self.cacheManager.clearRecentFiles()
    await self.sendRecentFiles()

  async def openFileFromDialog(self) -> None:
    window = getTkinterWindow()
    filetypes = [(_('file.open.dialog.jsonFilename'), '*.json'), (_('file.open.dialog.otherFilename'), '*.*')]
    fileInfo = askopenfile(parent=window, filetypes=filetypes, title=_('file.open.dialog.title'))
    window.destroy()
    if fileInfo is None:
      return
    await self.openFile(fileInfo.name)

  async def openFile(self, filepath: str) -> None:
    try:
      with open(filepath, 'r') as file:
        try:
          data = json.load(file)
        except:
          await self.manageOpenFileError(filepath)
          # il8n: {filename}
          error = _('file.open.error.cannotLoad').format(filename=filepath)
          response = {'type': ServerResponseType.OPEN_FILE, 'error': error, 'filepath': filepath}
          await self.callManager.sendResponse(response)
          return
    except:
      await self.manageOpenFileError(filepath)
      # il8n: {filename}
      error = _('file.open.error.cannotOpen').format(filename=filepath)
      response = {'type': ServerResponseType.OPEN_FILE, 'error': error, 'filepath': filepath}
      await self.callManager.sendResponse(response)
      return
    response = {'type': ServerResponseType.OPEN_FILE, 'fileData': data, 'filepath': filepath}
    await self.callManager.sendResponse(response)

    self.cacheManager.addRecentFile(filepath)
    await self.sendRecentFiles()

  async def manageOpenFileError(self, filepath: str) -> None:
    didRemove = self.cacheManager.removeRecentFile(filepath)
    if didRemove:
      await self.sendRecentFiles()

  async def saveFile(self, data: Any) -> None:
    filepath = None
    if 'filepath' in data:
      filepath = data['filepath']
    if filepath is None:
      window = getTkinterWindow()
      # il8n: Name of the json files seen in the save dialog.
      filetypes = [(_('file.save.dialog.jsonFilename'), '*.json'), (_('file.save.dialog.otherFilename'), '*.*')]
      fileInfo = asksaveasfile(parent=window, filetypes=filetypes, defaultextension='.json', title=_('file.save.dialog.title'),
          initialfile=_('file.save.defaultFilename'))
      window.destroy()
      if fileInfo is None:
        return
      filepath = fileInfo.name

    try:
      with open(filepath, 'w') as file:
        json.dump(data['fileData'], file)
    except:
      # il8n: {filename}
      error = _('file.open.error.cannotSave').format(filename=filepath)
      response = {'type': ServerResponseType.SAVE_FILE, 'error': error}
      await self.callManager.sendResponse(response)
      return

    response = {'type': ServerResponseType.SAVE_FILE, 'filepath': filepath}
    await self.callManager.sendResponse(response)
    self.cacheManager.addRecentFile(filepath)
    await self.sendRecentFiles()

  def openFileInBrowser(self, data: Any) -> None:
    show_in_file_manager(os.path.abspath(data['filepath']))
