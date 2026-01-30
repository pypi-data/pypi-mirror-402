


import re
import typing

from jk_hwriter import HWriter

from .CSSMap import CSSMap








class CSSStyleGroup(object):

	################################################################################################################################
	## Constructor
	################################################################################################################################

	#
	# Constructor method.
	#
	def __init__(self, selectors:str, ruleset:typing.Union[dict,CSSMap] = None, **kwargs):
		assert isinstance(selectors, str)
		selectors = selectors.strip()
		assert selectors

		self.selectors = selectors

		if ruleset is None:
			ruleset = CSSMap(**kwargs)
		else:
			if isinstance(ruleset, dict):
				for k, v in ruleset.items():
					assert isinstance(k, str)
			else:
				assert isinstance(ruleset, CSSMap)
		self.ruleset = ruleset
	#

	################################################################################################################################
	## Public Properties
	################################################################################################################################

	################################################################################################################################
	## Helper Methods
	################################################################################################################################

	################################################################################################################################
	## Public Methods
	################################################################################################################################

	def __bool__(self):
		if not self.selectors:
			return False
		if not self.ruleset:
			return False
		return True
	#

	def _serialize(self, w:HWriter):
		w.writeLn(self.selectors + " {")
		w.incrementIndent()
		for k in dir(self.ruleset):
			if k.startswith("__") or k.startswith("_CSSMap"):
				continue
			v = getattr(self.ruleset, k)
			k = k.replace("_", "-")
			if v:
				w.writeLn(k + ": " + str(v) + ";")
		w.decrementIndent()
		w.writeLn("}")
	#

	@staticmethod
	def parse(someString:str):
		someString = someString.strip()

		n1 = someString.find("{")
		if n1 <= 0:
			raise SyntaxError(someString)
		if not someString.endswith("}"):
			raise SyntaxError(someString)

		selector = someString[:n1].strip()
		sGroup = someString[n1+1:-1].strip()
		groupLines = re.split(";|\n", sGroup)

		data = {}
		for groupLine in groupLines:
			groupLine = groupLine.strip()

			if groupLine:
				n2 = groupLine.find(":")
				if n2 <= 0:
					raise SyntaxError(groupLine)
				attrib = groupLine[:n2].strip()
				attrValue = groupLine[n2+1:].strip()
				if not attrib:
					raise SyntaxError(groupLine)
				if not attrValue:
					raise SyntaxError(groupLine)
				data[attrib.replace("-", "_")] = attrValue

		return CSSStyleGroup(selector, CSSMap(**data))
	#

#





