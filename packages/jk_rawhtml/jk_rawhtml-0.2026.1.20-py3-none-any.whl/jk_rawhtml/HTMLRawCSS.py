

from jk_hwriter import HWriter

from .htmlgeneral import *




class HTMLRawCSS(object):

	def __init__(self, textOrTextList):
		if isinstance(textOrTextList, str):
			self.texts = [ textOrTextList ]
		else:
			self.texts = list(textOrTextList)
	#

	def __call__(self, *attrs):
		self.texts.append("".join(attrs))
		return self
	#

	def __getitem__(self, textOrTexts):
		if hasattr(type(textOrTexts), "__iter__"):
			self.texts.extend(textOrTexts)
		else:
			self.texts.append(textOrTexts)
		return self
	#

	def _serialize(self, w:HWriter):
		if self.texts:
			w.lineBreak()
			w.writeLn("<style type=\"text/css\">")
			w.incrementIndent()
			for text in self.texts:
				w.writeLn(text)
			w.decrementIndent()
			w.writeLn("</style>")
	#

#
