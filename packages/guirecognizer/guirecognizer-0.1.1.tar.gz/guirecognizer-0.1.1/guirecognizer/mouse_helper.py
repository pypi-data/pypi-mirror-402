import time

import pyautogui

from guirecognizer.types import PointCoord


class MouseHelper:
  """
  Helper for mouse actions.
  """

  @classmethod
  def clickOnPosition(cls, xy: tuple[int, int], pauseDuration: float=0.02, nbClicks: int=1) -> None:
    """
    :param xy:
    :param pauseDuration: (optional) pause duration of the click in second - default: 0.02
    :param nbClicks: (optional) number of clicks - default: 1
    """
    previousPause = pyautogui.PAUSE
    pyautogui.moveTo(xy)
    pyautogui.PAUSE = pauseDuration
    for _ in range(nbClicks):
      pyautogui.click()
    pyautogui.PAUSE = previousPause

  @classmethod
  def dragCoords(cls, coords: tuple[PointCoord, ...] | list[PointCoord], pauseDuration: float=0.1, moveDuration: float=0.25) -> None:
    """
    :param coords:
    :param pauseDuration: (optional) pause duration at the beginning and end of the drag - default: 0.01
    :param moveDuration: (optional) move duration between two coordinates - default: 0.25
    """
    for i, coord in enumerate(coords):
      if i == 0:
        pyautogui.moveTo(coord)
        pyautogui.mouseDown();
        time.sleep(pauseDuration)
      else:
        pyautogui.moveTo(coord[0], coord[1], moveDuration)
      if i == len(coords) - 1:
        time.sleep(pauseDuration)
        pyautogui.mouseUp();
