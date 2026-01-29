import json
import os
from pathlib import Path

import platformdirs


class CacheDataManager:
  maxNbRecentFiles = 10
  maxNbRecentImages = 10

  def __init__(self, appname: str):
    self.cacheDirectory = platformdirs.user_cache_dir(appname)
    self.cacheDataFilepath = os.path.join(self.cacheDirectory, 'cacheData.json')
    try:
      with open(self.cacheDataFilepath, 'r') as file:
        data = json.load(file)
        self.cacheData = {}
        if 'recentFiles' in data and isinstance(data['recentFiles'], (list, tuple)) and all(type(i) == str for i in data['recentFiles']):
          self.cacheData['recentFiles'] = data['recentFiles'][0:self.maxNbRecentFiles]
        else:
          self.cacheData['recentFiles'] = []
        if 'recentImages' in data and isinstance(data['recentImages'], (list, tuple)) and all(type(i) == str for i in data['recentImages']):
          self.cacheData['recentImages'] = data['recentImages'][0:self.maxNbRecentImages]
        else:
          self.cacheData['recentImages'] = []
        if 'lastImage' in data and isinstance(data['lastImage'], str):
          self.cacheData['lastImage'] = data['lastImage']
        else:
          self.cacheData['lastImage'] = None
    except:
      self.cacheData = {'recentFiles': [], 'recentImages': [], 'lastImage': None}

  def getRecentFiles(self) -> list[str]:
    return self.cacheData['recentFiles']

  def addRecentFile(self, filepath: str) -> None:
    self._addRecentFilepath(self.cacheData['recentFiles'], filepath, self.maxNbRecentFiles)
    self._save()

  def removeRecentFile(self, filepath: str) -> bool:
    if filepath not in self.cacheData['recentFiles']:
      return False
    self.cacheData['recentFiles'].remove(filepath)
    self._save()
    return True

  def clearRecentFiles(self) -> None:
    self.cacheData['recentFiles'].clear()
    self._save()

  def getRecentImages(self) -> list[str]:
    return self.cacheData['recentImages']

  def addRecentImage(self, imageFilepath: str) -> None:
    self._addRecentFilepath(self.cacheData['recentImages'], imageFilepath, self.maxNbRecentImages)
    self.cacheData['lastImage'] = imageFilepath
    self._save()

  def removeRecentImage(self, filepath: str) -> bool:
    if filepath not in self.cacheData['recentImages']:
      return False
    self.cacheData['recentImages'].remove(filepath)
    if filepath == self.cacheData['lastImage']:
      self.cacheData['lastImage'] = None
    self._save()
    return True

  def clearRecentImages(self) -> None:
    self.cacheData['recentImages'].clear()
    self.cacheData['lastImage'] = None
    self._save()

  def getLastImage(self) -> str | None:
    return self.cacheData['lastImage']

  def clearLastImage(self) -> str | None:
    if self.getLastImage() is None:
      return
    self.cacheData['lastImage'] = None
    self._save()

  def _addRecentFilepath(self, filepaths: list[str], filepath: str, maxNbRecentFilepaths: int) -> None:
    if filepath in filepaths:
      filepaths.remove(filepath)
    filepaths.insert(0, filepath)
    while len(filepaths) > maxNbRecentFilepaths:
      filepaths.pop()

  def _save(self) -> None:
    try:
      Path(self.cacheDirectory).mkdir(parents=True, exist_ok=True)
      with open(self.cacheDataFilepath, 'w') as file:
        json.dump(self.cacheData, file)
    except:
      pass
