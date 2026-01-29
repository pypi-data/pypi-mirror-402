from enum import StrEnum, unique


@unique
class PreprocessingType(StrEnum):
  """
  Available preprocessing types.
  """
  GRAYSCALE = 'grayscale'
  COLOR_MAP = 'colorMap'
  THRESHOLD = 'threshold'
  RESIZE = 'resize'
