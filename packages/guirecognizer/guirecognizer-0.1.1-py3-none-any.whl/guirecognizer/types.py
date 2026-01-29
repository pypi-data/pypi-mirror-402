from typing import Annotated

PointCoord = tuple[int, int] | Annotated[list[int], 2]
AreaCoord = tuple[int, int, int, int] | Annotated[list[int], 4]
Coord = PointCoord | AreaCoord
PointRatios = tuple[float | int, float | int] | Annotated[list[float | int], 2]
AreaRatios = tuple[float | int, float | int, float | int, float | int] | Annotated[list[float | int], 4]
Ratios = PointRatios | AreaRatios
PixelColor = tuple[int, int, int] | Annotated[list[int], 3]
