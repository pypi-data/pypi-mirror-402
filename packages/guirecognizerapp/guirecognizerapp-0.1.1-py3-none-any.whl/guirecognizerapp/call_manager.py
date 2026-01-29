import asyncio
import json
from typing import Any

import keyboard
from fastapi import WebSocket

from guirecognizerapp.action_manager import ActionManager
from guirecognizerapp.cache_manager import CacheDataManager
from guirecognizerapp.file_manager import FileManager
from guirecognizerapp.process_manager import ProcessManager
from guirecognizerapp.screenshot_manager import ScreenshotManager
from guirecognizerapp.server_client_interface import ClientRequestType
from guirecognizerapp.settings_manager import SettingsManager


class CallManager:
  def __init__(self, appname: str, websocket: WebSocket):
    self.websocket = websocket
    self.processManager = ProcessManager()
    self.settingsManager = SettingsManager(appname, self, self.processManager)
    self.cacheManager = CacheDataManager(appname)
    self.actionManager = ActionManager(self, self.processManager, self.settingsManager)
    self.fileManager = FileManager(self, self.cacheManager)
    self.screenshotManager = ScreenshotManager(self, self.cacheManager, self.settingsManager)

    self.hotKeyTakeScreenshot = keyboard.add_hotkey('ctrl+alt+t', lambda: self.handleTakeScreenshotShortcut(), suppress=True)

  async def manageData(self, rawData: str) -> None:
    #try:
    data = json.loads(rawData)
    # TODO: manage error
    #except Exception:
    #  logging.error(traceback.format_exc())
    #  return
    match data['type']:
      case ClientRequestType.INIT:
        await self.initClient()
      case ClientRequestType.OPEN_FILE:
        if 'filepath' in data:
          await self.fileManager.openFile(data['filepath'])
        else:
          await self.fileManager.openFileFromDialog()
      case ClientRequestType.SAVE_FILE:
        await self.fileManager.saveFile(data)
      case ClientRequestType.CLEAR_FILE_HISTORY:
        await self.fileManager.clearRecentFiles()
      case ClientRequestType.TAKE_SCREENSHOT:
        await self.screenshotManager.takeScreenshot()
      case ClientRequestType.UPDATE_SCREENSHOT:
        self.screenshotManager.updateScreenshot(data['image'], data['doesClearLastImage'])
      case ClientRequestType.OPEN_SCREENSHOT:
        if 'filepath' in data:
          await self.screenshotManager.openScreenshot(data['filepath'])
        else:
          await self.screenshotManager.openScreenshotFromDialog()
      case ClientRequestType.SAVE_SCREENSHOT:
        await self.screenshotManager.saveScreenshot()
      case ClientRequestType.CLEAR_SCREENSHOT_HISTORY:
        await self.screenshotManager.clearRecentScreenshots()
      case ClientRequestType.SAVE_SETTINGS:
        await self.settingsManager.saveSettings(data)
      case ClientRequestType.OPEN_IN_FILE_BROWSER:
        self.fileManager.openFileInBrowser(data)
      case ClientRequestType.GET_FILEPATH:
        await self.settingsManager.getFilepath(data)
      case ClientRequestType.SEARCH_TESSERACT_CMD:
        self.settingsManager.searchTesseractCmd(data)
      case ClientRequestType.FIND_IMAGE:
        self.actionManager.findImage(data)
      case ClientRequestType.GET_IMAGE_HASH:
        await self.actionManager.getImageHash(data)
      case ClientRequestType.GET_IMAGE_HASH_DIFFERENCE:
        await self.actionManager.getImageHashDifference(data)
      case ClientRequestType.IS_IMAGE_HASH_VALID:
        await self.actionManager.isImageHashValid(data)
      case ClientRequestType.GET_TEXT:
        self.actionManager.getText(data)
      case ClientRequestType.GET_NUMBER:
        self.actionManager.getNumber(data)
      case ClientRequestType.PREPROCESS_IMAGE:
        await self.actionManager.preprocessImage(data)
      case _:
        # TODO: manage error
        pass

  async def sendResponse(self, data: dict[str, Any]) -> None:
    await self.websocket.send_text(json.dumps(data))

  async def initClient(self) -> None:
    await self.fileManager.initClient()
    await self.screenshotManager.initClient()
    await self.settingsManager.initClient()

  def handleTakeScreenshotShortcut(self) -> None:
    asyncio.run(self.screenshotManager.takeScreenshot())

  def remove(self) -> None:
    self.processManager.close()
    keyboard.remove_hotkey(self.hotKeyTakeScreenshot)
