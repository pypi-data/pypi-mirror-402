import logging
from abc import ABC, abstractmethod
from enum import StrEnum, unique
from typing import Any, Literal, TypedDict, TypeGuard, TypeIs, assert_never

import numpy as np
from PIL import Image, ImageOps

from guirecognizer.common import (RecognizerValueError, isIdDataValid,
                                  isImageDataValid, isPixelColorDataValid,
                                  isPixelColorDifferenceDataValid)
from guirecognizer.preprocessing_type import PreprocessingType
from guirecognizer.types import PixelColor

logger = logging.getLogger(__name__)

class Preprocessor(ABC):
  @abstractmethod
  def process(self, image: Image.Image) -> Image.Image:
    """
    :param image:
    """
    pass

  def checkImage(self, image):
    if not Preprocessing.isImageDataValid(image):
      raise RecognizerValueError('Invalid image to process value.')

class GrayscalePreprocessor(Preprocessor):
  """
  Grayscale the image.
  """

  def process(self, image: Image.Image) -> Image.Image:
    self.checkImage(image)
    return ImageOps.grayscale(image)

@unique
class ColorMapMethod(StrEnum):
  """
  Color mapping methods.
  """
  ONE_TO_ONE = 'oneToOne'
  RANGE_TO_ONE = 'rangeToOne'
  RANGE_TO_RANGE = 'rangeToRange'

class ColorMapData(TypedDict, total=False):
  method: ColorMapMethod | str
  inputColor1: PixelColor
  inputColor2: PixelColor
  difference: float
  outputColor1: PixelColor
  outputColor2: PixelColor

class ColorMapPreprocessor(Preprocessor):
  """
  Map a color or a range of colors to another color or a range of colors.
  """

  def __init__(self, method: ColorMapMethod | str=ColorMapMethod.ONE_TO_ONE, inputColor1: PixelColor=(255, 255, 255),
      inputColor2: PixelColor=(255, 255, 255), difference: float=0, outputColor1: PixelColor=(0, 0, 0),
      outputColor2: PixelColor=(0, 0, 0)):
    """
    :param colorMapMethod: (optional) default: one to one
    :param inputColor1: (optional) default: (255, 255, 255)
    :param inputColor2: (optional) default: (255, 255, 255)
    :param difference: (optional) default: 0
    :param outputColor1: (optional) default: (0, 0, 0)
    :param outputColor2: (optional) default: (0, 0, 0)
    :raise RecognizerValueError: invalid input
    """
    if self.isColorMapMethodDataValid(method):
      self.method = ColorMapMethod(method)
    else:
      raise RecognizerValueError('Invalid method value.')
    if not Preprocessing.isPixelColorDataValid(inputColor1):
      raise RecognizerValueError('Invalid inputColor1 value.')
    self.inputColor1 = inputColor1
    if self.method in [ColorMapMethod.RANGE_TO_ONE, ColorMapMethod.RANGE_TO_RANGE]:
      if not Preprocessing.isPixelColorDataValid(inputColor2):
        raise RecognizerValueError('Invalid inputColor2 value.')
      self.inputColor2 = inputColor2
    if not Preprocessing.isPixelColorDifferenceDataValid(difference):
      raise RecognizerValueError('Invalid difference value.')
    self.difference = difference
    if not Preprocessing.isPixelColorDataValid(outputColor1):
      raise RecognizerValueError('Invalid outputColor1 value.')
    self.outputColor1 = outputColor1
    if self.method is ColorMapMethod.RANGE_TO_RANGE:
      if not Preprocessing.isPixelColorDataValid(outputColor2):
        raise RecognizerValueError('Invalid outputColor2 value.')
      self.outputColor2 = outputColor2

  @classmethod
  def isColorMapMethodDataValid(cls, colorMapMethodData: Any) -> TypeGuard[ColorMapMethod | str]:
    """
    :param colorMapMethodData:
    """
    return isinstance(colorMapMethodData, str) and colorMapMethodData in [colorMapMethod.value for colorMapMethod in ColorMapMethod]

  def process(self, image: Image.Image) -> Image.Image:
    self.checkImage(image)
    match self.method:
      case ColorMapMethod.ONE_TO_ONE:
        return self._processOneToOne(image)
      case ColorMapMethod.RANGE_TO_ONE:
        return self._processRangeToOne(image)
      case ColorMapMethod.RANGE_TO_RANGE:
        return self._processRangeToRange(image)
      case _ as unreachable:
        assert_never(self.method)

  def _processOneToOne(self, image: Image.Image) -> Image.Image:
    """
    :param image:
    """
    npimage = np.array(image.convert('RGB'))
    input1 = np.array(self.inputColor1)
    output1 = np.array(self.outputColor1)

    threshold = self.difference * 255 * 3
    inThreshold = np.sum(np.abs(npimage - input1), axis=2) <= threshold
    npimage[inThreshold] = output1
    newImage = Image.fromarray(np.uint8(npimage))
    return newImage

  def _computeClosestColor(self, image: np.ndarray, input1: np.ndarray, input2: np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
    """
    :param image:
    :param input1:
    :param input2:
    """
    if np.array_equal(input1, input2):
      return input1, None

    # For each pixel of the given image, we compute the closest color on the line segment represented by the two input colors.
    # The closest color is the projection of the image color to the line segment.
    # It is parameterised by input1 + t * (input2 - input1)
    inputDistance = np.sum((input2 - input1) ** 2)
    t = np.clip(np.dot((image - input1), (input2 - input1)) / inputDistance, 0, 1)
    t = t.reshape(t.shape + (1,))
    closest = np.round(input1 + t * (input2 - input1))
    return closest, t

  def _processRangeToOne(self, image: Image.Image) -> Image.Image:
    """
    :param image:
    """
    npimage = np.array(image.convert('RGB'))
    closest, _ = self._computeClosestColor(npimage, np.array(self.inputColor1), np.array(self.inputColor2))
    threshold = self.difference * 255 * 3
    inThreshold = np.sum(np.abs(npimage - closest), axis=2) <= threshold
    npimage[inThreshold] = np.array(self.outputColor1)
    newImage = Image.fromarray(np.uint8(npimage))
    return newImage

  def _processRangeToRange(self, image: Image.Image) -> Image.Image:
    """
    :param image:
    """
    if self.outputColor1 == self.outputColor2:
      return self._processRangeToOne(image)

    npimage = np.array(image.convert('RGB'))
    closest, t = self._computeClosestColor(npimage, np.array(self.inputColor1), np.array(self.inputColor2))
    threshold = self.difference * 255 * 3
    inThreshold = np.sum(np.abs(npimage - closest), axis=2) <= threshold
    output1 = np.array(self.outputColor1)
    if t is None:
      npimage[inThreshold] = output1
    else:
      # The output color is computed using the parameter used to compute the closest input color.
      output2 = np.array(self.outputColor2)
      output = np.round(output1 + t * (output2 - output1))
      npimage[inThreshold] = output[inThreshold]
    newImage = Image.fromarray(np.uint8(npimage))
    return newImage

@unique
class ThresholdMethod(StrEnum):
  """
  Threshold methods.
  """
  SIMPLE = 'simple'
  ADAPTIVE_MEAN = 'adaptiveMean'
  ADAPTIVE_GAUSSIAN = 'adaptiveGaussian'
  OTSU = 'otsu'

@unique
class ThresholdType(StrEnum):
  """
  Threshold types.
  """
  BINARY = 'binary'
  BINARY_INVERSE = 'binaryInverse'
  TRUNCATE = 'truncate'
  TO_ZERO = 'toZero'
  TO_ZERO_INVERSE = 'toZeroInverse'

class ThresholdData(TypedDict, total=False):
  method: ThresholdMethod | str
  thresholdType: ThresholdType | str
  maxValue: int
  threshold: int
  blockSize: int
  cConstant: float

class ThresholdPreprocessor(Preprocessor):
  """
  Check OpenCV documentation about image thresholding.
  https://docs.opencv.org/4.7.0/d7/d4d/tutorial_py_thresholding.html
  """

  def __init__(self, method: ThresholdMethod | str=ThresholdMethod.SIMPLE, thresholdType: ThresholdType | str=ThresholdType.BINARY,
      maxValue: int=255, threshold: int=127, blockSize: int=11, cConstant: float=2.0):
    """
    :param method: (optional) default: simple
    :param thresholdType: (optional) default: binary
    :param maxValue: (optional) default: 255
    :param threshold: (optional) default: 127
    :param blockSize: (optional) default: 11
    :param cConstant: (optional) default: 2.0
    :raise RecognizerValueError: invalid input
    """
    if self.isThresholdMethodDataValid(method):
      self.method = ThresholdMethod(method)
    else:
      raise RecognizerValueError('Invalid method value.')
    if self.isThresholdTypeDataValid(thresholdType):
      self.thresholdType = ThresholdType(thresholdType)
    else:
      raise RecognizerValueError('Invalid thresholdType value.')
    if not self.isThresholdTypeCompatibleWithThresholdMethod(self.thresholdType, self.method):
      raise RecognizerValueError('Threshold method and type are incompatible.')

    match self.method:
      case ThresholdMethod.SIMPLE:
        if not self.isThresholdDataValid(threshold):
          raise RecognizerValueError('Invalid threshold value.')
        self.threshold = threshold
      case ThresholdMethod.ADAPTIVE_MEAN | ThresholdMethod.ADAPTIVE_GAUSSIAN:
        if not self.isBlockSizeDataValid(blockSize):
          raise RecognizerValueError('Invalid blockSize value')
        self.blockSize = blockSize
        if not self.isCConstantDataValid(cConstant):
          raise RecognizerValueError('Invalid cConstant value.')
        self.cConstant = cConstant
    if self.thresholdType in [ThresholdType.BINARY, ThresholdType.BINARY_INVERSE]:
      if not self.isMaxValueDataValid(maxValue):
        raise RecognizerValueError('Invalid maxValue value.')
      self.maxValue = maxValue

  @classmethod
  def isThresholdMethodDataValid(cls, methodData: Any) -> TypeGuard[ThresholdMethod | str]:
    """
    :param methodData:
    """
    return isinstance(methodData, str) and methodData in [method.value for method in ThresholdMethod]

  @classmethod
  def isThresholdTypeDataValid(cls, thresholdTypeData: Any) -> TypeGuard[ThresholdType | str]:
    """
    :param thresholdTypeData:
    """
    return isinstance(thresholdTypeData, str) and thresholdTypeData in [thresholdType.value for thresholdType in ThresholdType]

  @classmethod
  def isThresholdTypeCompatibleWithThresholdMethod(cls, thresholdType: ThresholdType, method: ThresholdMethod) -> bool:
    """
    :param thresholdType:
    :param method:
    """
    return (method != ThresholdMethod.ADAPTIVE_MEAN and method != ThresholdMethod.ADAPTIVE_GAUSSIAN) \
        or thresholdType in [ThresholdType.BINARY, ThresholdType.BINARY_INVERSE]

  @classmethod
  def isMaxValueDataValid(cls, maxValueData: Any) -> TypeGuard[int]:
    """
    :param maxValueData:
    """
    return isinstance(maxValueData, int) and 0 <= maxValueData and maxValueData <= 255

  @classmethod
  def isThresholdDataValid(cls, thresholdData: Any) -> TypeGuard[int]:
    """
    :param thresholdData:
    """
    return isinstance(thresholdData, int) and 0 <= thresholdData and thresholdData <= 255

  @classmethod
  def isBlockSizeDataValid(cls, blockSizeData: Any) -> TypeGuard[int]:
    """
    :param blockSizeData:
    """
    return isinstance(blockSizeData, int) and blockSizeData > 1 and blockSizeData % 2 == 1

  @classmethod
  def isCConstantDataValid(cls, cConstantData: Any) -> TypeGuard[int | float]:
    """
    :param cConstantData:
    """
    return isinstance(cConstantData, (int, float))

  def process(self, image: Image.Image) -> Image.Image:
    self.checkImage(image)

    import cv2 as cv

    # TODO: With some threshold type, could keep the color by using the generated image after threshold as a mask.
    #       It could be the default behavior since the user can always add a grayscale preprocessing.
    imageCv = np.array(ImageOps.grayscale(image))
    match self.thresholdType:
      case ThresholdType.BINARY:
        thresholdType = cv.THRESH_BINARY
      case ThresholdType.BINARY_INVERSE:
        thresholdType = cv.THRESH_BINARY_INV
      case ThresholdType.TRUNCATE:
        thresholdType = cv.THRESH_TRUNC
      case ThresholdType.TO_ZERO:
        thresholdType = cv.THRESH_TOZERO
      case ThresholdType.TO_ZERO_INVERSE:
        thresholdType = cv.THRESH_TOZERO_INV
      case _ as unreachable:
        assert_never(self.thresholdType)
    match self.method:
      case ThresholdMethod.SIMPLE | ThresholdMethod.OTSU:
        if self.thresholdType in [ThresholdType.BINARY, ThresholdType.BINARY_INVERSE]:
          maxValue = self.maxValue
        else:
          maxValue = 0
        if self.method == ThresholdMethod.OTSU:
          thresholdType += cv.THRESH_OTSU
          threshold = 0
        else:
          threshold = self.threshold
        _, newImageCv = cv.threshold(imageCv, threshold, maxValue, thresholdType)
      case ThresholdMethod.ADAPTIVE_MEAN | ThresholdMethod.ADAPTIVE_GAUSSIAN:
        match self.method:
          case ThresholdMethod.ADAPTIVE_MEAN:
            adaptiveType = cv.ADAPTIVE_THRESH_MEAN_C
          case ThresholdMethod.ADAPTIVE_GAUSSIAN:
            adaptiveType = cv.ADAPTIVE_THRESH_GAUSSIAN_C
          case _ as unreachable:
            assert_never(self.method)
        newImageCv = cv.adaptiveThreshold(imageCv, self.maxValue, adaptiveType, thresholdType, self.blockSize, self.cConstant)
      case _ as unreachable:
        assert_never(self.method)
    return Image.fromarray(newImageCv)

@unique
class ResizeMethod(StrEnum):
  """
  Resize methods.
  """
  UNFIXED_RATIO = 'unfixedRatio'
  FIXED_RATIO_WIDTH = 'fixedRatioWidth'
  """
  The height is computed from the width and the ratio width/height of the image to process.
  """
  FIXED_RATIO_HEIGHT = 'fixedRatioHeight'
  """
  The width is computed from the height and the ratio width/height of the image to process.
  """

class ResizeData(TypedDict, total=False):
  width: int
  height: int
  method: ResizeMethod | str

class ResizePreprocessor(Preprocessor):
  """
  Resize the image.
  """

  def __init__(self, width: int=100, height: int=100, method: ResizeMethod | str=ResizeMethod.UNFIXED_RATIO):
    """
    :param width: (optional) default: 100
    :param height: (optional) default: 100
    :param method: (optional) default: unfixed ratio
    :raise RecognizerValueError: invalid input
    """
    if self.isResizeMethodDataValid(method):
      self.method = ResizeMethod(method)
    else:
      raise RecognizerValueError('Invalid method value.')
    if self.method in [ResizeMethod.UNFIXED_RATIO, ResizeMethod.FIXED_RATIO_WIDTH]:
      if not self.isWidthOrHeightDataValid(width):
        raise RecognizerValueError('Invalid width value.')
      self.width = width
    if self.method in [ResizeMethod.UNFIXED_RATIO, ResizeMethod.FIXED_RATIO_HEIGHT]:
      if not self.isWidthOrHeightDataValid(height):
        raise RecognizerValueError('Invalid height value.')
      self.height = height

  @classmethod
  def isWidthOrHeightDataValid(cls, widthOrHeightData: Any) -> TypeGuard[int]:
    """
    :param widthOrHeightData:
    """
    return isinstance(widthOrHeightData, int) and 0 < widthOrHeightData

  @classmethod
  def isResizeMethodDataValid(cls, methodData: Any) -> TypeGuard[ResizeMethod | str]:
    """
    :param methodData:
    """
    return isinstance(methodData, str) and methodData in [method.value for method in ResizeMethod]

  def process(self, image: Image.Image) -> Image.Image:
    self.checkImage(image)
    match self.method:
      case ResizeMethod.FIXED_RATIO_WIDTH:
        self.height = max(round(image.size[1] / image.size[0] * self.width), 1)
      case ResizeMethod.FIXED_RATIO_HEIGHT:
        self.width = max(round(image.size[0] / image.size[1] * self.height), 1)
    return image.resize((self.width, self.height))

class OperationDict(TypedDict):
  id: str
  suboperations: list[Preprocessor]

class BaseSuboperationData(TypedDict):
  type: PreprocessingType

class GrayscaleSuboperationData(BaseSuboperationData):
  type: Literal[PreprocessingType.GRAYSCALE]

class ColorMapSuboperationData(BaseSuboperationData):
  type: Literal[PreprocessingType.COLOR_MAP]
  colorMap: ColorMapData

class ThresholdSuboperationData(BaseSuboperationData):
  type: Literal[PreprocessingType.THRESHOLD]
  threshold: ThresholdData

class ResizeSuboperationData(BaseSuboperationData):
  type: Literal[PreprocessingType.RESIZE]
  resize: ResizeData

SuboperationData = GrayscaleSuboperationData | ColorMapSuboperationData | ThresholdSuboperationData | ResizeSuboperationData

class OperationData(TypedDict):
  id: str
  suboperations: list[SuboperationData]

class PreprocessingData(TypedDict, total=False):
  operations: list[OperationData]

class Preprocessing:
  """
  Preprocess images.

  Can be used to load preprocessing operations (:class:`PreprocessingType`) defined in config data.
  """
  operationById: dict[str, OperationDict]

  def __init__(self, data: PreprocessingData | None=None) -> None:
    """
    :param data: (optional) config data
    :raise RecognizerValueError: invalid `data`
    """
    self.operationById = {}
    if isinstance(data, dict):
      self.loadData(data)
    elif data is not None:
      raise RecognizerValueError('Expect a dict as config data.')

  @classmethod
  def isIdDataValid(cls, idData: Any) -> TypeGuard[str]:
    """
    :param idData:
    """
    return isIdDataValid(idData)

  @classmethod
  def isImageDataValid(cls, imageData: Any) -> TypeIs[Image.Image]:
    """
    :param imageData:
    """
    return isImageDataValid(imageData)

  @classmethod
  def isTypeDataValid(cls, typeData: Any) -> TypeGuard[PreprocessingType]:
    """
    :param typeData:
    """
    return isinstance(typeData, str) and typeData in [preprocessingType.value for preprocessingType in PreprocessingType]

  @classmethod
  def isPixelColorDataValid(cls, pixelColorData: Any) -> TypeGuard[PixelColor]:
    """
    :param pixelColorData:
    """
    return isPixelColorDataValid(pixelColorData)

  @classmethod
  def isPixelColorDifferenceDataValid(cls, differenceData: Any) -> TypeGuard[int | float]:
    """
    :param differenceData:
    """
    return isPixelColorDifferenceDataValid(differenceData)

  def loadData(self, data: PreprocessingData) -> None:
    """
    Load actions.

    Can be called multiple times to load more data.

    :param data: config data
    :raise RecognizerValueError: invalid `data`
    """
    if 'operations' in data:
      if not isinstance(data['operations'], (list, tuple)):
        raise RecognizerValueError('Invalid preprocessing operations data: expects a list of preprocessing operations.')
      for operationData in data['operations']:
        if not isinstance(operationData, dict):
          raise RecognizerValueError('Invalid preprocessing operation data: every preprocessing operation data should be a dict.')
        self._addOperation(operationData)

  def clearAllData(self) -> None:
    """
    Remove all data.
    """
    self.operationById.clear()

  def _addOperation(self, data: OperationData) -> None:
    """
    Create a preprocessing operation and add it to the list of operations.

    The config data of the operations can have an operation not yet properly defined by the user.
    This is why invalid operation should be ignored with a warning and not trigger an error.
    Any operation with an invalid suboperation is also invalid and is ignored.

    :param data:
    :raise RecognizerValueError: invalid `data`
    """
    if 'id' in data and self.isIdDataValid(data['id']):
      operationId = data['id']
      if operationId in self.operationById:
        logger.warning(f'Operation id \'{operationId}\' is already used. This operation is ignored.')
        return
      operation: OperationDict = {'id': operationId, 'suboperations': []}
    else:
      logger.warning('Invalid operation id. This operation is ignored.')
      return

    if 'suboperations' not in data or not isinstance(data['suboperations'], (list, tuple)):
      raise RecognizerValueError('Invalid preprocessing suboperations data: expects a list of preprocessing suboperations.')
    for suboperationData in data['suboperations']:
      if not isinstance(suboperationData, dict):
        raise RecognizerValueError('Invalid preprocessing suboperation data: every preprocessing suboperation data should be a dict.')
      try:
        preprocessor = self._createPreprocessor(suboperationData)
      except RecognizerValueError as e:
        logger.warning(f'{str(e)} Operation \'{operationId}\' is ignored.')
        return
      operation['suboperations'].append(preprocessor)

    self.operationById[operation['id']] = operation

  def _isSuboperationDataMissing(self, preprocessingType: PreprocessingType, data: SuboperationData) -> bool:
    match preprocessingType:
      case PreprocessingType.COLOR_MAP:
        return 'colorMap' not in data or not isinstance(data['colorMap'], dict)
      case PreprocessingType.THRESHOLD:
        return 'threshold' not in data or not isinstance(data['threshold'], dict)
      case PreprocessingType.RESIZE:
        return 'resize' not in data or not isinstance(data['resize'], dict)
    return False

  def _createPreprocessor(self, data: SuboperationData) -> Preprocessor:
    """
    Create a preprocessing suboperation or preprocessor to be added to the list of suboperations of an operation.

    The config data of the operations can have a suboperation not yet properly defined by the user.
    This is why invalid suboperation should be ignored with a warning and not trigger an error.

    :param data:
    :raise RecognizerValueError: invalid `data`
    """
    if 'type' not in data or not self.isTypeDataValid(data['type']):
      raise RecognizerValueError('Invalid preprocessing type.')

    if self._isSuboperationDataMissing(PreprocessingType(data['type']), data):
      raise RecognizerValueError('Invalid suboperation data.')

    match data['type']:
      case PreprocessingType.GRAYSCALE:
        return GrayscalePreprocessor()
      case PreprocessingType.COLOR_MAP:
        return ColorMapPreprocessor(**data['colorMap'])
      case PreprocessingType.THRESHOLD:
        return ThresholdPreprocessor(**data['threshold'])
      case PreprocessingType.RESIZE:
        return ResizePreprocessor(**data['resize'])
      case _ as unreachable:
        assert_never(data['type'])

  def checkProcessInput(self, operationId: str) -> None:
    """
    :param operationId:
    :raise RecognizerValueError: invalid `operationId`
    """
    if not isinstance(operationId, str):
      raise RecognizerValueError(f'Expected an operation id instead of \'{operationId}\'.')
    if operationId not in self.operationById:
      raise RecognizerValueError(f'Id \'{operationId}\' is not in the list of available preprocessing operations.'
          ' Maybe it\'s a typo or the operation was ignored during the data loading because of an import issue.'
          ' You can check the logs for warnings about import issues.')

  def process(self, image: Image.Image, operationId: str) -> Image.Image:
    """
    :param image:
    :param operationId:
    :raise RecognizerValueError: invalid `operationId`
    """
    if not self.isImageDataValid(image):
      raise RecognizerValueError('Invalid image to process value.')
    self.checkProcessInput(operationId)
    operation = self.operationById[operationId]
    for preprocessor in operation['suboperations']:
      image = preprocessor.process(image)
    return image
