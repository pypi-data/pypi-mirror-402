"""
Test the calls handled by a websocket that use ProcessManager.

Those calls don't work well with fastapi.testclient.TestClient.
When using ProcessManager and TestClient, the test doesn't end, some data is sent using the websocket but nothing is received in the test function.
There may be a way to fix this. This test suite is a workaround using more mocks to test those calls that use ProcessManager.
"""

import asyncio
import json
import logging
import sys
import tempfile
import threading
import unittest
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from unittest.mock import AsyncMock, patch

from guirecognizerapp.call_manager import CallManager
from guirecognizerapp.server import ConnectionManager
from guirecognizerapp.server_client_interface import (ClientRequestType,
                                                      ServerResponseType)

# Tkinter window creation is mocked so as to avoid a multithreading issue.
# Function handleTakeScreenshotShortcut is mocked so that the global shortcut to take screenshot does not interfere with the tests.

class IsolatedAsyncioLoggedTestCase(unittest.IsolatedAsyncioTestCase):
  def setUp(self):
    logger = logging.getLogger('guirecognizerapp')
    logger.level = logging.DEBUG
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(fmt='%(levelname)s: %(message)s'))
    logger.addHandler(stream_handler)

@asynccontextmanager
async def getCallManageWithAppMocks() -> AsyncIterator[tuple[CallManager, AsyncMock, asyncio.Event]]:
    with tempfile.TemporaryDirectory() as directory, patch('platformdirs.user_config_dir') as configMock, patch('platformdirs.user_cache_dir') as cacheMock, \
        patch('tkinter.Tk'), patch('guirecognizerapp.call_manager.CallManager.handleTakeScreenshotShortcut'):
      configMock.return_value = directory
      cacheMock.return_value = directory

      websocket = AsyncMock()
      loop = asyncio.get_running_loop()
      event = asyncio.Event()
      websocket.send_text.side_effect = lambda _: loop.call_soon_threadsafe(event.set)

      connectionManager = ConnectionManager()
      callManager = await connectionManager.connect(websocket)
      try:
        yield (callManager, websocket.send_text, event)
      finally:
        connectionManager.disconnect(callManager)

class TestUsingProcess(IsolatedAsyncioLoggedTestCase):
  def assertResponseType(self, data: Any, responseType: ServerResponseType):
    self.assertIn('type', data)
    self.assertEqual(data['type'], responseType)

  def assertHasError(self, data: Any, responseType: ServerResponseType):
    self.assertResponseType(data, responseType)
    self.assertIn('error', data)
    self.assertEqual(type(data['error']), str)

  def assertFindImage(self, data: Any, foundImages: list):
    self.assertResponseType(data, ServerResponseType.FIND_IMAGE)
    self.assertIn('foundImages', data)
    self.assertEqual(data['foundImages'], foundImages)
    self.assertIn('elapsedTime', data)
    self.assertEqual(type(data['elapsedTime']), float)
    self.assertIn('key', data)
    self.assertEqual(type(data['key']), str)

  def assertGetText(self, data: Any, text: str):
    self.assertResponseType(data, ServerResponseType.GET_TEXT)
    self.assertIn('text', data)
    self.assertEqual(data['text'], text)
    self.assertIn('elapsedTime', data)
    self.assertEqual(type(data['elapsedTime']), float)
    self.assertIn('key', data)
    self.assertEqual(type(data['key']), str)

  def assertGetNumber(self, data: Any, nb: float | None):
    self.assertResponseType(data, ServerResponseType.GET_NUMBER)
    self.assertIn('nb', data)
    self.assertEqual(data['nb'], nb)
    self.assertIn('elapsedTime', data)
    self.assertEqual(type(data['elapsedTime']), float)
    self.assertIn('key', data)
    self.assertEqual(type(data['key']), str)

  def assertSearchTesseractCmd(self, data: Any):
    self.assertResponseType(data, ServerResponseType.SEARCH_TESSERACT_CMD)
    self.assertIn('cmd', data)
    self.assertEqual(type(data['cmd']), str)
    self.assertIn('key', data)
    self.assertEqual(type(data['key']), str)

  async def test_findImage(self):
    async with getCallManageWithAppMocks() as (callManager, mock, event):
      data = {'type': ClientRequestType.FIND_IMAGE, 'key': 'key', 'coord': [303,70,410,91],
        'image': 'iVBORw0KGgoAAAANSUhEUgAAAGsAAAAVCAYAAABBlxC9AAAAAXNSR0IArs4c6QAAA9VJREFUaEPtWD1PG0EQff4bsXxC+Q8gOY4EHVWkFOQsodAgpTEFzocLfgEFSYACl2lASHZSIKVJiSVsS+Q3BCE7V6ahpHG0tx+3uzd7d7a5iItMZXH7MfPezsybKf25u59g8VcIBEoLsgrBU2jkoyXr5/ELHGIP57vPioNmzpaWttfXJ0ut79hZyfmmKY/PSlbwrYFWZxyd7m3h4JOP8pT3ZV0eu09tXMXbrx+wnPUgY90YF+8b6I60fxJ+lNbfnE3ydA5BF63mJWpHbbycAsFsZA1wcgzsqOgTTiM/wjhZT+cghmAz6OJkWMXORkV8HODk1T76FmGl7S+/Jgdq0UzPInlTrmQRV19/xOYBHhZM7ZpcyKIQDP24ga898tKPu/vJbKGbkdh/TFbeYOZ9vkKVwI0LDIJFwJFSjJcrwlXn7bkUBUQeBlCutxFFcny//K7S4MZvtJqnCMQd5n7rwYQOngLsjuow/E3V4/Ds0WypMpks4bNnCaMQsx5qhjbga/tVHQ/NHyJDCDXIQbslgawYoajXEmb4hdeOxIkOlkytrsgSawNFLsDqm8zd4T1XAPS8TTotHBTfIjIdwMHyVdrhTBSm/2mRRX1XosTy1VnLhU32Q1PSPfbamPMdoIYeUJdqkTuKBPUYEwYkWS4gI8Q4WbbCykiAOIYEds6a5lSDkogY0NzmwFtFf+QppRqeM1yLlKt4bNx0WllGfZblBAOrW27DDxpRv5MEvEt2UnscL0d/3C41SKYwJwHxjJFNZbrrcVpkyfKh0lvo6wj+kYeupoqT7ZDlQSdtoDfFetSw32coMyUSROrqifUaZKrS60gMTIosskaaAE1Plqmc5GmGPRkeSZpsSicL0KMGDLPgNc53K1qNGqdmKNjp2pxgaCmmOsBmR4asJG4P+KwVRAfgmcjKoBCnIisJYc3O5aGVeti+B65ZoSnqTo5ZIMpISCIjjuGb2l7EU74xbpIvwvdO0S9LlSJVyxaWOpc82lhzS5JFNHMkMZSgmSOyEsNB2r+H2nDfrb7SQiqpDsb2iixV38JtZwRfTjZEuvbrN+iG0ZY0SotjZM4GBbDwgNq7aOLASQTKWENTjnII5UcqOCKco9fXM6W8rQaJ2SBZsygVGmtk2UhqnpEQPzBLGmTrwpo/qiDwdFJ4lrr1xlhSoo2tbSDY0Cc8dNtkDXIdvRUls1W49xQsrI9YGcZ7GF1BGX1SLAVFMnmqNJhClkp1unTOGEn2Mvds0JT4PPPYvRUn8fCKXmvcRdj6aKfuM2L5X29bkFUgehdkLcgqEAIFMnURWQUi6y+oApbB3XY+7QAAAABJRU5ErkJggg==',
        'findImageInfo': {
          'imageToFind': {
            'data': 'iVBORw0KGgoAAAANSUhEUgAAAA0AAAAJCAYAAADpeqZqAAAAAXNSR0IArs4c6QAAAR1JREFUKFNdkb9Kw1AUxn95jpJL8R0UagXdnASHmkDRTZc4tKIZ+gQO8U8czKaLpZDoIPgCCrZC3VycLCXhjlk6ukRy722snu3ew/f7zvmOdXOwWSSix6CzSlXjM9rBC03/icOV+W/G47HHsBFhfdzuF368xNH9CcumLx88/DiDtQWYTPC7zzTDCCv/7Bd+9456RdVEKdYZpoLg3KEGKNDbhnpb+eyrmNsGLRsUMcUJBYkhb9fg/WqLS7Szlc++i0UKJVHuMujY1Q5BK+N65xTMNEqEWnyCE/bgwkO6OgAFKwGNEe2Aam8tYqRJ7h7TOMWZh6Jg4LgTEuWuEzYiPXOS2kjx29SwPlORUTfuf0R6xP+3MQG82jhhRBlIWT+leJ0g+CrGrQAAAABJRU5ErkJggg==',
            'width': 13, 'height': 9
          },
          'threshold': 5, 'maxNbResults': 5, 'resizeInterval': {'min': None, 'max': None}
        }
      }
      await callManager.manageData(json.dumps(data))
      await asyncio.wait_for(event.wait(), timeout=10)
      receivedData = json.loads(mock.call_args.args[0])
      self.assertFindImage(receivedData, [[387, 77, 400, 86]])

  async def test_findImage_withResizeInterval(self):
    async with getCallManageWithAppMocks() as (callManager, mock, event):
      data = {'type': ClientRequestType.FIND_IMAGE, 'key': 'key', 'coord': [303,70,410,91],
        'image': 'iVBORw0KGgoAAAANSUhEUgAAAGsAAAAVCAYAAABBlxC9AAAAAXNSR0IArs4c6QAAA9VJREFUaEPtWD1PG0EQff4bsXxC+Q8gOY4EHVWkFOQsodAgpTEFzocLfgEFSYACl2lASHZSIKVJiSVsS+Q3BCE7V6ahpHG0tx+3uzd7d7a5iItMZXH7MfPezsybKf25u59g8VcIBEoLsgrBU2jkoyXr5/ELHGIP57vPioNmzpaWttfXJ0ut79hZyfmmKY/PSlbwrYFWZxyd7m3h4JOP8pT3ZV0eu09tXMXbrx+wnPUgY90YF+8b6I60fxJ+lNbfnE3ydA5BF63mJWpHbbycAsFsZA1wcgzsqOgTTiM/wjhZT+cghmAz6OJkWMXORkV8HODk1T76FmGl7S+/Jgdq0UzPInlTrmQRV19/xOYBHhZM7ZpcyKIQDP24ga898tKPu/vJbKGbkdh/TFbeYOZ9vkKVwI0LDIJFwJFSjJcrwlXn7bkUBUQeBlCutxFFcny//K7S4MZvtJqnCMQd5n7rwYQOngLsjuow/E3V4/Ds0WypMpks4bNnCaMQsx5qhjbga/tVHQ/NHyJDCDXIQbslgawYoajXEmb4hdeOxIkOlkytrsgSawNFLsDqm8zd4T1XAPS8TTotHBTfIjIdwMHyVdrhTBSm/2mRRX1XosTy1VnLhU32Q1PSPfbamPMdoIYeUJdqkTuKBPUYEwYkWS4gI8Q4WbbCykiAOIYEds6a5lSDkogY0NzmwFtFf+QppRqeM1yLlKt4bNx0WllGfZblBAOrW27DDxpRv5MEvEt2UnscL0d/3C41SKYwJwHxjJFNZbrrcVpkyfKh0lvo6wj+kYeupoqT7ZDlQSdtoDfFetSw32coMyUSROrqifUaZKrS60gMTIosskaaAE1Plqmc5GmGPRkeSZpsSicL0KMGDLPgNc53K1qNGqdmKNjp2pxgaCmmOsBmR4asJG4P+KwVRAfgmcjKoBCnIisJYc3O5aGVeti+B65ZoSnqTo5ZIMpISCIjjuGb2l7EU74xbpIvwvdO0S9LlSJVyxaWOpc82lhzS5JFNHMkMZSgmSOyEsNB2r+H2nDfrb7SQiqpDsb2iixV38JtZwRfTjZEuvbrN+iG0ZY0SotjZM4GBbDwgNq7aOLASQTKWENTjnII5UcqOCKco9fXM6W8rQaJ2SBZsygVGmtk2UhqnpEQPzBLGmTrwpo/qiDwdFJ4lrr1xlhSoo2tbSDY0Cc8dNtkDXIdvRUls1W49xQsrI9YGcZ7GF1BGX1SLAVFMnmqNJhClkp1unTOGEn2Mvds0JT4PPPYvRUn8fCKXmvcRdj6aKfuM2L5X29bkFUgehdkLcgqEAIFMnURWQUi6y+oApbB3XY+7QAAAABJRU5ErkJggg==',
        'findImageInfo': {
          'imageToFind': {
            'data': 'iVBORw0KGgoAAAANSUhEUgAAAA0AAAAJCAYAAADpeqZqAAAAAXNSR0IArs4c6QAAAR1JREFUKFNdkb9Kw1AUxn95jpJL8R0UagXdnASHmkDRTZc4tKIZ+gQO8U8czKaLpZDoIPgCCrZC3VycLCXhjlk6ukRy722snu3ew/f7zvmOdXOwWSSix6CzSlXjM9rBC03/icOV+W/G47HHsBFhfdzuF368xNH9CcumLx88/DiDtQWYTPC7zzTDCCv/7Bd+9456RdVEKdYZpoLg3KEGKNDbhnpb+eyrmNsGLRsUMcUJBYkhb9fg/WqLS7Szlc++i0UKJVHuMujY1Q5BK+N65xTMNEqEWnyCE/bgwkO6OgAFKwGNEe2Aam8tYqRJ7h7TOMWZh6Jg4LgTEuWuEzYiPXOS2kjx29SwPlORUTfuf0R6xP+3MQG82jhhRBlIWT+leJ0g+CrGrQAAAABJRU5ErkJggg==',
            'width': 13, 'height': 9
          },
          'threshold': 15, 'maxNbResults': 5, 'resizeInterval': {'min': 1.1, 'max': 1.5}
        }
      }
      await callManager.manageData(json.dumps(data))
      await asyncio.wait_for(event.wait(), timeout=10)
      receivedData = json.loads(mock.call_args.args[0])
      self.assertFindImage(receivedData, [[304, 77, 318, 86], [386, 77, 400, 86]])

  async def test_findImage_cancelPreviousWork(self):
    async with getCallManageWithAppMocks() as (callManager, mock, event):
      data = {'type': ClientRequestType.GET_TEXT, 'key': 'key',
        'image': 'iVBORw0KGgoAAAANSUhEUgAAABMAAAAWCAYAAAAinad/AAAAAXNSR0IArs4c6QAAAb1JREFUOE+1lD2vAVEQht8NCaGg0yManei0foAQ0Sv8Ah/xkYjQCoVEpaVBKSREoVFoKEVJolAJCUL2ZiZxwt67cZd7T7e7M8/OvPOekSwWi4w/OtK/wEKhEEqlEsxm84913m437Pd7rFYrNJtNdDqdb3Gislewx8zr9YrBYIB4PI7j8Sg+qcIo4Xw+c6BOp4PRaHyq5HK5oF6vo1wuv4Ytl0v4/X4R6PF4kM1m4fV6IUkSv5/NZggGg9phlBGJRFAoFGAymRig/KFqm8pASlbq+hGsUqkgEAiwhrIs8xBisdjrNg+HA9brtQi0Wq2w2WxCr+12i1QqhfF4zDEulwtvWYPay+VymE6n4mfpdPo9GBE2mw0ymYyorNvtqsOU4lIbiUSC7UKa0VksFjxhp9PJntM0TbvdjkajAYfDwTDSNZ/Pc5XValUbjACtVgs+n49h91swmUxQq9W0wWgJtNttuN1uhp1OJ5BdqMVer/d7GIFI8HA4LO7pbrdDMpnEcDhEsVhUhz1edKrCYDBAr9cLK5BpR6MRotHoZz4j0Hw+5xVEU78fTaYljWhy/X6fBX/cZQT8n7X9tPnefPgCvT8ZAO+m/7YAAAAASUVORK5CYII='
      }
      await callManager.manageData(json.dumps(data))
      data = {'type': ClientRequestType.FIND_IMAGE, 'key': 'key', 'coord': [303,70,410,91],
        'image': 'iVBORw0KGgoAAAANSUhEUgAAAGsAAAAVCAYAAABBlxC9AAAAAXNSR0IArs4c6QAAA9VJREFUaEPtWD1PG0EQff4bsXxC+Q8gOY4EHVWkFOQsodAgpTEFzocLfgEFSYACl2lASHZSIKVJiSVsS+Q3BCE7V6ahpHG0tx+3uzd7d7a5iItMZXH7MfPezsybKf25u59g8VcIBEoLsgrBU2jkoyXr5/ELHGIP57vPioNmzpaWttfXJ0ut79hZyfmmKY/PSlbwrYFWZxyd7m3h4JOP8pT3ZV0eu09tXMXbrx+wnPUgY90YF+8b6I60fxJ+lNbfnE3ydA5BF63mJWpHbbycAsFsZA1wcgzsqOgTTiM/wjhZT+cghmAz6OJkWMXORkV8HODk1T76FmGl7S+/Jgdq0UzPInlTrmQRV19/xOYBHhZM7ZpcyKIQDP24ga898tKPu/vJbKGbkdh/TFbeYOZ9vkKVwI0LDIJFwJFSjJcrwlXn7bkUBUQeBlCutxFFcny//K7S4MZvtJqnCMQd5n7rwYQOngLsjuow/E3V4/Ds0WypMpks4bNnCaMQsx5qhjbga/tVHQ/NHyJDCDXIQbslgawYoajXEmb4hdeOxIkOlkytrsgSawNFLsDqm8zd4T1XAPS8TTotHBTfIjIdwMHyVdrhTBSm/2mRRX1XosTy1VnLhU32Q1PSPfbamPMdoIYeUJdqkTuKBPUYEwYkWS4gI8Q4WbbCykiAOIYEds6a5lSDkogY0NzmwFtFf+QppRqeM1yLlKt4bNx0WllGfZblBAOrW27DDxpRv5MEvEt2UnscL0d/3C41SKYwJwHxjJFNZbrrcVpkyfKh0lvo6wj+kYeupoqT7ZDlQSdtoDfFetSw32coMyUSROrqifUaZKrS60gMTIosskaaAE1Plqmc5GmGPRkeSZpsSicL0KMGDLPgNc53K1qNGqdmKNjp2pxgaCmmOsBmR4asJG4P+KwVRAfgmcjKoBCnIisJYc3O5aGVeti+B65ZoSnqTo5ZIMpISCIjjuGb2l7EU74xbpIvwvdO0S9LlSJVyxaWOpc82lhzS5JFNHMkMZSgmSOyEsNB2r+H2nDfrb7SQiqpDsb2iixV38JtZwRfTjZEuvbrN+iG0ZY0SotjZM4GBbDwgNq7aOLASQTKWENTjnII5UcqOCKco9fXM6W8rQaJ2SBZsygVGmtk2UhqnpEQPzBLGmTrwpo/qiDwdFJ4lrr1xlhSoo2tbSDY0Cc8dNtkDXIdvRUls1W49xQsrI9YGcZ7GF1BGX1SLAVFMnmqNJhClkp1unTOGEn2Mvds0JT4PPPYvRUn8fCKXmvcRdj6aKfuM2L5X29bkFUgehdkLcgqEAIFMnURWQUi6y+oApbB3XY+7QAAAABJRU5ErkJggg==',
        'findImageInfo': {
          'imageToFind': {
            'data': 'iVBORw0KGgoAAAANSUhEUgAAAA0AAAAJCAYAAADpeqZqAAAAAXNSR0IArs4c6QAAAR1JREFUKFNdkb9Kw1AUxn95jpJL8R0UagXdnASHmkDRTZc4tKIZ+gQO8U8czKaLpZDoIPgCCrZC3VycLCXhjlk6ukRy722snu3ew/f7zvmOdXOwWSSix6CzSlXjM9rBC03/icOV+W/G47HHsBFhfdzuF368xNH9CcumLx88/DiDtQWYTPC7zzTDCCv/7Bd+9456RdVEKdYZpoLg3KEGKNDbhnpb+eyrmNsGLRsUMcUJBYkhb9fg/WqLS7Szlc++i0UKJVHuMujY1Q5BK+N65xTMNEqEWnyCE/bgwkO6OgAFKwGNEe2Aam8tYqRJ7h7TOMWZh6Jg4LgTEuWuEzYiPXOS2kjx29SwPlORUTfuf0R6xP+3MQG82jhhRBlIWT+leJ0g+CrGrQAAAABJRU5ErkJggg==',
            'width': 13, 'height': 9
          },
          'threshold': 5, 'maxNbResults': 5, 'resizeInterval': {'min': None, 'max': None}
        }
      }
      await callManager.manageData(json.dumps(data))
      await asyncio.wait_for(event.wait(), timeout=10)
      receivedData = json.loads(mock.call_args.args[0])
      self.assertFindImage(receivedData, [[387, 77, 400, 86]])

  async def test_getText(self):
    async with getCallManageWithAppMocks() as (callManager, mock, event):
      data = {'type': ClientRequestType.GET_TEXT, 'key': 'key',
        'image': 'iVBORw0KGgoAAAANSUhEUgAAABMAAAAWCAYAAAAinad/AAAAAXNSR0IArs4c6QAAAb1JREFUOE+1lD2vAVEQht8NCaGg0yManei0foAQ0Sv8Ah/xkYjQCoVEpaVBKSREoVFoKEVJolAJCUL2ZiZxwt67cZd7T7e7M8/OvPOekSwWi4w/OtK/wEKhEEqlEsxm84913m437Pd7rFYrNJtNdDqdb3Gislewx8zr9YrBYIB4PI7j8Sg+qcIo4Xw+c6BOp4PRaHyq5HK5oF6vo1wuv4Ytl0v4/X4R6PF4kM1m4fV6IUkSv5/NZggGg9phlBGJRFAoFGAymRig/KFqm8pASlbq+hGsUqkgEAiwhrIs8xBisdjrNg+HA9brtQi0Wq2w2WxCr+12i1QqhfF4zDEulwtvWYPay+VymE6n4mfpdPo9GBE2mw0ymYyorNvtqsOU4lIbiUSC7UKa0VksFjxhp9PJntM0TbvdjkajAYfDwTDSNZ/Pc5XValUbjACtVgs+n49h91swmUxQq9W0wWgJtNttuN1uhp1OJ5BdqMVer/d7GIFI8HA4LO7pbrdDMpnEcDhEsVhUhz1edKrCYDBAr9cLK5BpR6MRotHoZz4j0Hw+5xVEU78fTaYljWhy/X6fBX/cZQT8n7X9tPnefPgCvT8ZAO+m/7YAAAAASUVORK5CYII='
      }
      await callManager.manageData(json.dumps(data))
      await asyncio.wait_for(event.wait(), timeout=100)
      receivedData = json.loads(mock.call_args.args[0])
      self.assertGetText(receivedData, 'B')

  async def test_getText_emptyString(self):
    async with getCallManageWithAppMocks() as (callManager, mock, event):
      data = {'type': ClientRequestType.GET_TEXT, 'key': 'key',
        'image': 'iVBORw0KGgoAAAANSUhEUgAAAAkAAAAKCAYAAABmBXS+AAAAAXNSR0IArs4c6QAAABZJREFUKFNj5Ofn/89AADCOKqJeEAAAL1QLw3zF5FUAAAAASUVORK5CYII='
      }
      await callManager.manageData(json.dumps(data))
      await asyncio.wait_for(event.wait(), timeout=100)
      receivedData = json.loads(mock.call_args.args[0])
      self.assertGetText(receivedData, '')

  async def test_getText_cancelPreviousWork(self):
    async with getCallManageWithAppMocks() as (callManager, mock, event):
      data = {'type': ClientRequestType.GET_NUMBER, 'key': 'key',
        'image': 'iVBORw0KGgoAAAANSUhEUgAAABsAAAAWCAYAAAAxSueLAAAAAXNSR0IArs4c6QAAAflJREFUSEvtVU2rqWEUXYiTjwmRn2BkRgYGzEgYUooMEIWJYkKhTJRMJGWoJGWC/AFlQvEPxAxDKRLntp9yu86Ley/nns7g7tHb87T3etbaa++Xp9Fo3vFFwfsP9hlKfw8Z1Wo1bDYbrFYrJBIJ8vk8xuPxFUGfzwe32w2lUsnOV6sVWq0Wms3mTSE4zAjAbrdDq9Xi7e2NJa3Xa+RyuSuwSCQCj8cDkUiE7XYLHo8HmUyGw+GAer2ORqPBAeSAVatV6HQ6HI9HVkShUHDA6CGFQgHEfjKZIJlMssLFYhF6vR6LxQKJRALL5fIKkAMWi8VwOp3Q6XQQDAbhdDo5YF6vl91RVCoVtNtt9u1yuRCNRll+qVRCv99/DPbrbTqdvgkWDodBgMSe2AwGA5ZGLSCWQqGQyVir1V4HCwQC8Pv9Pxl0u91/B2Y0GpHJZCCXyzEajUAK7HY7ZLNZWCwWnM/nz2NGNC6F+Xw+NpsNY6ZSqZgr9/v9VS8vWj4c6ns9o2SpVIpUKgWTyQSxWMycO51OYTAYGEty63A4fL1n91ZXuVwGSTybzRAKhX4/Z3/ixo9VaN7i8TjMZjMzDc0qbZKP8bSMVIhsTnanTSMQCNj26PV6bBxuxUtg1FOHw8EMMZ/P2XBfZu6vwe715tnz7/GLefb1j/K+lNkPknVAHrOet8wAAAAASUVORK5CYII='
      }
      await callManager.manageData(json.dumps(data))
      data = {'type': ClientRequestType.GET_TEXT, 'key': 'key',
        'image': 'iVBORw0KGgoAAAANSUhEUgAAABMAAAAWCAYAAAAinad/AAAAAXNSR0IArs4c6QAAAb1JREFUOE+1lD2vAVEQht8NCaGg0yManei0foAQ0Sv8Ah/xkYjQCoVEpaVBKSREoVFoKEVJolAJCUL2ZiZxwt67cZd7T7e7M8/OvPOekSwWi4w/OtK/wEKhEEqlEsxm84913m437Pd7rFYrNJtNdDqdb3Gislewx8zr9YrBYIB4PI7j8Sg+qcIo4Xw+c6BOp4PRaHyq5HK5oF6vo1wuv4Ytl0v4/X4R6PF4kM1m4fV6IUkSv5/NZggGg9phlBGJRFAoFGAymRig/KFqm8pASlbq+hGsUqkgEAiwhrIs8xBisdjrNg+HA9brtQi0Wq2w2WxCr+12i1QqhfF4zDEulwtvWYPay+VymE6n4mfpdPo9GBE2mw0ymYyorNvtqsOU4lIbiUSC7UKa0VksFjxhp9PJntM0TbvdjkajAYfDwTDSNZ/Pc5XValUbjACtVgs+n49h91swmUxQq9W0wWgJtNttuN1uhp1OJ5BdqMVer/d7GIFI8HA4LO7pbrdDMpnEcDhEsVhUhz1edKrCYDBAr9cLK5BpR6MRotHoZz4j0Hw+5xVEU78fTaYljWhy/X6fBX/cZQT8n7X9tPnefPgCvT8ZAO+m/7YAAAAASUVORK5CYII='
      }
      await callManager.manageData(json.dumps(data))
      await asyncio.wait_for(event.wait(), timeout=100)
      receivedData = json.loads(mock.call_args.args[0])
      self.assertGetText(receivedData, 'B')

  async def test_getText_error(self):
    async with getCallManageWithAppMocks() as (callManager, mock, event):
      with patch('guirecognizerapp.call_manager.ProcessManager.executeGetText') as getTextMock:
        getTextMock.return_value = 1

        def mockSideEffect(_area, _settingData, callback):
          thread = threading.Thread(target=callback, args=(None, None, 'Mock recognize number error.'))
          thread.start()
        getTextMock.side_effect = mockSideEffect

        data = {'type': ClientRequestType.GET_TEXT, 'key': 'key',
          'image': 'iVBORw0KGgoAAAANSUhEUgAAAAkAAAAKCAYAAABmBXS+AAAAAXNSR0IArs4c6QAAABZJREFUKFNj5Ofn/89AADCOKqJeEAAAL1QLw3zF5FUAAAAASUVORK5CYII='
        }
        await callManager.manageData(json.dumps(data))
        await asyncio.wait_for(event.wait(), timeout=10)
        receivedData = json.loads(mock.call_args.args[0])
        self.assertHasError(receivedData, ServerResponseType.GET_TEXT)

  async def test_getNumber(self):
    async with getCallManageWithAppMocks() as (callManager, mock, event):
      data = {'type': ClientRequestType.GET_NUMBER, 'key': 'key',
        'image': 'iVBORw0KGgoAAAANSUhEUgAAABsAAAAWCAYAAAAxSueLAAAAAXNSR0IArs4c6QAAAflJREFUSEvtVU2rqWEUXYiTjwmRn2BkRgYGzEgYUooMEIWJYkKhTJRMJGWoJGWC/AFlQvEPxAxDKRLntp9yu86Ley/nns7g7tHb87T3etbaa++Xp9Fo3vFFwfsP9hlKfw8Z1Wo1bDYbrFYrJBIJ8vk8xuPxFUGfzwe32w2lUsnOV6sVWq0Wms3mTSE4zAjAbrdDq9Xi7e2NJa3Xa+RyuSuwSCQCj8cDkUiE7XYLHo8HmUyGw+GAer2ORqPBAeSAVatV6HQ6HI9HVkShUHDA6CGFQgHEfjKZIJlMssLFYhF6vR6LxQKJRALL5fIKkAMWi8VwOp3Q6XQQDAbhdDo5YF6vl91RVCoVtNtt9u1yuRCNRll+qVRCv99/DPbrbTqdvgkWDodBgMSe2AwGA5ZGLSCWQqGQyVir1V4HCwQC8Pv9Pxl0u91/B2Y0GpHJZCCXyzEajUAK7HY7ZLNZWCwWnM/nz2NGNC6F+Xw+NpsNY6ZSqZgr9/v9VS8vWj4c6ns9o2SpVIpUKgWTyQSxWMycO51OYTAYGEty63A4fL1n91ZXuVwGSTybzRAKhX4/Z3/ixo9VaN7i8TjMZjMzDc0qbZKP8bSMVIhsTnanTSMQCNj26PV6bBxuxUtg1FOHw8EMMZ/P2XBfZu6vwe715tnz7/GLefb1j/K+lNkPknVAHrOet8wAAAAASUVORK5CYII='
      }
      await callManager.manageData(json.dumps(data))
      await asyncio.wait_for(event.wait(), timeout=100)
      receivedData = json.loads(mock.call_args.args[0])
      self.assertGetNumber(receivedData, 19)

  async def test_getNumber_notANumber(self):
    async with getCallManageWithAppMocks() as (callManager, mock, event):
      data = {'type': ClientRequestType.GET_NUMBER, 'key': 'key',
        'image': 'iVBORw0KGgoAAAANSUhEUgAAAAkAAAAKCAYAAABmBXS+AAAAAXNSR0IArs4c6QAAABZJREFUKFNj5Ofn/89AADCOKqJeEAAAL1QLw3zF5FUAAAAASUVORK5CYII='
      }
      await callManager.manageData(json.dumps(data))
      await asyncio.wait_for(event.wait(), timeout=100)
      receivedData = json.loads(mock.call_args.args[0])
      self.assertGetNumber(receivedData, None)

  async def test_getNumber_cancelPreviousWork(self):
    async with getCallManageWithAppMocks() as (callManager, mock, event):
      data = {'type': ClientRequestType.GET_TEXT, 'key': 'key',
        'image': 'iVBORw0KGgoAAAANSUhEUgAAABMAAAAWCAYAAAAinad/AAAAAXNSR0IArs4c6QAAAb1JREFUOE+1lD2vAVEQht8NCaGg0yManei0foAQ0Sv8Ah/xkYjQCoVEpaVBKSREoVFoKEVJolAJCUL2ZiZxwt67cZd7T7e7M8/OvPOekSwWi4w/OtK/wEKhEEqlEsxm84913m437Pd7rFYrNJtNdDqdb3Gislewx8zr9YrBYIB4PI7j8Sg+qcIo4Xw+c6BOp4PRaHyq5HK5oF6vo1wuv4Ytl0v4/X4R6PF4kM1m4fV6IUkSv5/NZggGg9phlBGJRFAoFGAymRig/KFqm8pASlbq+hGsUqkgEAiwhrIs8xBisdjrNg+HA9brtQi0Wq2w2WxCr+12i1QqhfF4zDEulwtvWYPay+VymE6n4mfpdPo9GBE2mw0ymYyorNvtqsOU4lIbiUSC7UKa0VksFjxhp9PJntM0TbvdjkajAYfDwTDSNZ/Pc5XValUbjACtVgs+n49h91swmUxQq9W0wWgJtNttuN1uhp1OJ5BdqMVer/d7GIFI8HA4LO7pbrdDMpnEcDhEsVhUhz1edKrCYDBAr9cLK5BpR6MRotHoZz4j0Hw+5xVEU78fTaYljWhy/X6fBX/cZQT8n7X9tPnefPgCvT8ZAO+m/7YAAAAASUVORK5CYII='
      }
      await callManager.manageData(json.dumps(data))
      data = {'type': ClientRequestType.GET_NUMBER, 'key': 'key',
        'image': 'iVBORw0KGgoAAAANSUhEUgAAABsAAAAWCAYAAAAxSueLAAAAAXNSR0IArs4c6QAAAflJREFUSEvtVU2rqWEUXYiTjwmRn2BkRgYGzEgYUooMEIWJYkKhTJRMJGWoJGWC/AFlQvEPxAxDKRLntp9yu86Ley/nns7g7tHb87T3etbaa++Xp9Fo3vFFwfsP9hlKfw8Z1Wo1bDYbrFYrJBIJ8vk8xuPxFUGfzwe32w2lUsnOV6sVWq0Wms3mTSE4zAjAbrdDq9Xi7e2NJa3Xa+RyuSuwSCQCj8cDkUiE7XYLHo8HmUyGw+GAer2ORqPBAeSAVatV6HQ6HI9HVkShUHDA6CGFQgHEfjKZIJlMssLFYhF6vR6LxQKJRALL5fIKkAMWi8VwOp3Q6XQQDAbhdDo5YF6vl91RVCoVtNtt9u1yuRCNRll+qVRCv99/DPbrbTqdvgkWDodBgMSe2AwGA5ZGLSCWQqGQyVir1V4HCwQC8Pv9Pxl0u91/B2Y0GpHJZCCXyzEajUAK7HY7ZLNZWCwWnM/nz2NGNC6F+Xw+NpsNY6ZSqZgr9/v9VS8vWj4c6ns9o2SpVIpUKgWTyQSxWMycO51OYTAYGEty63A4fL1n91ZXuVwGSTybzRAKhX4/Z3/ixo9VaN7i8TjMZjMzDc0qbZKP8bSMVIhsTnanTSMQCNj26PV6bBxuxUtg1FOHw8EMMZ/P2XBfZu6vwe715tnz7/GLefb1j/K+lNkPknVAHrOet8wAAAAASUVORK5CYII='
      }
      await callManager.manageData(json.dumps(data))
      await asyncio.wait_for(event.wait(), timeout=100)
      receivedData = json.loads(mock.call_args.args[0])
      self.assertGetNumber(receivedData, 19)

  async def test_getNumber_error(self):
    async with getCallManageWithAppMocks() as (callManager, mock, event):
      with patch('guirecognizerapp.call_manager.ProcessManager.executeGetNumber') as getNumberMock:
        getNumberMock.return_value = 1

        def mockSideEffect(_area, _settingData, callback):
          thread = threading.Thread(target=callback, args=(None, None, 'Mock recognize number error.'))
          thread.start()
        getNumberMock.side_effect = mockSideEffect

        data = {'type': ClientRequestType.GET_NUMBER, 'key': 'key',
          'image': 'iVBORw0KGgoAAAANSUhEUgAAAAkAAAAKCAYAAABmBXS+AAAAAXNSR0IArs4c6QAAABZJREFUKFNj5Ofn/89AADCOKqJeEAAAL1QLw3zF5FUAAAAASUVORK5CYII='
        }
        await callManager.manageData(json.dumps(data))
        await asyncio.wait_for(event.wait(), timeout=10)
        receivedData = json.loads(mock.call_args.args[0])
        self.assertHasError(receivedData, ServerResponseType.GET_NUMBER)

  async def test_searchTesseractCmd(self):
    async with getCallManageWithAppMocks() as (callManager, mock, event):
      data = {'type': ClientRequestType.SEARCH_TESSERACT_CMD, 'key': 'key'}
      await callManager.manageData(json.dumps(data))
      await asyncio.wait_for(event.wait(), timeout=100)
      receivedData = json.loads(mock.call_args.args[0])
      self.assertSearchTesseractCmd(receivedData)

  async def test_searchTesseractCmd_cancelPreviousWork(self):
    async with getCallManageWithAppMocks() as (callManager, mock, event):
      data = {'type': ClientRequestType.SEARCH_TESSERACT_CMD, 'key': 'key1'}
      await callManager.manageData(json.dumps(data))
      secondKey = 'key2'
      data = {'type': ClientRequestType.SEARCH_TESSERACT_CMD, 'key': secondKey}
      await callManager.manageData(json.dumps(data))
      await asyncio.wait_for(event.wait(), timeout=100)
      receivedData = json.loads(mock.call_args.args[0])
      self.assertSearchTesseractCmd(receivedData)
      self.assertEqual(receivedData['key'], secondKey)

  async def test_searchTesseractCmd_abort(self):
    async with getCallManageWithAppMocks() as (callManager, mock, event):
      with patch('guirecognizerapp.call_manager.ProcessManager.executeFindTesseractPath') as findPathMock:
        def mockSideEffect(callback):
            def worker():
                import time
                time.sleep(0.5)
                callback(None)
            thread = threading.Thread(target=worker)
            thread.start()
        findPathMock.side_effect = mockSideEffect

      key = 'key1'
      data = {'type': ClientRequestType.SEARCH_TESSERACT_CMD, 'key': key}
      await callManager.manageData(json.dumps(data))
      data = {'type': ClientRequestType.SEARCH_TESSERACT_CMD, 'key': key, 'doesAbort': True}
      await callManager.manageData(json.dumps(data))

      try:
        await asyncio.wait_for(event.wait(), timeout=3)
      except asyncio.TimeoutError:
        pass
      mock.assert_not_called()

  async def test_searchTesseractCmd_error(self):
    async with getCallManageWithAppMocks() as (callManager, mock, event):
      with patch('guirecognizerapp.call_manager.ProcessManager.executeFindTesseractPath') as findPathMock:
        findPathMock.return_value = 1

        def mockSideEffect(callback):
          thread = threading.Thread(target=callback, args=(None,))
          thread.start()
        findPathMock.side_effect = mockSideEffect

        data = {'type': ClientRequestType.SEARCH_TESSERACT_CMD, 'key': 'key'}
        await callManager.manageData(json.dumps(data))
        await asyncio.wait_for(event.wait(), timeout=10)
        receivedData = json.loads(mock.call_args.args[0])
        self.assertHasError(receivedData, ServerResponseType.SEARCH_TESSERACT_CMD)

if __name__ == '__main__':
  unittest.main()
