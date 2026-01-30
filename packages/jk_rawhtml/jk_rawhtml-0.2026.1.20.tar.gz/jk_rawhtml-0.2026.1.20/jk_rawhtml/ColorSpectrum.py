


from .Color import *



class ColorSpectrum(list):

	def __init__(self, name, *colorOrListOfColors):
		super().__init__(self)

		self.name = name

		if isinstance(colorOrListOfColors, Color):
			self.append(colorOrListOfColors)
		else:
			for c in colorOrListOfColors:
				assert isinstance(c, Color)
				self.append(c)
	#

	def getColor(self, f:float, bRaiseExceptionOnInvalidValue:bool = False):
		if bRaiseExceptionOnInvalidValue:
			if (f < 0) or (f > 1):
				raise Exception("Invalid value specified: " + repr(f))
		else:
			if f < 0:
				f = 0
			elif f > 1:
				f = 1

		if len(self) == 0:
			return Color.BLACK
		if len(self) == 1:
			return self[0]
		if f == 0:
			return self[0]
		if f == 1:
			return self[-1]

		f = f * (len(self) - 1)
		i = int(f)
		f = f - i

		c1 = self[i]
		c2 = self[i + 1]
		r = f * c2.r + (1 - f) * c1.r
		g = f * c2.g + (1 - f) * c1.g
		b = f * c2.b + (1 - f) * c1.b

		return Color(r, g, b)
	#

	def reversed(self):
		return ColorSpectrum(self[::-1])
	#

#



ColorSpectrum.RED_GREEN_BLUE_YELLOW_PINK_CYAN = ColorSpectrum(
	"RED_GREEN_BLUE_YELLOW_PINK_CYAN",
	Color.RED,
	Color.GREEN,
	Color.BLUE,
	Color.YELLOW,
	Color.PINK,
	Color.CYAN
)

ColorSpectrum.GREEN_BLUE_RED = ColorSpectrum(
	"GREEN_BLUE_RED",
	Color.GREEN,
	Color.BLUE,
	Color.RED,
)

ColorSpectrum.RED_BLUE_GREEN = ColorSpectrum(
	"RED_BLUE_GREEN",
	Color.RED,
	Color.BLUE,
	Color.GREEN,
)

ColorSpectrum.RED_GREEN_BLUE = ColorSpectrum(
	"RED_GREEN_BLUE",
	Color.RED,
	Color.GREEN,
	Color.BLUE,
)

ColorSpectrum.BLACK_BLUE_GREEN_RED_LRED = ColorSpectrum(
	"BLACK_BLUE_GREEN_RED_LRED",
	Color.BLACK,
	Color.BLUE,
	Color.GREEN,
	Color.RED,
	Color.LIGHT_RED,
)

ColorSpectrum.BLACK_WHITE = ColorSpectrum(
	"BLACK_WHITE",
	Color.BLACK,
	Color.WHITE,
)

ColorSpectrum.BLACK_RED = ColorSpectrum(
	"BLACK_RED",
	Color.BLACK,
	Color.RED,
)

ColorSpectrum.BLACK_GREEN = ColorSpectrum(
	"BLACK_GREEN",
	Color.BLACK,
	Color.GREEN,
)

ColorSpectrum.BLACK_BLUE = ColorSpectrum(
	"BLACK_BLUE",
	Color.BLACK,
	Color.BLUE,
)

ColorSpectrum.BLACK_RED_WHITE = ColorSpectrum(
	"BLACK_RED_WHITE",
	Color.BLACK,
	Color.RED,
	Color.WHITE,
)

ColorSpectrum.BLACK_GREEN_WHITE = ColorSpectrum(
	"BLACK_GREEN_WHITE",
	Color.BLACK,
	Color.GREEN,
	Color.WHITE,
)

ColorSpectrum.BLACK_BLUE_WHITE = ColorSpectrum(
	"BLACK_BLUE_WHITE",
	Color.BLACK,
	Color.BLUE,
	Color.WHITE,
)

ColorSpectrum.RAINBOW = ColorSpectrum(
	"RAINBOW",
	Color.BLACK,
	Color.RED,
	Color.YELLOW,
	Color.GREEN,
	Color.CYAN,
	Color.BLUE,
	Color.DARK_PINK,
	Color.BLACK,
)

ColorSpectrum.RAINBOW_REVERSED = ColorSpectrum(
	"RAINBOW_REVERSED",
	Color.BLACK,
	Color.DARK_PINK,
	Color.BLUE,
	Color.CYAN,
	Color.GREEN,
	Color.YELLOW,
	Color.RED,
	Color.BLACK,
)

ColorSpectrum.ALL = [
	ColorSpectrum.RED_GREEN_BLUE_YELLOW_PINK_CYAN,
	ColorSpectrum.GREEN_BLUE_RED,
	ColorSpectrum.RED_BLUE_GREEN,
	ColorSpectrum.RED_GREEN_BLUE,
	ColorSpectrum.BLACK_BLUE_GREEN_RED_LRED,
	ColorSpectrum.RED_GREEN_BLUE,
	ColorSpectrum.BLACK_WHITE,
	ColorSpectrum.BLACK_RED,
	ColorSpectrum.BLACK_GREEN,
	ColorSpectrum.BLACK_BLUE,
	ColorSpectrum.BLACK_RED_WHITE,
	ColorSpectrum.BLACK_GREEN_WHITE,
	ColorSpectrum.BLACK_BLUE_WHITE,
	ColorSpectrum.RAINBOW,
	ColorSpectrum.RAINBOW_REVERSED,
]






