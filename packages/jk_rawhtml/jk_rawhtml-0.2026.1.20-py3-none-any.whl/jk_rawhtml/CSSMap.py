





class CSSMap(object):

	################################################################################################################################
	## Constructor Method
	################################################################################################################################

	def __init__(self, **kwargs):
		for k, v in kwargs.items():
			setattr(self, k, v)
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	def __toStrE(self, k, v):
		if isinstance(v, (int, float)):
			return str(v)

		if isinstance(v, str):
			return v

		if hasattr(v, "toHTMLCSS"):
			m = getattr(v, "toHTMLCSS")
			if callable(m):
				return m()

		if hasattr(v, "toHTML"):
			m = getattr(v, "toHTML")
			if callable(m):
				return m()

		raise Exception("Unexpected value type specified for CSS attribute '" + k + "': type " + str(type(v)) + ", value " + repr(v))
	#

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	def __bool__(self):
		for k in dir(self):
			if k.startswith("__"):
				continue
			return True
		return False
	#

	def __str__(self):
		ret = []
		for k in dir(self):
			if k.startswith("__"):
				continue
			if k.startswith("_CSSMap__"):
				continue

			if len(ret) > 0:
				ret.append(" ")

			ret.append(k.replace("_", "-"))
			ret.append(":")

			v = getattr(self, k)
			ret.append(self.__toStrE(k, v))
				
			ret.append(";")
		return "".join(ret)
	#

#



