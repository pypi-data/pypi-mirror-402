from guirecognizer.action_type import ActionType, SelectionType
from guirecognizer.common import RecognizerValueError
from guirecognizer.mouse_helper import MouseHelper
from guirecognizer.preprocessing import (ColorMapMethod, ColorMapPreprocessor,
                                         GrayscalePreprocessor, Preprocessing,
                                         ResizeMethod, ResizePreprocessor,
                                         ThresholdMethod,
                                         ThresholdPreprocessor, ThresholdType)
from guirecognizer.preprocessing_type import PreprocessingType
from guirecognizer.recognizer import OcrType, Recognizer

"""A library to help recognize some patterns on screen and make GUI actions."""

__version__ = "0.1.1"
