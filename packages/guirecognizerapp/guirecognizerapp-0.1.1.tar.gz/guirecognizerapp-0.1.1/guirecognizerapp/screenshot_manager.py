import base64
import time
from io import BytesIO
from tkinter.filedialog import askopenfile, asksaveasfile
from typing import TYPE_CHECKING, Any

from PIL import Image, ImageGrab

from guirecognizerapp.screen_helper import getTkinterWindow
from guirecognizerapp.server_client_interface import ServerResponseType

if TYPE_CHECKING:
  from guirecognizerapp.cache_manager import CacheDataManager
  from guirecognizerapp.call_manager import CallManager
  from guirecognizerapp.settings_manager import SettingsManager

class ScreenshotManager:
  def __init__(self, callManager: 'CallManager', cacheManager: 'CacheDataManager', settingsManager: 'SettingsManager') -> None:
    self.callManager = callManager
    self.cacheManager = cacheManager
    self.settingsManager = settingsManager
    self.screenshot = None

  def getScreenshot(self) -> Image.Image:
    self.screenshot = ImageGrab.grab(all_screens=self.settingsManager.settingData['allScreens'])
    return self.screenshot

  async def takeScreenshot(self) -> None:
    self.screenshot = self.getScreenshot()
    self.cacheManager.clearLastImage()
    await self.sendNewScreenshot(True)

  def updateScreenshot(self, image: str, doesClearLastImage: bool) -> None:
    self.screenshot = Image.open(BytesIO(base64.b64decode(image)))
    if doesClearLastImage:
      self.cacheManager.clearLastImage()

  async def sendNewScreenshot(self, doesSelectScreenshotTab: bool, filepath: str | None=None) -> None:
    assert self.screenshot is not None
    buffered = BytesIO()
    self.screenshot.save(buffered, format='PNG')
    imageStr = base64.b64encode(buffered.getvalue()).decode('utf-8')
    response = {'type': ServerResponseType.NEW_SCREENSHOT, 'image': imageStr, 'width': self.screenshot.width,
        'height': self.screenshot.height, 'doesSelectScreenshotTab': doesSelectScreenshotTab}
    if filepath:
      response['filepath'] = filepath
    await self.callManager.sendResponse(response)

  async def openScreenshotFromDialog(self) -> None:
    window = getTkinterWindow()
    # Since we want to open a screenshot, searching among png files only by default is appropriate.
    # il8n: Name of the png files seen in the open dialog.
    filetypes = [(_('screenshot.open.dialog.pngFilename'), '*.png'), (_('screenshot.open.dialog.otherFilename'), '*.*')]
    fileInfo = askopenfile(parent=window, filetypes=filetypes, title=_('screenshot.open.dialog.title'))
    window.destroy()
    if fileInfo is None:
      return
    await self.openScreenshot(fileInfo.name)

  async def openScreenshot(self, filepath: str) -> None:
    screenshot = self.tryOpenScreenshot(filepath)
    if screenshot is None:
      # il8n: {filename}
      error = _('screenshot.open.error').format(filename=filepath)
      response = {'type': ServerResponseType.NEW_SCREENSHOT, 'error': error}
      await self.callManager.sendResponse(response)

      didRemove = self.cacheManager.removeRecentImage(filepath)
      if didRemove:
        await self.sendRecentScreenshots()
      return

    self.screenshot = screenshot
    await self.sendNewScreenshot(True, filepath)

    self.cacheManager.addRecentImage(filepath)
    await self.sendRecentScreenshots()

  def tryOpenScreenshot(self, filepath: str) -> Image.Image | None:
    try:
      return Image.open(filepath)
    except:
      return None

  async def saveScreenshot(self) -> None:
    if self.screenshot is None:
      return
    window = getTkinterWindow()
    # il8n: Name of the png files seen in the save dialog.
    filetypes = [(_('screenshot.save.dialog.pngFilename'), '*.png'), (_('screenshot.save.dialog.otherFilename'), '*.*')]
    fileInfo = asksaveasfile(parent=window, filetypes=filetypes, defaultextension='.png', title=_('screenshot.save.dialog.title'),
        # il8n: {datetime}: datetime of the screenshot
        initialfile=_('screenshot.save.defaultFilename').format(datetime=time.strftime('%m-%d-%Y--%H-%M-%S')))
    window.destroy()
    if fileInfo is None:
      return
    try:
      self.screenshot.save(fileInfo.name, 'PNG')
    except:
      # il8n: {filename}
      error = _('screenshot.save.error').format(filename=fileInfo.name)
      response = {'type': ServerResponseType.NEW_SCREENSHOT, 'error': error}
      await self.callManager.sendResponse(response)
      return

    response = {'type': ServerResponseType.NEW_SCREENSHOT, 'filepath': fileInfo.name}
    await self.callManager.sendResponse(response)

    self.cacheManager.addRecentImage(fileInfo.name)
    await self.sendRecentScreenshots()

  async def initClient(self) -> None:
    await self.sendLastScreenshot()
    await self.sendRecentScreenshots()

  async def sendLastScreenshot(self) -> None:
    lastScreenshotFilepath = self.cacheManager.getLastImage()
    if lastScreenshotFilepath is None:
      return
    lastScreenshot = self.tryOpenScreenshot(lastScreenshotFilepath)
    if lastScreenshot is None:
      self.cacheManager.removeRecentImage(lastScreenshotFilepath)
      return
    self.screenshot = lastScreenshot
    await self.sendNewScreenshot(False, lastScreenshotFilepath)

  async def sendRecentScreenshots(self) -> None:
    response = {'type': ServerResponseType.RECENT_SCREENSHOTS, 'images': self.cacheManager.getRecentImages()}
    await self.callManager.sendResponse(response)

  async def clearRecentScreenshots(self) -> None:
    self.cacheManager.clearRecentImages()
    await self.sendRecentScreenshots()
