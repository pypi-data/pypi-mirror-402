from dataclasses import dataclass
from typing import List, Any

@dataclass
class TextBlock:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float

@dataclass
class ImageBlock:
    x0: float
    y0: float
    x1: float
    y1: float
    width: float
    height: float

@dataclass
class TableBlock:
    data: List[List[Any]]
    bbox: List[float]
