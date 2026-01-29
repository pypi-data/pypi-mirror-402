import asyncio
import importlib.util
import json
import os
from enum import Enum, unique
from pathlib import Path
from tkinter.filedialog import askopenfile
from typing import TYPE_CHECKING, Any, TypeGuard

import platformdirs
from guirecognizer import OcrType, Recognizer

from guirecognizerapp.screen_helper import getTkinterWindow
from guirecognizerapp.server_client_interface import ServerResponseType

if TYPE_CHECKING:
  from guirecognizerapp.call_manager import CallManager
  from guirecognizerapp.process_manager import ProcessManager

@unique
class ContextLevel(Enum):
  """
  Context level for saving screenshots.
  """
  NONE = 'none'
  BORDERS_ONLY = 'bordersOnly'
  ALL = 'all'

class SettingsManager():
  def __init__(self, appname: str, callManager: 'CallManager', processManager: 'ProcessManager') -> None:
    self.appname = appname
    self.callManager = callManager
    self.processManager = processManager
    self.settingDirectory = platformdirs.user_config_dir(self.appname)
    self.settingFilepath = os.path.join(self.settingDirectory, 'settings.json')
    self.callId = None
    self.settingData = self.getDefaultSettings()

  @classmethod
  def isContextLevelDataValid(cls, contextLevelData: Any) -> TypeGuard[dict[str, bool]]:
    contextLevelValues = [contextLevel.value for contextLevel in ContextLevel]
    return isinstance(contextLevelData, str) and contextLevelData in contextLevelValues

  @classmethod
  def isEasyOcrLanguagesDataValid(cls, languagesData: Any) -> TypeGuard[tuple[str] | list[str]]:
    return isinstance(languagesData, (tuple, list)) and len(languagesData) > 0 and all([isinstance(lang, str) and len(lang) > 0 for lang in languagesData])

  @classmethod
  def isOcrActivatedDataValid(cls, isActivatedData: Any) -> TypeGuard[dict[str, bool]]:
    ocrTypeValues = [ocrType.value for ocrType in OcrType]
    return isinstance(isActivatedData, dict) and len(isActivatedData) == len(OcrType) and \
        all(isinstance(ocrType, str) and ocrType in ocrTypeValues and isinstance(isActivated, bool) for ocrType, isActivated in isActivatedData.items())

  async def initClient(self) -> None:
    self.settingData = self.importSettings()
    response = {'type': ServerResponseType.UPDATE_SETTINGS, 'settings': self.settingData}
    await self.callManager.sendResponse(response)

  def getDefaultSettings(self) -> dict[str, Any]:
    isTesseractInstalled = importlib.util.find_spec('pytesseract') is not None
    isEasyOcrInstalled = importlib.util.find_spec('easyocr') is not None
    settingsData: dict[str, Any] = {
      'allScreens': False,
      'contextLevel': ContextLevel.BORDERS_ONLY.value,
      'tesseract': {
        'cmd': '',
        'textConfig': '--psm 7 --oem 3',
        'numberConfig': '--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789oOQiIl|',
        'lang': 'eng',
        'isInstalled': isTesseractInstalled
      },
      'easyOcr': {
        'lang': ['en'],
        'isInstalled': isEasyOcrInstalled
      },
      'ocrs': {
        'order': [OcrType.EASY_OCR.value, OcrType.TESSERACT.value],
        'isActivated': {OcrType.EASY_OCR.value: isEasyOcrInstalled, OcrType.TESSERACT.value: isTesseractInstalled}
      }
    }
    return settingsData

  def importSettings(self) -> dict[str, Any]:
    settingsData = self.getDefaultSettings()
    try:
      with open(self.settingFilepath, 'r') as file:
        data = json.load(file)
    except:
      data = {}
    if 'allScreens' in data and isinstance(data['allScreens'], bool):
      settingsData['allScreens'] = data['allScreens']
    if 'contextLevel' in data and self.isContextLevelDataValid(data['contextLevel']):
      settingsData['contextLevel'] = data['contextLevel']
    if 'tesseract' in data and isinstance(data['tesseract'], dict):
      tesseractInfo = data['tesseract']
      if 'cmd' in tesseractInfo and isinstance(tesseractInfo['cmd'], str):
        settingsData['tesseract']['cmd'] = tesseractInfo['cmd']
      if 'textConfig' in tesseractInfo and isinstance(tesseractInfo['textConfig'], str):
        settingsData['tesseract']['textConfig'] = tesseractInfo['textConfig']
      if 'numberConfig' in tesseractInfo and isinstance(tesseractInfo['numberConfig'], str):
        settingsData['tesseract']['numberConfig'] = tesseractInfo['numberConfig']
      if 'lang' in tesseractInfo and isinstance(tesseractInfo['lang'], str):
        settingsData['tesseract']['lang'] = tesseractInfo['lang']
    if 'easyOcr' in data and isinstance(data['easyOcr'], dict):
      easyOcrInfo = data['easyOcr']
      if 'lang' in easyOcrInfo and self.isEasyOcrLanguagesDataValid(easyOcrInfo['lang']):
        settingsData['easyOcr']['lang'] = easyOcrInfo['lang']
    if 'ocrs' in data and isinstance(data['ocrs'], dict):
      ocrsInfo = data['ocrs']
      if 'order' in ocrsInfo and Recognizer.isOcrOrderDataValid(ocrsInfo['order']) and len(ocrsInfo['order']) == len(OcrType):
        settingsData['ocrs']['order'] = ocrsInfo['order']
      if 'isActivated' in ocrsInfo and self.isOcrActivatedDataValid(ocrsInfo['isActivated']):
        settingsData['ocrs']['isActivated'] = ocrsInfo['isActivated']
    return settingsData

  async def saveSettings(self, data: Any) -> None:
    self.settingData = data['settings']
    try:
      Path(self.settingDirectory).mkdir(parents=True, exist_ok=True)
      with open(self.settingFilepath, 'w') as file:
        json.dump(self.settingData, file)
    except:
      pass

  async def getFilepath(self, data: Any) -> None:
    window = getTkinterWindow()
    filetypes = [(_('settings.getFilepath.dialog.exeFilename'), '*.exe'), (_('settings.getFilepath.dialog.otherFilename'), '*.*')]
    fileInfo = askopenfile(parent=window, filetypes=filetypes, title=_('settings.getFilepath.dialog.title'))
    window.destroy()
    if fileInfo is None:
      return
    response = {'type': ServerResponseType.GET_FILEPATH, 'filepath': fileInfo.name, 'key': data['key']}
    await self.callManager.sendResponse(response)

  def searchTesseractCmd(self, data: Any) -> None:
    if self.processManager.isWaitingForAnExecute() and self.callId is not None:
      self.processManager.close()
    if 'doesAbort' in data and data['doesAbort']:
      return
    self.callId = self.processManager.executeFindTesseractPath(lambda filepath : asyncio.run(self.endSearchTesseractCmd(data['key'], filepath)))

  async def endSearchTesseractCmd(self, key: str, filepath: str | None) -> None:
    self.callId = None
    if filepath is None:
      error = _('settings.searchTesseractCmd.notFound')
      response = {'type': ServerResponseType.SEARCH_TESSERACT_CMD, 'error': error, 'key': key}
      await self.callManager.sendResponse(response)
      return
    response = {'type': ServerResponseType.SEARCH_TESSERACT_CMD, 'cmd': filepath, 'key': key}
    await self.callManager.sendResponse(response)
