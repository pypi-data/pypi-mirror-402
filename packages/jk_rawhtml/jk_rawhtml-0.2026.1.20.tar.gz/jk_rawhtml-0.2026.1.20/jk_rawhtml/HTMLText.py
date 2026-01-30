

from jk_hwriter import HWriter

from .htmlgeneral import *




class HTMLText(object):

	def __init__(self, textOrTextList):
		if isinstance(textOrTextList, str):
			self.texts1 = [ textOrTextList ]
		else:
			self.texts1 = list(textOrTextList)
		self.texts2 = []
	#

	def __call__(self, **attrs):
		self.texts1.append("".join(attrs))
		return self
	#

	def __getitem__(self, textOrTexts):
		if hasattr(type(textOrTexts), "__iter__"):
			self.texts2.extend(textOrTexts)
		else:
			self.texts2.append(textOrTexts)
		return self
	#

	def _serialize(self, w:HWriter):
		if self.texts1:
			for text in self.texts1:
				w.lineBreak()
				w.write(self.__encodeText(text))
				w.lineBreak()
		for text in self.texts2:
			w.write(self.__encodeText(text))
	#

	def __encodeText(self, text:str) -> str:
		ret = []
		for c in text:
			if c == "<":
				ret.append("&lt;")
			elif c == ">":
				ret.append("&gt;")
			else:
				ret.append(c)
		return "".join(ret)
	#

#
