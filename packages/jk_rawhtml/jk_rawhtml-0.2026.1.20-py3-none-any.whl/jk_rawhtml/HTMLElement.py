


from jk_hwriter import HWriter

from .htmlgeneral import *
from .CSSMap import CSSMap





class HTMLElement(object):

	def __init__(self, proto, name:str):
		self.name = name
		self.attributes = {}
		self.children = []
		self._proto = proto			# this is _HTMLElementProto; we cant's specify this as otherwise we'd create circular dependencies
	#

	def addAttributes(self, **attrs):
		for k, v in attrs.items():
			if k.startswith("_"):
				self.attributes[k[1:]] = v
			else:
				self.attributes[k] = v
		return self
	#

	def addContent(self, *args):
		self.children.extend(args)
		return self
	#

	"""
	def addChildren(self, *args):
		self.children.extend(args)
		return self
	#
	"""

	def __call__(self, **attrs):
		assert not self.attributes
		for k, v in attrs.items():
			if k.startswith("_"):
				self.attributes[k[1:]] = v
			else:
				self.attributes[k] = v
		return self
	#

	def __getitem__(self, childOrChildren):
		if hasattr(type(childOrChildren), "__iter__"):
			for c1 in childOrChildren:
				if hasattr(type(c1), "__iter__"):
					for c2 in c1:
						if hasattr(type(c2), "__iter__"):
							self.children.extend(c2)
						else:
							self.children.append(c2)
				else:
					self.children.append(c1)
		else:
			self.children.append(childOrChildren)
		return self
	#

	def _openingTagData(self):
		ret = [ "<", self.name ]
		self._attrsToStr(ret)
		ret.append(">")
		return ret
	#

	def _attrsToStr(self, ret:list):
		for k, v in self.attributes.items():
			if v is None:
				continue

			if k == "style":
				if isinstance(v, str):
					v = v.strip()
					if v:
						ret.extend((" style=\"", v, "\""))
				elif isinstance(v, CSSMap):
					if v:
						ret.extend((" style=\"", str(v), "\""))
				elif isinstance(v, dict):
					if v:
						_ruleset = CSSMap(**v)
						ret.extend((" style=\"", str(_ruleset), "\""))
				else:
					raise Exception("Unexpected value specified for HTML tag attribute '" + k + "': type " + str(type(v)) + ", value " + repr(v))

			elif k == "class":
				if isinstance(v, str):
					ret.extend((" ", k, "=\"", htmlEscape(v), "\""))
				elif isinstance(v, list):
					_xList = []
					for x in v:
						if not x:
							continue
						assert isinstance(x, str)
						if x not in _xList:
							_xList.append(x)
					if _xList:
						ret.extend((" ", k, "=\"", htmlEscape(" ".join(_xList)), "\""))
				else:
					raise Exception("Unexpected value specified for HTML tag attribute '" + k + "': type " + str(type(v)) + ", value " + repr(v))

			else:
				if isinstance(v, (int, float)):
					ret.extend((" ", k, "=\"", str(v), "\""))
				elif isinstance(v, str):
					ret.extend((" ", k, "=\"", htmlEscape(v), "\""))
				elif v is None:
					ret.extend((" ", k, "=\"\""))
				else:
					raise Exception("Unexpected value specified for HTML tag attribute '" + k + "': type " + str(type(v)) + ", value " + repr(v))
	#

	def _closingTagData(self):
		return [ "</", self.name, ">" ]
	#

	def __str__(self):
		w = HWriter()
		self._serialize(w)
		return str(w)
	#

	def _serialize(self, w:HWriter):
		if self._proto.bLineBreakOuter:
			w.lineBreak()
		w.write(self._openingTagData())

		bHasClosingTag = self._proto.bHasClosingTag
		if bHasClosingTag is HTML_CLOSING_TAG_MAYBE:
			bHasClosingTag = len(self.children) > 0

		if bHasClosingTag:
			w.incrementIndent()
			if self._proto.bLineBreakInner:
				if self.children:
					w.lineBreak()
					for child in self.children:
						if isinstance(child, (int, float, str)):
							w.write(htmlEscape(str(child)))
						else:
							child._serialize(w)
					w.lineBreak()
			else:
				for child in self.children:
					if isinstance(child, (int, float, str)):
						w.write(htmlEscape(str(child)))
					else:
						child._serialize(w)

			w.decrementIndent()
			w.write(self._closingTagData())

		else:
			if len(self.children) > 0:
				raise Exception("HTML tag \"" + self.name + "\" is not allowed to have child elements!")

		if self._proto.bLineBreakOuter:
			w.lineBreak()
	#

#





