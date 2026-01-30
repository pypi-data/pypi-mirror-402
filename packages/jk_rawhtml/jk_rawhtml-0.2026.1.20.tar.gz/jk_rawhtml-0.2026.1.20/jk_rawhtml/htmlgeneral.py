


import re



HTML_TAG_TYPE_STRUCTURE = 1
HTML_TAG_TYPE_INLINE_CONTENT = 2
HTML_TAG_TYPE_INLINE_ALL = 3

HTML_CLOSING_TAG_NEVER = False
HTML_CLOSING_TAG_ALWAYS = True
HTML_CLOSING_TAG_MAYBE = None




_HTML_ESCAPE_TABLE = {
	"&": "&amp;",
	"\"": "&quot;",
	"'": "&apos;",
	">": "&gt;",
	"<": "&lt;",
}

"""
OLD version

def htmlEscape_org(text:str):
	return "".join(_HTML_ESCAPE_TABLE.get(c, c) for c in text)
#
"""

def _htmlEscape0(text:str):
	return "".join(_HTML_ESCAPE_TABLE.get(c, c) for c in text)
#

def htmlEscape(text:str):
	n = 0
	ret = []
	for m in re.finditer(r"(&#\d+;)|(&[A-Za-z][A-Za-z0-9]*;)", text):
		n2, n3 = m.span()
		ret.append(_htmlEscape0(text[n:n2]))
		ret.append(text[n2:n3])
		n = n3
	ret.append(text[n:])
	return "".join(ret)
#





