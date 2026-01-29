import unittest
from unittest.mock import patch

from guirecognizer import MouseHelper
from tests.test_utility import LoggedTestCase


class TestMouseManager(LoggedTestCase):
  def test_click(self):
    with patch('pyautogui.click') as clickMock, patch('pyautogui.moveTo') as moveToMock:
      MouseHelper.clickOnPosition((0, 0))
      moveToMock.assert_called_once()
      clickMock.assert_called_once()

  def test_click_pauseDuration(self):
    with patch('pyautogui.click') as clickMock, patch('pyautogui.moveTo') as moveToMock:
      MouseHelper.clickOnPosition((0, 0), pauseDuration=0.5)
      moveToMock.assert_called_once()
      clickMock.assert_called_once()

  def test_click_manyClicks(self):
    with patch('pyautogui.click') as clickMock, patch('pyautogui.moveTo') as moveToMock:
      MouseHelper.clickOnPosition((0, 0), nbClicks=10)
      moveToMock.assert_called_once()
      self.assertEqual(clickMock.call_count, 10)

  def test_dragCoords_noCoord(self):
    with patch('pyautogui.mouseDown') as mousDownMock, patch('pyautogui.mouseUp') as mousUpMock, patch('pyautogui.moveTo') as moveToMock:
      MouseHelper.dragCoords([])
      moveToMock.assert_not_called()
      mousDownMock.assert_not_called()
      mousUpMock.assert_not_called()

  def test_dragCoords_oneCoord(self):
    with patch('pyautogui.mouseDown') as mousDownMock, patch('pyautogui.mouseUp') as mousUpMock, patch('pyautogui.moveTo') as moveToMock:
      MouseHelper.dragCoords([(0, 0)])
      moveToMock.assert_called_once()
      mousDownMock.assert_called_once()
      mousUpMock.assert_called_once()

  def test_dragCoords_manyCoords(self):
    with patch('pyautogui.mouseDown') as mousDownMock, patch('pyautogui.mouseUp') as mousUpMock, patch('pyautogui.moveTo') as moveToMock:
      MouseHelper.dragCoords([(0, 0), (5, 5), (10, 20)])
      self.assertEqual(moveToMock.call_count, 3)
      mousDownMock.assert_called_once()
      mousUpMock.assert_called_once()

  def test_dragCoords_pauseDuration(self):
    with patch('pyautogui.mouseDown') as mousDownMock, patch('pyautogui.mouseUp') as mousUpMock, patch('pyautogui.moveTo') as moveToMock:
      MouseHelper.dragCoords([(0, 0), (5, 5), (10, 20)], pauseDuration=0.5)
      self.assertEqual(moveToMock.call_count, 3)
      mousDownMock.assert_called_once()
      mousUpMock.assert_called_once()

  def test_dragCoords_moveDuration(self):
    with patch('pyautogui.mouseDown') as mousDownMock, patch('pyautogui.mouseUp') as mousUpMock, patch('pyautogui.moveTo') as moveToMock:
      MouseHelper.dragCoords([(0, 0), (5, 5), (10, 20)], moveDuration=0.5)
      self.assertEqual(moveToMock.call_count, 3)
      mousDownMock.assert_called_once()
      mousUpMock.assert_called_once()

if __name__ == '__main__':
  unittest.main()
