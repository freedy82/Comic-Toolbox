from enum import Enum

class ScrollFlow(Enum):
	LEFT_RIGHT = 1
	UP_DOWN = 2

class PageFit(Enum):
	HEIGHT = 1
	WIDTH = 2
	BOTH = 3
	WIDTH_FREE = 4

class PageMode(Enum):
	SINGLE = 1
	DOUBLE = 2
	TRIPLE = 3
	QUADRUPLE = 4

class PageFlow(Enum):
	LEFT_TO_RIGHT = 1
	RIGHT_TO_LEFT = 2

class PageRotate(Enum):
	ROTATE_0 = 0
	ROTATE_90 = 90
	ROTATE_180 = 180
	ROTATE_270 = 270

class PageRotateMode(Enum):
	MEMORY = 1
	FILE = 2

