from enum import Enum, unique


@unique
class ClientRequestType(str, Enum):
  INIT = 'init'
  SAVE_FILE = 'saveFile'
  OPEN_FILE = 'openFile'
  CLEAR_FILE_HISTORY = 'clearFileHistory'
  TAKE_SCREENSHOT = 'takeScreenshot'
  UPDATE_SCREENSHOT = 'updateScreenshot'
  OPEN_SCREENSHOT = 'openScreenshot'
  SAVE_SCREENSHOT = 'saveScreenshot'
  CLEAR_SCREENSHOT_HISTORY = 'clearScreesnhotHistory'
  SAVE_SETTINGS = 'saveSettings'
  OPEN_IN_FILE_BROWSER = 'openInFileBrowser'
  GET_FILEPATH = 'getFilepath'
  SEARCH_TESSERACT_CMD = 'searchTesseractCmd'
  FIND_IMAGE = 'findImage'
  GET_IMAGE_HASH = 'getImageHash'
  GET_IMAGE_HASH_DIFFERENCE = 'getImageHashDifference'
  IS_IMAGE_HASH_VALID = 'isImageHashValid'
  GET_TEXT = 'getText'
  GET_NUMBER = 'getNumber'
  PREPROCESS_IMAGE = 'preprocessImage'

@unique
class ServerResponseType(str, Enum):
  SAVE_FILE = 'saveFile'
  OPEN_FILE = 'openFile'
  RECENT_FILES = 'recentFiles'
  NEW_SCREENSHOT = 'newScreenshot'
  RECENT_SCREENSHOTS = 'recentScreenshots'
  UPDATE_SETTINGS = 'updateSettings'
  GET_FILEPATH = 'getFilepath'
  SEARCH_TESSERACT_CMD = 'searchTesseractCmd'
  FIND_IMAGE = 'findImage'
  GET_IMAGE_HASH = 'getImageHash'
  GET_IMAGE_HASH_DIFFERENCE = 'getImageHashDifference'
  IS_IMAGE_HASH_VALID = 'isImageHashValid'
  GET_TEXT = 'getText'
  GET_NUMBER = 'getNumber'
  PREPROCESS_IMAGE = 'preprocessImage'
