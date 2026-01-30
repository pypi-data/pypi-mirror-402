


from jk_hwriter import HWriter

from .HTMLElement import *
from .HTML5HeadElement import HTML5HeadElement




class HTML5RootElement(HTMLElement):

	def __init__(self, proto, name):
		assert name == "html"
		super().__init__(proto, "html")
	#

	def _openingTagData(self):
		ret = [ "<!DOCTYPE html>\n<html" ]
		if "lang" not in self.attributes:
			ret.append(" lang=\"en\"")
		self._attrsToStr(ret)
		ret.append(">")
		return ret
	#

	def __hasHeadTag(self):
		for child in self.children:
			if isinstance(child, HTMLElement):
				if child.name == "head":
					return True
		return False
	#

	def _serialize(self, w:HWriter):
		w.write(self._openingTagData())

		if self._proto.bHasClosingTag:
			w.incrementIndent()

			if self.children:
				w.lineBreak()
				if not self.__hasHeadTag():
					head = HTML5HeadElement(self._proto, "head")
					head._serialize(w)
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





