
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from guirecognizerapp.cache_manager import CacheDataManager
from tests.test_utility import LoggedTestCase


class TestCacheManager(LoggedTestCase):
  def test_files(self):
    with tempfile.TemporaryDirectory() as directory, patch('platformdirs.user_cache_dir') as cacheMock:
      cacheMock.return_value = directory

      cacheManager = CacheDataManager('app')
      self.assertEqual(cacheManager.getRecentFiles(), [])
      cacheManager.addRecentFile('a')
      cacheManager.addRecentFile('b')
      cacheManager.addRecentFile('c')
      cacheManager.addRecentFile('d')
      cacheManager.addRecentFile('e')
      cacheManager.addRecentFile('f')
      cacheManager.addRecentFile('g')
      cacheManager.addRecentFile('h')
      cacheManager.addRecentFile('i')
      cacheManager.addRecentFile('j')
      cacheManager.addRecentFile('k')
      cacheManager.addRecentFile('a')
      cacheManager.addRecentFile('i')
      self.assertEqual(cacheManager.getRecentFiles(), ['i', 'a', 'k', 'j', 'h', 'g', 'f', 'e', 'd', 'c'])

      cacheManager = CacheDataManager('app')
      self.assertEqual(cacheManager.getRecentFiles(), ['i', 'a', 'k', 'j', 'h', 'g', 'f', 'e', 'd', 'c'])

      didRemove = cacheManager.removeRecentFile('a')
      self.assertTrue(didRemove)
      self.assertEqual(cacheManager.getRecentFiles(), ['i', 'k', 'j', 'h', 'g', 'f', 'e', 'd', 'c'])

      didRemove = cacheManager.removeRecentFile('z')
      self.assertFalse(didRemove)
      self.assertEqual(cacheManager.getRecentFiles(), ['i', 'k', 'j', 'h', 'g', 'f', 'e', 'd', 'c'])

      cacheManager.clearRecentFiles()
      self.assertEqual(cacheManager.getRecentFiles(), [])

  def test_images(self):
    with tempfile.TemporaryDirectory() as directory, patch('platformdirs.user_cache_dir') as cacheMock:
      cacheMock.return_value = directory

      cacheManager = CacheDataManager('app')
      self.assertEqual(cacheManager.getRecentImages(), [])
      self.assertEqual(cacheManager.getLastImage(), None)
      cacheManager.addRecentImage('a')
      cacheManager.addRecentImage('b')
      cacheManager.addRecentImage('c')
      cacheManager.addRecentImage('d')
      cacheManager.addRecentImage('e')
      cacheManager.addRecentImage('f')
      cacheManager.addRecentImage('g')
      cacheManager.addRecentImage('h')
      cacheManager.addRecentImage('i')
      cacheManager.addRecentImage('j')
      cacheManager.addRecentImage('k')
      cacheManager.addRecentImage('a')
      cacheManager.addRecentImage('i')
      self.assertEqual(cacheManager.getRecentImages(), ['i', 'a', 'k', 'j', 'h', 'g', 'f', 'e', 'd', 'c'])
      self.assertEqual(cacheManager.getLastImage(), 'i')

      cacheManager = CacheDataManager('app')
      self.assertEqual(cacheManager.getRecentImages(), ['i', 'a', 'k', 'j', 'h', 'g', 'f', 'e', 'd', 'c'])
      self.assertEqual(cacheManager.getLastImage(), 'i')

      didRemove = cacheManager.removeRecentImage('a')
      self.assertTrue(didRemove)
      self.assertEqual(cacheManager.getRecentImages(), ['i', 'k', 'j', 'h', 'g', 'f', 'e', 'd', 'c'])
      self.assertEqual(cacheManager.getLastImage(), 'i')

      didRemove = cacheManager.removeRecentImage('z')
      self.assertFalse(didRemove)
      self.assertEqual(cacheManager.getRecentImages(), ['i', 'k', 'j', 'h', 'g', 'f', 'e', 'd', 'c'])
      self.assertEqual(cacheManager.getLastImage(), 'i')

      didRemove = cacheManager.removeRecentImage('i')
      self.assertTrue(didRemove)
      self.assertEqual(cacheManager.getRecentImages(), ['k', 'j', 'h', 'g', 'f', 'e', 'd', 'c'])
      self.assertEqual(cacheManager.getLastImage(), None)

      cacheManager.addRecentImage('a')
      self.assertEqual(cacheManager.getLastImage(), 'a')
      cacheManager.clearLastImage()
      self.assertEqual(cacheManager.getLastImage(), None)
      cacheManager.clearLastImage()
      self.assertEqual(cacheManager.getLastImage(), None)

      cacheManager.addRecentImage('a')
      self.assertEqual(cacheManager.getLastImage(), 'a')
      cacheManager.clearRecentImages()
      self.assertEqual(cacheManager.getRecentImages(), [])
      self.assertEqual(cacheManager.getLastImage(), None)

  def test_invalidCacheFileData(self):
    with tempfile.TemporaryDirectory() as directory, patch('platformdirs.user_cache_dir') as cacheMock:
      cacheMock.return_value = directory
      cacheDataFilepath = os.path.join(directory, 'cacheData.json')
      with open(cacheDataFilepath, 'w') as file:
        invalidData = {
          'recentFiles': ['a', 42],
          'recentImages': 42,
          'lastImage': []
        }
        json.dump(invalidData, file)
      cacheManager = CacheDataManager('app')
      self.assertEqual(cacheManager.getRecentFiles(), [])
      self.assertEqual(cacheManager.getRecentImages(), [])
      self.assertEqual(cacheManager.getLastImage(), None)

  def test_invalidCacheFile(self):
    with patch('platformdirs.user_cache_dir') as cacheMock:
      # The cache filepath is made invalid from forbidden characters in its parent directory name.
      cacheMock.return_value = 'forbidden/*?<>:'
      cacheManager = CacheDataManager('app')
      self.assertEqual(cacheManager.getRecentFiles(), [])
      cacheManager.addRecentFile('a')
      self.assertEqual(cacheManager.getRecentFiles(), ['a'])

      cacheManager = CacheDataManager('app')
      self.assertEqual(cacheManager.getRecentFiles(), [])

if __name__ == '__main__':
  unittest.main()
