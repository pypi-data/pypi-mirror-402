import multiprocessing as mp
import os
import threading
import time
import traceback
from enum import Enum, auto, unique
from multiprocessing import shared_memory
from multiprocessing.connection import PipeConnection
from typing import Callable

import numpy as np
from guirecognizer import OcrType, Recognizer
from guirecognizer.types import AreaCoord
from PIL import Image


@unique
class ProcessType(Enum):
  FIND_IMAGE = auto()
  TEXT = auto()
  NUMBER = auto()
  FIND_TESSERACT_PATH = auto()

class ProcessManager:
  recognizer = None
  lastEasyOcrSettingData = None
  lastTesseractSettingData = None

  def __init__(self):
    self.callbackById = {}
    self.imageSharedMemoriesById = {}
    self.currentWaitingThreads = []
    self.lock = threading.Lock()
    self.process = None
    self.mainConnection = None
    self.processConnection = None
    self.restart()

  @classmethod
  def processWork(cls, processConnection: PipeConnection):
    while True:
      message = processConnection.recv()
      callId = message[0]
      match message[1]:
        case ProcessType.FIND_IMAGE:
          selectedArea, selectedAreaSharedMemory = cls.getSharedMemoryImage(*message[3:6])
          imageToFind, imageToFindSharedMemory = cls.getSharedMemoryImage(*message[6:9])
          startTime = time.time()
          coords = Recognizer.findImageCoordinatesWithImageToFindAsImage(message[2], selectedArea,
              imageToFind, message[9], message[10], message[11])
          elapsedTime = time.time() - startTime
          processConnection.send((callId, (coords, elapsedTime)))
          selectedAreaSharedMemory.close()
          imageToFindSharedMemory.close()
        case ProcessType.TEXT | ProcessType.NUMBER:
          cls.processOcrAction(processConnection, message)
        case ProcessType.FIND_TESSERACT_PATH:
          filepath = Recognizer.tryGetTesseractFilepath()
          processConnection.send((callId, (filepath,)))

  @classmethod
  def processOcrAction(cls, processConnection: PipeConnection, message):
    image, imageSharedMemory = cls.getSharedMemoryImage(*message[2:5])
    try:
      cls.prepareForOcr(message[5])
      startTime = time.time()
      assert cls.recognizer is not None
      match message[1]:
        case ProcessType.TEXT:
          result = cls.recognizer.getText(image)
        case ProcessType.NUMBER:
          result = cls.recognizer.getNumber(image)
      elapsedTime = time.time() - startTime
      errorMessage = None
    except:
      result = None
      elapsedTime = None
      errorMessage = traceback.format_exc()
    processConnection.send((message[0], (result, elapsedTime, errorMessage)))
    imageSharedMemory.close()

  @classmethod
  def prepareForOcr(cls, settingData) -> None:
    if cls.recognizer is None:
      cls.recognizer = Recognizer()
    ocrsInfo = settingData['ocrs']
    ocrOrder = [OcrType(ocrType) for ocrType in ocrsInfo['order'] if ocrsInfo['isActivated'][ocrType]]
    cls.recognizer.setOcrOrder(ocrOrder)
    cls.manageEasyOcrSettingData(settingData)
    cls.manageTesseractSettingData(settingData)

  @classmethod
  def manageEasyOcrSettingData(cls, settingData) -> None:
    assert cls.recognizer is not None
    if OcrType.EASY_OCR not in cls.recognizer.ocrOrder:
      return
    if cls.lastEasyOcrSettingData is not None and cls.lastEasyOcrSettingData['easyOcr']['lang'] == settingData['easyOcr']['lang']:
      return
    cls.recognizer.setEasyOcr(languages=settingData['easyOcr']['lang'])
    cls.lastEasyOcrSettingData = settingData

  @classmethod
  def manageTesseractSettingData(cls, settingData) -> None:
    assert cls.recognizer is not None
    if OcrType.TESSERACT not in cls.recognizer.ocrOrder:
      return
    if cls.lastTesseractSettingData is not None and cls.lastTesseractSettingData['tesseract']['cmd'] == settingData['tesseract']['cmd'] \
        and cls.lastTesseractSettingData['tesseract']['lang'] == settingData['tesseract']['lang'] \
        and cls.lastTesseractSettingData['tesseract']['textConfig'] == settingData['tesseract']['textConfig'] \
        and cls.lastTesseractSettingData['tesseract']['numberConfig'] == settingData['tesseract']['numberConfig']:
      return
    cls.recognizer.setTesseractOcr(tesseract_cmd=settingData['tesseract']['cmd'], lang=settingData['tesseract']['lang'],
        textConfig=settingData['tesseract']['textConfig'], numberConfig=settingData['tesseract']['numberConfig'])
    cls.lastTesseractSettingData = settingData

  @classmethod
  def getSharedMemoryImage(cls, sharedMemoryName, shape, dtype) -> tuple[Image.Image, shared_memory.SharedMemory]:
    imageSharedMemory = shared_memory.SharedMemory(name=sharedMemoryName)
    imageData = np.ndarray(shape, dtype=dtype, buffer=imageSharedMemory.buf)
    return Image.fromarray(imageData), imageSharedMemory

  @classmethod
  def threadWork(cls, mainConnection: PipeConnection, callbackById, imageSharedMemoriesById, currentWaitingThreads, lock) -> None:
    try:
      callId, result = mainConnection.recv()
    except EOFError:
      return
    with lock:
      if callId in currentWaitingThreads:
        currentWaitingThreads.remove(callId)
      if callId in callbackById:
        callback = callbackById.pop(callId)
        callback(*result)
      cls.deleteImageSharedMemories(callId, imageSharedMemoriesById)

  @classmethod
  def deleteImageSharedMemories(cls, callId: int, imageSharedMemoriesById) -> None:
    if callId not in imageSharedMemoriesById:
      return
    imageSharedMemories = imageSharedMemoriesById.pop(callId)
    for imageSharedMemory in imageSharedMemories:
      imageSharedMemory.close()
      imageSharedMemory.unlink()

  def restart(self) -> None:
    self.close()
    self.mainConnection, self.processConnection = mp.Pipe()
    self.isClosed = False
    self.callId = 0

  def executeFindImage(self, areaCoord: tuple[int, int, int, int], selectedArea: Image.Image, imageToFindValue: str, threshold: int,
      maxResults: int, resizeInterval: tuple[int, int] | None, callback: Callable[[list[AreaCoord], float | None], None]) -> int:
    imageToFind = Recognizer.getImageToFindFromData(imageToFindValue)
    return self.execute((ProcessType.FIND_IMAGE, areaCoord, selectedArea, imageToFind,
        threshold, maxResults, resizeInterval), callback)

  def executeGetText(self, area: Image.Image, settingData, callback: Callable[[str | None, float | None, str | None], None]) -> int:
    return self.execute((ProcessType.TEXT, area, settingData), callback)

  def executeGetNumber(self, area: Image.Image, settingData, callback: Callable[[float | None, float | None, str | None], None]) -> int:
    return self.execute((ProcessType.NUMBER, area, settingData), callback)

  def executeFindTesseractPath(self, callback: Callable[[str | None], None]) -> int:
    return self.execute((ProcessType.FIND_TESSERACT_PATH,), callback)

  def execute(self, processArgs, callback) -> int:
    if self.isClosed:
      self.restart()
    if self.process is None:
      self.process = mp.Process(target=self.processWork, args=(self.processConnection,))
      self.process.start()

    callId = self.callId
    self.callId += 1
    callArgs = [callId]
    imageSharedMemories = []
    for arg in processArgs:
      if isinstance(arg, Image.Image):
        imageData = np.asarray(arg)
        imageSharedMemory = shared_memory.SharedMemory(create=True, size=imageData.nbytes)
        imageDataCopy = np.ndarray(imageData.shape, dtype=imageData.dtype, buffer=imageSharedMemory.buf)
        imageDataCopy[:] = imageData[:]
        callArgs.extend((imageSharedMemory.name, imageDataCopy.shape, imageDataCopy.dtype))
        imageSharedMemories.append(imageSharedMemory)
      else:
        callArgs.append(arg)
    with self.lock:
      self.callbackById[callId] = callback
      self.imageSharedMemoriesById[callId] = imageSharedMemories
      self.currentWaitingThreads.append(callId)
    assert self.mainConnection is not None
    self.mainConnection.send(callArgs)

    thread = threading.Thread(target=self.threadWork, args=(self.mainConnection, self.callbackById,
        self.imageSharedMemoriesById, self.currentWaitingThreads, self.lock))
    thread.start()
    return callId

  def cancel(self, callId: int) -> None:
    with self.lock:
      if callId in self.callbackById:
        self.callbackById.pop(callId)

  def isWaitingForAnExecute(self) -> bool:
    with self.lock:
      return len(self.currentWaitingThreads) > 0

  def close(self) -> None:
    self.isClosed = True
    if self.process is not None:
      self.process.terminate()
      self.process = None
    if self.mainConnection is not None:
      self.mainConnection.close()
      self.mainConnection = None
    for callId in list(self.callbackById.keys()):
      self.cancel(callId)
    for callId in list(self.imageSharedMemoriesById.keys()):
      self.deleteImageSharedMemories(callId, self.imageSharedMemoriesById)
    self.currentWaitingThreads.clear()
