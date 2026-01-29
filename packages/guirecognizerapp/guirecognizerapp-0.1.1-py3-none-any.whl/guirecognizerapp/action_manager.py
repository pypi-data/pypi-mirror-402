import asyncio
import base64
import logging
from io import BytesIO
from time import perf_counter
from typing import TYPE_CHECKING, Any, assert_never

from guirecognizer import (ColorMapPreprocessor, GrayscalePreprocessor,
                           PreprocessingType, Recognizer, ResizePreprocessor,
                           ThresholdPreprocessor)
from guirecognizer.types import AreaCoord
from PIL import Image

from guirecognizerapp.server_client_interface import ServerResponseType

if TYPE_CHECKING:
  from guirecognizerapp.call_manager import CallManager
  from guirecognizerapp.process_manager import ProcessManager
  from guirecognizerapp.settings_manager import SettingsManager

logger = logging.getLogger(__name__)

class ActionManager:
  def __init__(self, callManager: 'CallManager', processManager: 'ProcessManager', settingsManager: 'SettingsManager') -> None:
    self.callManager = callManager
    self.processManager = processManager
    self.settingsManager = settingsManager
    self.callId = None

  async def getImageHash(self, data: Any) -> None:
    if 'coord' in data:
      assert self.callManager.screenshotManager.screenshot is not None
      area = Recognizer.getAreaFromScreenshot(self.callManager.screenshotManager.screenshot, data['coord'])
      hash = Recognizer.getImageHash(area)
    else:
      image = Image.open(BytesIO(base64.b64decode(data['image'])))
      hash = Recognizer.getImageHash(image)
    response = {'type': ServerResponseType.GET_IMAGE_HASH, 'hash': hash, 'key': data['key']}
    await self.callManager.sendResponse(response)

  async def getImageHashDifference(self, data: Any) -> None:
    hashReference = data['hashReference']
    if not Recognizer.isImageHashDataValid(hashReference):
      # il8n: {hash}
      error = _('action.imageHashReference.error').format(hash=hashReference)
      response = {'type': ServerResponseType.GET_IMAGE_HASH_DIFFERENCE, 'error': error, 'key': data['key']}
      await self.callManager.sendResponse(response)
      return
    hash = data['hash']
    difference = Recognizer.getImageHashDifference(hash, hashReference)
    response = {'type': ServerResponseType.GET_IMAGE_HASH_DIFFERENCE, 'difference': difference, 'key': data['key']}
    await self.callManager.sendResponse(response)

  async def isImageHashValid(self, data: Any) -> None:
    isValid = Recognizer.isImageHashDataValid(data['hash'])
    response = {'type': ServerResponseType.IS_IMAGE_HASH_VALID, 'isValid': isValid, 'key': data['key']}
    await self.callManager.sendResponse(response)

  def findImage(self, data: Any) -> None:
    image = Image.open(BytesIO(base64.b64decode(data['image'])))
    if self.processManager.isWaitingForAnExecute() and self.callId is not None:
      self.processManager.close()
    findImageInfo = data['findImageInfo']
    if findImageInfo['resizeInterval']['min'] is not None and findImageInfo['resizeInterval']['max'] is not None:
      resizeInterval = (findImageInfo['resizeInterval']['min'], findImageInfo['resizeInterval']['max'])
    else:
      resizeInterval = None
    self.callId = self.processManager.executeFindImage(data['coord'], image, findImageInfo['imageToFind']['data'], findImageInfo['threshold'], findImageInfo['maxNbResults'],
        resizeInterval, lambda result, elapsedTime : asyncio.run(self.endFindImage(data['key'], result, elapsedTime)))

  async def endFindImage(self, key: str, result: list[AreaCoord], elapsedTime: float | None) -> None:
    self.callId = None
    response = {'type': ServerResponseType.FIND_IMAGE, 'foundImages': result, 'elapsedTime': elapsedTime, 'key': key}
    await self.callManager.sendResponse(response)

  def getText(self, data: Any) -> None:
    image = Image.open(BytesIO(base64.b64decode(data['image'])))
    if self.processManager.isWaitingForAnExecute() and self.callId is not None:
      self.processManager.close()
    self.callId = self.processManager.executeGetText(image, self.settingsManager.settingData,
        lambda result, elapsedTime, errorMessage : asyncio.run(self.endGetText(data['key'], result, elapsedTime, errorMessage)))

  async def endGetText(self, key: str, result: str | None, elapsedTime: float | None, errorMessage: str | None) -> None:
    self.callId = None
    if errorMessage:
      logger.error(errorMessage)
      response = {'type': ServerResponseType.GET_TEXT, 'error': _('action.getText.error'), 'key': key}
      await self.callManager.sendResponse(response)
      return
    response = {'type': ServerResponseType.GET_TEXT, 'text': result, 'elapsedTime': elapsedTime, 'key': key}
    await self.callManager.sendResponse(response)

  def getNumber(self, data: Any) -> None:
    image = Image.open(BytesIO(base64.b64decode(data['image'])))
    if self.processManager.isWaitingForAnExecute() and self.callId is not None:
      self.processManager.close()
    self.callId = self.processManager.executeGetNumber(image, self.settingsManager.settingData,
        lambda result, elapsedTime, errorMessage : asyncio.run(self.endGetNumber(data['key'], result, elapsedTime, errorMessage)))

  async def endGetNumber(self, key: str, result: float | None, elapsedTime: float | None, errorMessage: str | None) -> None:
    self.callId = None
    if errorMessage:
      logger.error(errorMessage)
      response = {'type': ServerResponseType.GET_NUMBER, 'error': _('action.getNumber.error'), 'key': key}
      await self.callManager.sendResponse(response)
      return
    response = {'type': ServerResponseType.GET_NUMBER, 'nb': result, 'elapsedTime': elapsedTime, 'key': key}
    await self.callManager.sendResponse(response)

  async def preprocessImage(self, data: Any) -> None:
    image = Image.open(BytesIO(base64.b64decode(data['image'])))
    totalElapsedTime = 0
    for operationData in data['operations']:
      image, elapsedTime = self.preprocessImageOnce(image, PreprocessingType(operationData['type']), operationData['params'])
      totalElapsedTime += elapsedTime

    buffered = BytesIO()
    image.save(buffered, format='PNG')
    newImageStr = base64.b64encode(buffered.getvalue()).decode('utf-8')
    response = {'type': ServerResponseType.PREPROCESS_IMAGE, 'image': newImageStr, 'width': image.width, 'height': image.height,
        'elapsedTime': totalElapsedTime, 'key': data['key']}
    await self.callManager.sendResponse(response)

  def preprocessImageOnce(self, image: Image.Image, preprocessingType: PreprocessingType, params) -> tuple[Image.Image, float]:
    match preprocessingType:
      case PreprocessingType.GRAYSCALE:
        preprocessor = GrayscalePreprocessor()
      case PreprocessingType.COLOR_MAP:
        preprocessor = ColorMapPreprocessor(**params)
      case PreprocessingType.THRESHOLD:
        preprocessor = ThresholdPreprocessor(**params)
      case PreprocessingType.RESIZE:
        preprocessor = ResizePreprocessor(**params)
      case _ as unreachable:
        assert_never(preprocessingType)
    start = perf_counter()
    newImage = preprocessor.process(image)
    elapsedTime = perf_counter() - start
    return newImage, elapsedTime
