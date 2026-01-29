import copy
import os
import shutil
import tempfile
import unittest
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from guirecognizer import (ColorMapMethod, OcrType, PreprocessingType,
                           ResizeMethod, ThresholdMethod, ThresholdType)

from guirecognizerapp.server import createApp
from guirecognizerapp.server_client_interface import (ClientRequestType,
                                                      ServerResponseType)
from guirecognizerapp.settings_manager import ContextLevel
from tests.test_utility import LoggedTestCase, timeout

if TYPE_CHECKING:
  from starlette.testclient import WebSocketTestSession

# Tkinter window creation is mocked so as to avoid a multithreading issue.
# Function handleTakeScreenshotShortcut is mocked so that the global keyboard shortcut to take screenshot does not interfere with the tests.

@contextmanager
def getWebsocketWithAppMocks(client: TestClient, openFilepath: str | None=None, saveFilepath: str | None=None):
    with tempfile.TemporaryDirectory() as directory, patch('platformdirs.user_config_dir') as configMock, patch('platformdirs.user_cache_dir') as cacheMock, \
        patch('tkinter.Tk'), patch('guirecognizerapp.call_manager.CallManager.handleTakeScreenshotShortcut'), \
        patch('guirecognizerapp.file_manager.askopenfile') as openFileMock1, \
        patch('guirecognizerapp.screenshot_manager.askopenfile') as openFileMock2, \
        patch('guirecognizerapp.settings_manager.askopenfile') as openFileMock3, \
        patch('guirecognizerapp.file_manager.asksaveasfile') as saveFileMock1, \
        patch('guirecognizerapp.screenshot_manager.asksaveasfile') as saveFileMock2:
      configMock.return_value = directory
      cacheMock.return_value = directory

      openFileMocks = [openFileMock1, openFileMock2, openFileMock3]
      if openFilepath is None:
        for openFileMock in openFileMocks:
          openFileMock.return_value = None
      else:
        mock = Mock()
        mock.name = openFilepath
        for openFileMock in openFileMocks:
          openFileMock.return_value = mock

      saveFileMocks = [saveFileMock1, saveFileMock2]
      if saveFilepath is None:
        for saveFileMock in saveFileMocks:
          saveFileMock.return_value = None
      else:
        mock = Mock()
        mock.name = saveFilepath
        for saveFileMock in saveFileMocks:
          saveFileMock.return_value = mock

      with client.websocket_connect('/ws') as websocket:
        yield websocket

class ClientRequestTestCase(LoggedTestCase):
  defaultSettings = {
    'allScreens': False,
    'contextLevel': ContextLevel.BORDERS_ONLY.value,
    'tesseract': {
      'cmd': '',
      'textConfig': '--psm 7 --oem 3',
      'numberConfig': '--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789oOQiIl|',
      'lang': 'eng',
      'isInstalled': True
    },
    'easyOcr': {
        'lang': ['en'],
        'isInstalled': True
    },
    'ocrs': {'order': [OcrType.EASY_OCR.value, OcrType.TESSERACT.value], 'isActivated': {OcrType.EASY_OCR.value: True, OcrType.TESSERACT.value: True}}
  }

  def setUp(self):
    super().setUp()
    self.client = TestClient(createApp())

  @timeout(1)
  def receiveDataOnTimeout(self, websocket: 'WebSocketTestSession'):
    websocket.receive_json()

  def assertNoDataReceived(self, websocket: 'WebSocketTestSession'):
    """
    Assert the websocket does not receive any data for 1 second.

    Do not try to receive any data again after calling this. The next data would most likely be lost.
    """
    with self.assertRaises(TimeoutError):
      self.receiveDataOnTimeout(websocket)

  def assertResponseType(self, data: Any, responseType: ServerResponseType):
    self.assertIn('type', data)
    self.assertEqual(data['type'], responseType)

  def assertNewScreenshot(self, data: Any, width: int | None=None, height: int | None=None, filepath: str | None=None):
    self.assertResponseType(data, ServerResponseType.NEW_SCREENSHOT)
    self.assertIn('image', data)
    self.assertEqual(type(data['image']), str)
    self.assertIn('width', data)
    self.assertEqual(type(data['width']), int)
    if width is None:
      self.assertGreater(data['width'], 0)
    else:
      self.assertEqual(data['width'], width)
    self.assertEqual(type(data['height']), int)
    self.assertIn('height', data)
    if height is None:
      self.assertGreater(data['height'], 0)
    else:
      self.assertEqual(data['height'], height)

    if filepath is not None:
      self.assertNewScreenshotFilepath(data, filepath)

  def assertNewScreenshotFilepath(self, data: Any, filepath: str):
    self.assertResponseType(data, ServerResponseType.NEW_SCREENSHOT)
    self.assertIn('filepath', data)
    self.assertEqual(data['filepath'], filepath)

  def assertHasError(self, data: Any, responseType: ServerResponseType):
    self.assertResponseType(data, responseType)
    self.assertIn('error', data)
    self.assertEqual(type(data['error']), str)

  def assertRecentScreenshots(self, data: Any, images: list[str]):
    self.assertResponseType(data, ServerResponseType.RECENT_SCREENSHOTS)
    self.assertIn('images', data)
    self.assertEqual(type(data['images']), list)
    self.assertEqual(data['images'], images)

  def assertRecentFiles(self, data: Any, files: list[str]):
    self.assertResponseType(data, ServerResponseType.RECENT_FILES)
    self.assertIn('files', data)
    self.assertEqual(type(data['files']), list)
    self.assertEqual(data['files'], files)

  def assertSettings(self, data: Any, settings: dict=defaultSettings):
    self.assertResponseType(data, ServerResponseType.UPDATE_SETTINGS)
    self.assertIn('settings', data)
    self.assertEqual(type(data['settings']), dict)

    self.assertIn('easyOcr', data['settings'])
    self.assertEqual(type(data['settings']['easyOcr']), dict)

    self.assertIn('tesseract', data['settings'])
    self.assertEqual(type(data['settings']['tesseract']), dict)

    self.assertIn('ocrs', data['settings'])
    self.assertEqual(type(data['settings']['ocrs']), dict)
    self.assertIn('isActivated', data['settings']['ocrs'])
    self.assertEqual(type(data['settings']['ocrs']['isActivated']), dict)

    # The values for isInstalled and isActivated are ignored during the tests so that installing tesseract is required as little as possible.
    data['settings']['easyOcr']['isInstalled'] = True
    settings['easyOcr']['isInstalled'] = True
    data['settings']['tesseract']['isInstalled'] = True
    settings['tesseract']['isInstalled'] = True
    data['settings']['ocrs']['isActivated'][OcrType.EASY_OCR.value] = True
    settings['ocrs']['isActivated'][OcrType.EASY_OCR.value] = True
    data['settings']['ocrs']['isActivated'][OcrType.TESSERACT.value] = True
    settings['ocrs']['isActivated'][OcrType.TESSERACT.value] = True
    self.assertEqual(data['settings'], settings)

  def openValidScreenshotThatBecomesInvalid(self) -> str:
    """
    After this is called the opened screenshot no longer exists but is still referenced in the recent screenshots.

    :return: deleted opened screenshot filepath
    """
    with tempfile.TemporaryDirectory() as directory:
      filepath = 'tests/data/img/img1.png'
      openFilepath = os.path.join(directory, 'img1.png')
      shutil.copyfile(filepath, openFilepath)
      with self.client.websocket_connect('/ws') as websocket:
        websocket.send_json({'type': ClientRequestType.OPEN_SCREENSHOT, 'filepath': openFilepath})
        data = websocket.receive_json()
        self.assertNewScreenshot(data, width=40, height=40)
        data = websocket.receive_json()
        self.assertRecentScreenshots(data, [openFilepath])
    return openFilepath

class TestClientInit(ClientRequestTestCase):
  @timeout()
  def test_connectToWebsocket(self):
    with getWebsocketWithAppMocks(self.client):
      pass

  @timeout()
  def test_init(self):
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.INIT})
      data = websocket.receive_json()
      self.assertRecentFiles(data, [])
      data = websocket.receive_json()
      self.assertRecentScreenshots(data, [])
      data = websocket.receive_json()
      self.assertSettings(data)

  @timeout()
  def test_init_lastScreenshot(self):
    filepath = 'tests/data/img/img1.png'
    with getWebsocketWithAppMocks(self.client, openFilepath=filepath) as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_SCREENSHOT})
      data = websocket.receive_json()
      self.assertNewScreenshot(data, width=40, height=40)
      data = websocket.receive_json()
      self.assertRecentScreenshots(data, [filepath])

      websocket.send_json({'type': ClientRequestType.INIT})
      data = websocket.receive_json()
      self.assertRecentFiles(data, [])
      data = websocket.receive_json()
      self.assertNewScreenshot(data, width=40, height=40, filepath=filepath)
      data = websocket.receive_json()
      self.assertRecentScreenshots(data, [filepath])
      data = websocket.receive_json()
      self.assertSettings(data)

  @timeout()
  def test_init_invalidLastScreenshot(self):
    with tempfile.TemporaryDirectory() as configDirectory, patch('platformdirs.user_config_dir') as configMock, patch('platformdirs.user_cache_dir') as cacheMock, \
        patch('tkinter.Tk'):
      configMock.return_value = configDirectory
      cacheMock.return_value = configDirectory

      self.openValidScreenshotThatBecomesInvalid()
      with self.client.websocket_connect('/ws') as websocket:
        websocket.send_json({'type': ClientRequestType.INIT})
        data = websocket.receive_json()
        self.assertRecentFiles(data, [])
        data = websocket.receive_json()
        self.assertRecentScreenshots(data, [])
        data = websocket.receive_json()
        self.assertSettings(data)

class TestFile(ClientRequestTestCase):
  def assertOpenFile(self, data: Any):
    self.assertResponseType(data, ServerResponseType.OPEN_FILE)
    self.assertIn('fileData', data)
    self.assertEqual(type(data['fileData']), dict)
    self.assertIn('filepath', data)
    self.assertEqual(type(data['filepath']), str)

  def assertSaveFile(self, data: Any, filepath: str):
    self.assertResponseType(data, ServerResponseType.SAVE_FILE)
    self.assertIn('filepath', data)
    self.assertEqual(type(data['filepath']), str)
    self.assertEqual(data['filepath'], filepath)

  def openValidFileThatBecomesInvalid(self) -> str:
    """
    After this is called the opened file no longer exists but is still referenced in the recent files.

    :return: deleted opened file filepath
    """
    with tempfile.TemporaryDirectory() as directory:
      filepath = 'tests/data/json/config1.json'
      openFilepath = os.path.join(directory, 'config1.png')
      shutil.copyfile(filepath, openFilepath)
      with self.client.websocket_connect('/ws') as websocket:
        websocket.send_json({'type': ClientRequestType.OPEN_FILE, 'filepath': openFilepath})
        data = websocket.receive_json()
        self.assertOpenFile(data)
        data = websocket.receive_json()
        self.assertRecentFiles(data, [openFilepath])
    return openFilepath

  @timeout()
  def test_openFile_nonexistentFile(self):
    with getWebsocketWithAppMocks(self.client, openFilepath='invalid') as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_FILE})
      data = websocket.receive_json()
      self.assertHasError(data, ServerResponseType.OPEN_FILE)

  @timeout()
  def test_openFile_invalidFile(self):
    with getWebsocketWithAppMocks(self.client, openFilepath='tests/data/json/invalid.json') as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_FILE})
      data = websocket.receive_json()
      self.assertHasError(data, ServerResponseType.OPEN_FILE)

  @timeout()
  def test_openFile_cancel(self):
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_FILE})
      self.assertNoDataReceived(websocket)

  @timeout()
  def test_openFile_validFile(self):
    filepath = 'tests/data/json/config1.json'
    with getWebsocketWithAppMocks(self.client, openFilepath=filepath) as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_FILE})
      data = websocket.receive_json()
      self.assertOpenFile(data)
      data = websocket.receive_json()
      self.assertRecentFiles(data, [filepath])

  @timeout()
  def test_openFile_validFileGivingFilepath(self):
    filepath = 'tests/data/json/config1.json'
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_FILE, 'filepath': filepath})
      data = websocket.receive_json()
      self.assertOpenFile(data)
      data = websocket.receive_json()
      self.assertRecentFiles(data, [filepath])

  @timeout()
  def test_openFile_validFileThenDeleted(self):
    with tempfile.TemporaryDirectory() as configDirectory, patch('platformdirs.user_config_dir') as configMock, patch('platformdirs.user_cache_dir') as cacheMock, \
        patch('tkinter.Tk'):
      configMock.return_value = configDirectory
      cacheMock.return_value = configDirectory

      openFilepath = self.openValidFileThatBecomesInvalid()
      with self.client.websocket_connect('/ws') as websocket:
        websocket.send_json({'type': ClientRequestType.OPEN_FILE, 'filepath': openFilepath})
        data = websocket.receive_json()
        self.assertRecentFiles(data, [])
        data = websocket.receive_json()
        self.assertHasError(data, ServerResponseType.OPEN_FILE)

  @timeout()
  def test_clearFileHistory(self):
    filepath = 'tests/data/json/config1.json'
    with getWebsocketWithAppMocks(self.client, openFilepath=filepath) as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_FILE})
      data = websocket.receive_json()
      self.assertOpenFile(data)
      data = websocket.receive_json()
      self.assertRecentFiles(data, [filepath])

      websocket.send_json({'type': ClientRequestType.CLEAR_FILE_HISTORY})
      data = websocket.receive_json()
      self.assertRecentFiles(data, [])

  @timeout()
  def test_saveFile_cancel(self):
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.SAVE_FILE, 'fileData': {'actions': [], 'borders': [0, 0, 39, 39]}})
      self.assertNoDataReceived(websocket)

  @timeout()
  def test_saveFile_invalidFile(self):
    with tempfile.TemporaryDirectory() as directory:
      with getWebsocketWithAppMocks(self.client, saveFilepath=directory) as websocket:
        websocket.send_json({'type': ClientRequestType.SAVE_FILE, 'fileData': {'actions': [], 'borders': [0, 0, 39, 39]}})
        data = websocket.receive_json()
        self.assertHasError(data, ServerResponseType.SAVE_FILE)

  @timeout()
  def test_saveFile_validFile(self):
    with tempfile.TemporaryDirectory() as directory:
      saveFilepath = os.path.join(directory, 'newConfig.png')
      with getWebsocketWithAppMocks(self.client, saveFilepath=saveFilepath) as websocket:
        websocket.send_json({'type': ClientRequestType.SAVE_FILE, 'fileData': {'actions': [], 'borders': [0, 0, 39, 39]}})
        data = websocket.receive_json()
        self.assertSaveFile(data, saveFilepath)
        data = websocket.receive_json()
        self.assertRecentFiles(data, [saveFilepath])

  @timeout()
  def test_saveFile_validFileGivingFilepath(self):
    with tempfile.TemporaryDirectory() as directory:
      saveFilepath = os.path.join(directory, 'newConfig.png')
      with getWebsocketWithAppMocks(self.client) as websocket:
        websocket.send_json({'type': ClientRequestType.SAVE_FILE, 'fileData': {'actions': [], 'borders': [0, 0, 39, 39]}, 'filepath': saveFilepath})
        data = websocket.receive_json()
        self.assertSaveFile(data, saveFilepath)
        data = websocket.receive_json()
        self.assertRecentFiles(data, [saveFilepath])

  @timeout()
  def test_openFileInBrowser(self):
    with patch('guirecognizerapp.file_manager.show_in_file_manager') as mock:
      with getWebsocketWithAppMocks(self.client) as websocket:
        websocket.send_json({'type': ClientRequestType.OPEN_IN_FILE_BROWSER, 'filepath': 'tests/data/json/config1.json'})
        self.assertNoDataReceived(websocket)
        mock.assert_called_once()

class TestScreenshot(ClientRequestTestCase):
  @timeout()
  def test_takeScreenshot(self):
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.TAKE_SCREENSHOT})
      data = websocket.receive_json()
      self.assertNewScreenshot(data)
      self.assertEqual(data['type'], ServerResponseType.NEW_SCREENSHOT)

  @timeout()
  def test_openScreenshot_nonexistentFile(self):
    with getWebsocketWithAppMocks(self.client, openFilepath='invalid') as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_SCREENSHOT})
      data = websocket.receive_json()
      self.assertHasError(data, ServerResponseType.NEW_SCREENSHOT)

  @timeout()
  def test_openScreenshot_cancel(self):
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_SCREENSHOT})
      self.assertNoDataReceived(websocket)

  @timeout()
  def test_openScreenshot_validFile(self):
    filepath = 'tests/data/img/img1.png'
    with getWebsocketWithAppMocks(self.client, openFilepath=filepath) as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_SCREENSHOT})
      data = websocket.receive_json()
      self.assertNewScreenshot(data, width=40, height=40)
      data = websocket.receive_json()
      self.assertRecentScreenshots(data, [filepath])

  @timeout()
  def test_openScreenshot_validFileGivingFilepath(self):
    filepath = 'tests/data/img/img1.png'
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_SCREENSHOT, 'filepath': filepath})
      data = websocket.receive_json()
      self.assertNewScreenshot(data, width=40, height=40)
      data = websocket.receive_json()
      self.assertRecentScreenshots(data, [filepath])

  @timeout()
  def test_openScreenshot_validFileThenDeleted(self):
    with tempfile.TemporaryDirectory() as configDirectory, patch('platformdirs.user_config_dir') as configMock, patch('platformdirs.user_cache_dir') as cacheMock, \
        patch('tkinter.Tk'):
      configMock.return_value = configDirectory
      cacheMock.return_value = configDirectory

      openFilepath = self.openValidScreenshotThatBecomesInvalid()
      with self.client.websocket_connect('/ws') as websocket:
        websocket.send_json({'type': ClientRequestType.OPEN_SCREENSHOT, 'filepath': openFilepath})
        data = websocket.receive_json()
        self.assertHasError(data, ServerResponseType.NEW_SCREENSHOT)
        data = websocket.receive_json()
        self.assertRecentScreenshots(data, [])

  @timeout()
  def test_saveScreenshot_noScreenshot(self):
    with tempfile.NamedTemporaryFile() as file:
      with getWebsocketWithAppMocks(self.client, saveFilepath=file.name) as websocket:
        websocket.send_json({'type': ClientRequestType.SAVE_SCREENSHOT})
        self.assertNoDataReceived(websocket)

  @timeout()
  def test_saveScreenshot_invalidFile(self):
    with tempfile.TemporaryDirectory() as directory:
      openFilepath = 'tests/data/img/img1.png'
      with getWebsocketWithAppMocks(self.client, openFilepath=openFilepath, saveFilepath=directory) as websocket:
        websocket.send_json({'type': ClientRequestType.OPEN_SCREENSHOT})
        websocket.receive_json()
        websocket.receive_json()

        websocket.send_json({'type': ClientRequestType.SAVE_SCREENSHOT})
        data = websocket.receive_json()
        self.assertHasError(data, ServerResponseType.NEW_SCREENSHOT)

  @timeout()
  def test_saveScreenshot_cancel(self):
    openFilepath = 'tests/data/img/img1.png'
    with getWebsocketWithAppMocks(self.client, openFilepath=openFilepath) as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_SCREENSHOT})
      websocket.receive_json()
      websocket.receive_json()

      websocket.send_json({'type': ClientRequestType.SAVE_SCREENSHOT})
      self.assertNoDataReceived(websocket)

  @timeout()
  def test_saveScreenshot_validFile(self):
    with tempfile.TemporaryDirectory() as directory:
      saveFilepath = os.path.join(directory, 'newImage.png')
      openFilepath = 'tests/data/img/img1.png'
      with getWebsocketWithAppMocks(self.client, saveFilepath=saveFilepath) as websocket:
        websocket.send_json({'type': ClientRequestType.OPEN_SCREENSHOT, 'filepath': openFilepath})
        websocket.receive_json()
        websocket.receive_json()

        websocket.send_json({'type': ClientRequestType.SAVE_SCREENSHOT})
        data = websocket.receive_json()
        self.assertNewScreenshotFilepath(data, saveFilepath)
        data = websocket.receive_json()
        self.assertRecentScreenshots(data, [saveFilepath, openFilepath])

  @timeout()
  def test_updateScreenshot(self):
    with tempfile.TemporaryDirectory() as directory:
      saveFilepath = os.path.join(directory, 'newScreenshot.png')
      with getWebsocketWithAppMocks(self.client, saveFilepath=saveFilepath) as websocket:
        websocket.send_json({'type': ClientRequestType.UPDATE_SCREENSHOT, 'key': 'key', 'doesClearLastImage': True,
            'image': 'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAG0lEQVR4nGOIi4v7//nz5/9Mz58/Zzh27BgDAGXBCvvJ+AJ6AAAAAElFTkSuQmCC'})

        websocket.send_json({'type': ClientRequestType.SAVE_SCREENSHOT})
        data = websocket.receive_json()
        self.assertNewScreenshotFilepath(data, saveFilepath)
        data = websocket.receive_json()
        self.assertRecentScreenshots(data, [saveFilepath])

        websocket.send_json({'type': ClientRequestType.INIT})
        data = websocket.receive_json()
        self.assertRecentFiles(data, [])
        data = websocket.receive_json()
        self.assertNewScreenshot(data, width=2, height=2, filepath=saveFilepath)
        data = websocket.receive_json()
        self.assertRecentScreenshots(data, [saveFilepath])

  @timeout()
  def test_updateScreenshot_noClearLastImage(self):
    filepath = 'tests/data/img/img1.png'
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_SCREENSHOT, 'filepath': filepath})
      websocket.receive_json()
      websocket.receive_json()

      websocket.send_json({'type': ClientRequestType.UPDATE_SCREENSHOT, 'key': 'key', 'doesClearLastImage': False,
          'image': 'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAG0lEQVR4nGOIi4v7//nz5/9Mz58/Zzh27BgDAGXBCvvJ+AJ6AAAAAElFTkSuQmCC'})

      websocket.send_json({'type': ClientRequestType.INIT})
      data = websocket.receive_json()
      self.assertRecentFiles(data, [])
      data = websocket.receive_json()
      self.assertNewScreenshot(data, width=40, height=40, filepath=filepath)
      data = websocket.receive_json()
      self.assertRecentScreenshots(data, [filepath])

  @timeout()
  def test_updateScreenshot_clearLastImage(self):
    filepath = 'tests/data/img/img1.png'
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_SCREENSHOT, 'filepath': filepath})
      websocket.receive_json()
      websocket.receive_json()

      websocket.send_json({'type': ClientRequestType.UPDATE_SCREENSHOT, 'key': 'key', 'doesClearLastImage': True,
          'image': 'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAG0lEQVR4nGOIi4v7//nz5/9Mz58/Zzh27BgDAGXBCvvJ+AJ6AAAAAElFTkSuQmCC'})

      websocket.send_json({'type': ClientRequestType.INIT})
      data = websocket.receive_json()
      self.assertRecentFiles(data, [])
      data = websocket.receive_json()
      self.assertRecentScreenshots(data, [filepath])

  @timeout()
  def test_clearScreenshotHistory(self):
    filepath = 'tests/data/img/img1.png'
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_SCREENSHOT, 'filepath': filepath})
      websocket.receive_json()
      data = websocket.receive_json()
      self.assertRecentScreenshots(data, [filepath])

      websocket.send_json({'type': ClientRequestType.CLEAR_SCREENSHOT_HISTORY})
      data = websocket.receive_json()
      self.assertRecentScreenshots(data, [])

class TestSettings(ClientRequestTestCase):
  def assertGetFilepath(self, data: Any, filepath: str):
    self.assertResponseType(data, ServerResponseType.GET_FILEPATH)
    self.assertIn('filepath', data)
    self.assertEqual(data['filepath'], filepath)
    self.assertIn('key', data)
    self.assertEqual(type(data['key']), str)

  @timeout()
  def test_getFilepath_cancel(self):
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.GET_FILEPATH, 'key': 'key'})
      self.assertNoDataReceived(websocket)

  @timeout()
  def test_getFilepath_validFile(self):
    filepath = 'tests/data/img/img1.png'
    with getWebsocketWithAppMocks(self.client, openFilepath=filepath) as websocket:
      websocket.send_json({'type': ClientRequestType.GET_FILEPATH, 'key': 'key'})
      data = websocket.receive_json()
      self.assertGetFilepath(data, filepath)

  @timeout()
  def test_importSettingsWithMissingValues(self):
    settings = {
      'tesseract': {},
      'easyOcr': {},
      'ocrs': {}
    }
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.SAVE_SETTINGS, 'settings': settings})
      websocket.send_json({'type': ClientRequestType.INIT})
      websocket.receive_json()
      websocket.receive_json()
      data = websocket.receive_json()
      self.assertSettings(data, self.defaultSettings)

    settings = {
      'tesseract': {'lang': 'fr'},
      'easyOcr': {},
      'ocrs': {'order': [OcrType.TESSERACT.value, OcrType.EASY_OCR.value]}
    }
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.SAVE_SETTINGS, 'settings': settings})
      websocket.send_json({'type': ClientRequestType.INIT})
      websocket.receive_json()
      websocket.receive_json()
      data = websocket.receive_json()
      newSettings = copy.deepcopy(self.defaultSettings)
      newSettings['tesseract']['lang'] = settings['tesseract']['lang']
      newSettings['ocrs']['order'] = settings['ocrs']['order']
      self.assertSettings(data, newSettings)

  @timeout()
  def test_saveSettings(self):
    settings = {
      'allScreens': True, 'contextLevel': ContextLevel.ALL.value,
      'tesseract': {'cmd': 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe', 'textConfig': '--psm 7 --oem 3', 'numberConfig': '--psm 8 --oem 3 -c tessedit_char_whitelist=0123oOQiIl|', 'lang': 'fr', 'isInstalled': True},
      'easyOcr': {'lang': ['en', 'fr'], 'isInstalled': True},
      'ocrs': {'order': [OcrType.EASY_OCR.value, OcrType.TESSERACT.value], 'isActivated': {OcrType.EASY_OCR.value: True, OcrType.TESSERACT.value: True}}
    }
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.SAVE_SETTINGS, 'settings': settings})
      websocket.send_json({'type': ClientRequestType.INIT})
      websocket.receive_json()
      websocket.receive_json()
      data = websocket.receive_json()
      self.assertSettings(data, settings)

  @timeout()
  def test_saveSettings_invalidSettingsFile(self):
    settings = {
      'allScreens': False,
      'tesseract': {'cmd': 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe', 'textConfig': '--psm 7 --oem 3', 'numberConfig': '--psm 8 --oem 3 -c tessedit_char_whitelist=0123oOQiIl|', 'lang': 'fr', 'isInstalled': True},
      'easyOcr': {'lang': ['en', 'fr'], 'isInstalled': True},
      'ocrs': {'order': [OcrType.EASY_OCR.value, OcrType.TESSERACT.value], 'isActivated': {OcrType.EASY_OCR.value: True, OcrType.TESSERACT.value: True}}
    }
    with tempfile.TemporaryDirectory() as directory:
      with patch('platformdirs.user_config_dir') as configMock, patch('platformdirs.user_cache_dir') as cacheMock, patch('tkinter.Tk'):
        # The settings filepath is made invalid from forbidden characters in its parent directory name.
        configMock.return_value = 'forbidden/*?<>:'
        cacheMock.return_value = directory
        with self.client.websocket_connect('/ws') as websocket:
          websocket.send_json({'type': ClientRequestType.SAVE_SETTINGS, 'settings': settings})
          websocket.send_json({'type': ClientRequestType.INIT})
          websocket.receive_json()
          websocket.receive_json()
          data = websocket.receive_json()
          self.assertSettings(data, self.defaultSettings)

class TestAction(ClientRequestTestCase):
  def assertGetImageHash(self, data: Any, hash: str):
    self.assertResponseType(data, ServerResponseType.GET_IMAGE_HASH)
    self.assertIn('hash', data)
    self.assertEqual(data['hash'], hash)
    self.assertIn('key', data)
    self.assertEqual(type(data['key']), str)

  def assertGetImageHashDifference(self, data: Any, difference: int):
    self.assertResponseType(data, ServerResponseType.GET_IMAGE_HASH_DIFFERENCE)
    self.assertIn('difference', data)
    self.assertEqual(data['difference'], difference)
    self.assertIn('key', data)
    self.assertEqual(type(data['key']), str)

  def assertIsImageHashValid(self, data: Any, isValid: bool):
    self.assertResponseType(data, ServerResponseType.IS_IMAGE_HASH_VALID)
    self.assertIn('isValid', data)
    self.assertEqual(data['isValid'], isValid)
    self.assertIn('key', data)
    self.assertEqual(type(data['key']), str)

  def assertPreprocessImage(self, data: Any, width: int, height: int):
    self.assertResponseType(data, ServerResponseType.PREPROCESS_IMAGE)
    self.assertIn('image', data)
    self.assertEqual(type(data['image']), str)
    self.assertIn('width', data)
    self.assertEqual(data['width'], width)
    self.assertIn('height', data)
    self.assertEqual(data['height'], height)
    self.assertIn('elapsedTime', data)
    self.assertEqual(type(data['elapsedTime']), float)
    self.assertIn('key', data)
    self.assertEqual(type(data['key']), str)

  @timeout()
  def test_getImageHash_fromCoord(self):
    filepath = 'tests/data/img/img1.png'
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.OPEN_SCREENSHOT, 'filepath': filepath})
      websocket.receive_json()
      websocket.receive_json()

      websocket.send_json({'type': ClientRequestType.GET_IMAGE_HASH, 'coord': [5, 5, 10, 10], 'key': 'key'})
      data = websocket.receive_json()
      self.assertGetImageHash(data, 'a5d22de7581c871e,07000000000')

  @timeout()
  def test_getImageHash_fromCoordAfterUpdateScreenshot(self):
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.UPDATE_SCREENSHOT, 'key': 'key', 'doesClearLastImage': True,
          'image': 'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAG0lEQVR4nGOIi4v7//nz5/9Mz58/Zzh27BgDAGXBCvvJ+AJ6AAAAAElFTkSuQmCC'})

      websocket.send_json({'type': ClientRequestType.GET_IMAGE_HASH, 'coord': [0, 0, 2, 2], 'key': 'key'})
      data = websocket.receive_json()
      self.assertGetImageHash(data, '90955ad25ada4bab,07000000000')

  @timeout()
  def test_getImageHash_fromImage(self):
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.GET_IMAGE_HASH, 'key': 'key',
          'image': 'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAG0lEQVR4nGOIi4v7//nz5/9Mz58/Zzh27BgDAGXBCvvJ+AJ6AAAAAElFTkSuQmCC'})
      data = websocket.receive_json()
      self.assertGetImageHash(data, '90955ad25ada4bab,07000000000')

  @timeout()
  def test_getImageHashDifference_invalidHashReference(self):
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.GET_IMAGE_HASH_DIFFERENCE, 'hashReference': 'invalid', 'hash': 'a5d22de7581c871e,07000000000', 'key': 'key'})
      data = websocket.receive_json()
      self.assertHasError(data, ServerResponseType.GET_IMAGE_HASH_DIFFERENCE)

  @timeout()
  def test_getImageHashDifference_validHashReference(self):
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.GET_IMAGE_HASH_DIFFERENCE, 'hashReference': '90955ad25ada4bab,07000000000',
          'hash': 'a5d22de7581c871e,07000000000', 'key': 'key'})
      data = websocket.receive_json()
      self.assertGetImageHashDifference(data, 32)

  @timeout()
  def test_isImageHashValid_false(self):
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.IS_IMAGE_HASH_VALID, 'hash': 'invalid', 'key': 'key'})
      data = websocket.receive_json()
      self.assertIsImageHashValid(data, False)

  @timeout()
  def test_isImageHashValid_true(self):
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.IS_IMAGE_HASH_VALID, 'hash': '90955ad25ada4bab,07000000000', 'key': 'key'})
      data = websocket.receive_json()
      self.assertIsImageHashValid(data, True)

  @timeout()
  def test_preprocessImage_oneSuboperation(self):
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.PREPROCESS_IMAGE, 'key': 'key', 'operations': [{'type': PreprocessingType.GRAYSCALE.value, 'params': {}}],
        'image': 'iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAAXNSR0IArs4c6QAAAFRJREFUGFdjXHTk7v/irbcYXn/7zQADjCEzj/1fc/UVXADEgAheQRNcePjO/+odtxmefvrOwMzIyKAtzsvAeP/Z+/83Xn5hePDuOwMzMyODoRQ/AwCfESRcVwbSqAAAAABJRU5ErkJggg==',
      })
      data = websocket.receive_json()
      self.assertPreprocessImage(data, width=5, height=5)

  @timeout()
  def test_preprocessImage_manySuboperations(self):
    with getWebsocketWithAppMocks(self.client) as websocket:
      websocket.send_json({'type': ClientRequestType.PREPROCESS_IMAGE, 'key': 'key',
        'operations': [
          {'type': PreprocessingType.COLOR_MAP.value, 'params': {'inputColor1': [255, 255, 255], 'inputColor2': [97, 97, 97], 'outputColor1': [103, 45, 45], 'outputColor2': [193, 26, 6], 'method': ColorMapMethod.RANGE_TO_RANGE.value, 'difference': 0.1}},
          {'type': PreprocessingType.GRAYSCALE.value, 'params': {}},
          {'type': PreprocessingType.THRESHOLD.value, 'params': {'thresholdType': ThresholdType.BINARY.value, 'method': ThresholdMethod.ADAPTIVE_MEAN.value, 'maxValue': 255, 'threshold': 127, 'blockSize': 11, 'cConstant': 2}},
          {'type': PreprocessingType.RESIZE.value, 'params': {'method': ResizeMethod.UNFIXED_RATIO.value, 'width': 100, 'height': 100}}
        ],
        'image': 'iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAYAAACp8Z5+AAAAAXNSR0IArs4c6QAAADxJREFUGFdjDJl57P+aq68YYIARLHAFSWDh4Tv/q3fcZnj66TsDMyMjA+P9Z+//33j5heHBu+8MzMyMDAB9MRuS1JvnbQAAAABJRU5ErkJggg=='
      })
      data = websocket.receive_json()
      self.assertPreprocessImage(data, width=100, height=100)

if __name__ == '__main__':
  unittest.main()
