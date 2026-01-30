


class Color(object):

	def __init__(self, r:float, g:float, b:float):
		self.r = r
		self.g = g
		self.b = b
	#

	def __repr__(self):
		return "Color(%0.2f, %0.2f, %0.2f)" % (self.r, self.g, self.b)
	#

	def __str__(self):
		return "Color(%0.2f, %0.2f, %0.2f)" % (self.r, self.g, self.b)
	#

	def toHTML(self):
		r, g, b = self.toRGB()
		return "#%0.2x%0.2x%0.2x" % (r, g, b)
	#

	def toRGB(self):
		if not isinstance(self.g, (int, float)) or (self.r < 0) or (self.r > 1):
			raise Exception("Red value must be a valid float value in the range [0..1]! (Value specified: " + str(self.r) + ")")
		if not isinstance(self.g, (int, float)) or (self.g < 0) or (self.g > 1):
			raise Exception("Green value must be a valid float value in the range [0..1]! (Value specified: " + str(self.g) + ")")
		if not isinstance(self.g, (int, float)) or (self.b < 0) or (self.b > 1):
			raise Exception("Blue value must be a valid float value in the range [0..1]! (Value specified: " + str(self.b) + ")")

		return int(round(self.r * 255)), int(round(self.g * 255)), int(round(self.b * 255))
	#

	def toConsoleBackGround(self):
		r, g, b = self.toRGB()

		return "\033[48;2;" + str(r) + ";" + str(g) + ";" + str(b) + "m"
	#

	def toConsoleForeGround(self):
		r, g, b = self.toRGB()

		return "\033[38;2;" + str(r) + ";" + str(g) + ";" + str(b) + "m"
	#

	@staticmethod
	def mix(*args):
		n = len(args)
		if n <= 1:
			raise Exception("Two or more color values required!")
		r = 0
		g = 0
		b = 0
		for c in args:
			r += c.r
			g += c.g
			b += c.b
		return Color(r / n, g / n, b / n)
	#

#



Color.CONSOLE_RESET_FG = "\033[39m"
Color.CONSOLE_RESET_BG = "\033[49m"

Color.BLACK = Color(0, 0, 0)
Color.DARK_GRAY = Color(0.25, 0.25, 0.25)
Color.GRAY = Color(0.5, 0.5, 0.5)
Color.LIGHT_GRAY = Color(0.75, 0.75, 0.75)
Color.WHITE = Color(1, 1, 1)

Color.DARK_RED = Color(0.5, 0, 0)
Color.DARK_GREEN = Color(0, 0.5, 0)
Color.DARK_BLUE = Color(0, 0, 0.5)

Color.DARK_YELLOW = Color(0.5, 0.5, 0)
Color.DARK_CYAN = Color(0, 0.5, 0.5)
Color.DARK_PINK = Color(0.5, 0, 0.5)

Color.LIGHT_CYAN = Color(0.5, 1, 1)
Color.LIGHT_PINK = Color(1, 0.5, 1)
Color.LIGHT_YELLOW = Color(1, 1, 0.5)

Color.LIGHT_BLUE = Color(0.5, 0.5, 1)
Color.LIGHT_RED = Color(1, 0.5, 0.5)
Color.LIGHT_GREEN = Color(0.5, 1, 0.5)

Color.BLUE = Color(0, 0, 1)
Color.RED = Color(1, 0, 0)
Color.GREEN = Color(0, 1, 0)

Color.CYAN = Color(0, 1, 1)
Color.PINK = Color(1, 0, 1)
Color.YELLOW = Color(1, 1, 0)



Color.DARK_ORANGE = Color(0.5, 0.25, 0)
Color.ORANGE = Color(1, 0.5, 0)





