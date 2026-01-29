from typing import Any, TypeGuard, TypeIs

from PIL import Image

from guirecognizer.types import PixelColor


class RecognizerValueError(ValueError):
  """
  Exception for invalid config data or action or preprocessing operation options.
  """
  pass

def isIdDataValid(idData: Any) -> TypeGuard[str]:
  """
  :param idData:
  """
  return isinstance(idData, str) and bool(idData)

def isPixelColorDataValid(pixelColorData: Any) -> TypeGuard[PixelColor]:
  """
  :param pixelColorData:
  """
  return isinstance(pixelColorData, (list, tuple)) and len(pixelColorData) == 3 \
      and all(isinstance(i, int) and 0 <= i and i <= 255 for i in pixelColorData)

def isPixelColorDifferenceDataValid(differenceData: Any) -> TypeGuard[int | float]:
  """
  :param differenceData:
  """
  return isinstance(differenceData, (int, float)) and 0 <= differenceData and differenceData <= 1

def isImageDataValid(imageData: Any) -> TypeIs[Image.Image]:
  """
  :param imageData:
  """
  return isinstance(imageData, Image.Image) and imageData.width != 0 and imageData.height != 0
