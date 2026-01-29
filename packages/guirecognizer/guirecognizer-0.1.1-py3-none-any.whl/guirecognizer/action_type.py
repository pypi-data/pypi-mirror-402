from enum import Enum, Flag, auto, unique

from guirecognizer.types import Coord, Ratios


@unique
class SelectionType(Flag):
  """
  Available selection types.
  """

  POINT = auto()
  """
  Point selection to select a pixel.
  """
  AREA = auto()
  """
  Area selection to select a rectangle of pixels on the image.
  """
  POINT_OR_AREA = POINT | AREA
  """
  Point or area selection.
  """

  @classmethod
  def fromSelection(cls, selection: Coord | Ratios) -> 'SelectionType':
    """
    Return a SelectionType from a selection.

    param selection: either borders or ratios
    """
    if len(selection) == 2:
      return cls.POINT
    elif len(selection) == 4:
      return cls.AREA
    raise ValueError('Selection must be of length 2 or 4.')

  def isCompatibleWithSelectionType(self, selectionType: 'SelectionType') -> bool:
    """
    Return whether the selection type is compatible with this selection type.

    param selectionType:
    """
    return self == SelectionType.POINT or self.isRightSelectionType(selectionType)

  def isCompatibleWithSelection(self, selection: Coord | Ratios) -> bool:
    """
    Return whether the selection is compatible with this selection.

    param selection: either coordinates or ratios
    """
    return self.isCompatibleWithSelectionType(self.fromSelection(selection))

  def isRightSelectionType(self, selectionType: 'SelectionType') -> bool:
    """
    Return whether the selection type is a right one with this selection.

    param selectionType:
    """
    return bool(self & selectionType)

  def isRightSelection(self, selection: Coord | Ratios) -> bool:
    """
    Return whether the selection is has a right form with this selection.

    param selection: either coordinates or ratios
    """
    return self.isRightSelectionType(self.fromSelection(selection))

@unique
class ActionType(Enum):
  """
  Available action types.
  """

  COORDINATES = ('coordinates', SelectionType.POINT_OR_AREA)
  """
  Return the coordinates of a point or an area.
  """
  SELECTION = ('selection', SelectionType.POINT_OR_AREA)
  """
  Return point as a pixel or an area as an image.
  """
  FIND_IMAGE = ('findImage', SelectionType.AREA)
  """
  Find the locations of an image inside the selected area.
  Specify a detection threshold, the maximum number of locations and a resize interval to find the same image
  but a bit smaller or bigger.
  """
  CLICK = ('click', SelectionType.POINT_OR_AREA)
  """
  Click on the selected point.
  """
  PIXEL_COLOR = ('pixelColor', SelectionType.POINT_OR_AREA)
  """
  Compute the pixel color of the point selection or the average pixel color of the area selection.
  """
  COMPARE_PIXEL_COLOR = ('comparePixelColor', SelectionType.POINT_OR_AREA)
  """
  Compute the pixel color of the point selection or the average pixel color of the area selection
  then compute the difference with the pixel color in reference.

  The difference is the average difference of the rgb colors. It's always between 0 and 1.
  """
  IS_SAME_PIXEL_COLOR = ('isSamePixelColor', SelectionType.POINT_OR_AREA)
  """
  Compute the pixel color of the point selection or the average pixel color of the area selection
  and compare it to the pixel color in reference.
  """
  IMAGE_HASH = ('imageHash', SelectionType.AREA)
  """
  Compute the image hash of the area selection. The color is taken into account. Similar images generate close hashes.

  More about image hashes: https://pypi.org/project/ImageHash .
  """
  COMPARE_IMAGE_HASH = ('compareImageHash', SelectionType.AREA)
  """
  Compute the image hash of the area selection then compute the difference with the hash in reference.
  """
  IS_SAME_IMAGE_HASH = ('isSameImageHash', SelectionType.AREA)
  """
  Compute the image hash of the area selection and compare it to the hash in reference.
  """
  TEXT = ('text', SelectionType.AREA)
  """
  Try to recognize text. Return the empty string if no text has been recognized.
  """
  NUMBER = ('number', SelectionType.AREA)
  """
  Try to recognize a number. Return None if no number has been recognized.
  """

  selectionType: SelectionType

  def __new__(cls, value, selectionType: SelectionType) -> 'ActionType':
    """
    Custom Enum to manage action types.

    param value: automatically filled
    param selectionType: right selection type for this action
    """
    obj = object.__new__(cls)
    obj._value_ = value
    obj.selectionType = selectionType
    return obj

  def isCompatibleWithSelectionType(self, selectionType: SelectionType) -> bool:
    """
    Return whether this action can be used with the selection type.

    param selectionType:
    """
    return self.selectionType.isCompatibleWithSelectionType(selectionType)

  def isCompatibleWithSelection(self, selection: Coord | Ratios) -> bool:
    """
    Return whether this action can be used with the selection.

    param selection: either coordinates or ratios
    """
    return self.isCompatibleWithSelectionType(SelectionType.fromSelection(selection))
