

from jk_hwriter import HWriter

from .htmlgeneral import *
from .CSSStyleGroup import CSSStyleGroup




class HTMLStyleElement(object):

	def __init__(self, styleOrStyles):
		if isinstance(styleOrStyles, CSSStyleGroup):
			self.styles = [ styleOrStyles ]
		elif isinstance(styleOrStyles, str):
			self.styles = [ CSSStyleGroup.parse(styleOrStyles) ]
		else:
			self.styles = []
			for element in styleOrStyles:
				if isinstance(element, CSSStyleGroup):
					self.styles.append(element)
				elif isinstance(element, str):
					self.styles.append(CSSStyleGroup.parse(element))
				else:
					raise TypeError()
	#

	def __call__(self):
		return self
	#

	def __getitem__(self, styleOrStyles):
		# print(">", styleOrStyles, repr(styleOrStyles))
		if hasattr(type(styleOrStyles), "__iter__"):
			self.styles.extend(styleOrStyles)
		else:
			self.styles.append(styleOrStyles)
		return self
	#

	def _serialize(self, w:HWriter):
		if self.styles:
			w.lineBreak()
			w.writeLn("<style type=\"text/css\">")
			w.incrementIndent()
			for style in self.styles:
				style._serialize(w)
			w.decrementIndent()
			w.writeLn("</style>")
	#

#
