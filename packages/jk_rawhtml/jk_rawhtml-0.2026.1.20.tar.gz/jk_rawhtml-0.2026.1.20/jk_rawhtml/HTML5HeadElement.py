


from jk_hwriter import HWriter

from .HTMLElement import *




class HTML5HeadElement(HTMLElement):

	def __init__(self, proto, name):
		assert name == "head"
		super().__init__(proto, "head")
	#

	def __hasMetaTagWithCharset(self):
		for child in self.children:
			if isinstance(child, HTMLElement):
				if child.name == "meta":
					if "charset" in child.attributes:
						return True
		return False
	#

	def _serialize(self, w:HWriter):
		w.write(self._openingTagData())

		if self._proto.bHasClosingTag:
			w.incrementIndent()

			bRequireExtraCharsetTag = not self.__hasMetaTagWithCharset()
			if self.children or bRequireExtraCharsetTag:
				w.lineBreak()
				if bRequireExtraCharsetTag:
					w.writeLn("<meta charset=\"UTF-8\">")
				for child in self.children:
					if isinstance(child, (int, float, str)):
						w.write(htmlEscape(str(child)))
					else:
						child._serialize(w)
				w.lineBreak()

			w.decrementIndent()
			w.write(self._closingTagData())

		else:
			if len(self.children) > 0:
				raise Exception("HTML tag \"" + self.name + "\" is not allowed to have child elements!")

		w.lineBreak()
	#

#





