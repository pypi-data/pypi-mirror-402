


import typing

from .htmlgeneral import *
from ._HTMLElementProto import _HTMLElementProto, HTMLElement
from ._HTMLCommentProto import _HTMLCommentProto, HTMLComment
from ._HTMLRawTextProto import _HTMLRawTextProto, HTMLRawText
from ._HTMLTextProto import _HTMLTextProto, HTMLText
from ._HTMLRawCSSProto import _HTMLRawCSSProto, HTMLRawCSS
from ._HTMLCSSProto import _HTMLCSSProto
from .HTML5RootElement import HTML5RootElement
from .HTML5HeadElement import HTML5HeadElement






HTML5Scope = typing.NewType("HTML5Scope", object)

class HTML5Scope(object):

	a =				_HTMLElementProto("a",													tagType=HTML_TAG_TYPE_INLINE_ALL)
	abbr =			_HTMLElementProto("abbr",												tagType=HTML_TAG_TYPE_INLINE_ALL)
	address =		_HTMLElementProto("address",											tagType=HTML_TAG_TYPE_STRUCTURE)
	area =			_HTMLElementProto("area", 		bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	article =		_HTMLElementProto("article",											tagType=HTML_TAG_TYPE_STRUCTURE)
	audio =			_HTMLElementProto("audio",												tagType=HTML_TAG_TYPE_STRUCTURE)
	b =				_HTMLElementProto("b",													tagType=HTML_TAG_TYPE_INLINE_ALL)
	big =			_HTMLElementProto("big",												tagType=HTML_TAG_TYPE_INLINE_ALL)
	base =			_HTMLElementProto("base", 		bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_INLINE_ALL)
	# bdi =			_HTMLElementProto("bdi",												tagType=XXXXX)
	# bdo =			_HTMLElementProto("bdo",												tagType=XXXXX)
	blockquote =	_HTMLElementProto("blockquote",											tagType=HTML_TAG_TYPE_STRUCTURE)
	body =			_HTMLElementProto("body",												tagType=HTML_TAG_TYPE_STRUCTURE)
	br =			_HTMLElementProto("br",			bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	button =		_HTMLElementProto("button",												tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	# canvas =		_HTMLElementProto("canvas",												tagType=XXXXX)
	caption =		_HTMLElementProto("caption",											tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	cite =			_HTMLElementProto("cite",												tagType=HTML_TAG_TYPE_INLINE_ALL)
	code =			_HTMLElementProto("code",												tagType=HTML_TAG_TYPE_STRUCTURE)
	col =			_HTMLElementProto("col", 		bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	colgroup =		_HTMLElementProto("colgroup",											tagType=HTML_TAG_TYPE_STRUCTURE)
	command =		_HTMLElementProto("command", 	bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_INLINE_ALL)
	data =			_HTMLElementProto("data",												tagType=HTML_TAG_TYPE_INLINE_ALL)
	datalist =		_HTMLElementProto("datalist",											tagType=HTML_TAG_TYPE_STRUCTURE)
	_del =			_HTMLElementProto("del",												tagType=HTML_TAG_TYPE_INLINE_ALL)			# problem
	details =		_HTMLElementProto("details",											tagType=HTML_TAG_TYPE_STRUCTURE)
	dfn =			_HTMLElementProto("dfn",												tagType=HTML_TAG_TYPE_INLINE_ALL)
	dl =			_HTMLElementProto("dl",													tagType=HTML_TAG_TYPE_STRUCTURE)
	dt =			_HTMLElementProto("dt",													tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	dd =			_HTMLElementProto("dd",													tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	div =			_HTMLElementProto("div",												tagType=HTML_TAG_TYPE_STRUCTURE)
	em =			_HTMLElementProto("em",													tagType=HTML_TAG_TYPE_INLINE_ALL)
	embed =			_HTMLElementProto("embed",		bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	fieldset =		_HTMLElementProto("fieldset",											tagType=HTML_TAG_TYPE_STRUCTURE)
	figcaption =	_HTMLElementProto("figcaption",											tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	figure =		_HTMLElementProto("figure",												tagType=HTML_TAG_TYPE_STRUCTURE)
	footer =		_HTMLElementProto("footer",												tagType=HTML_TAG_TYPE_STRUCTURE)
	form =			_HTMLElementProto("form",												tagType=HTML_TAG_TYPE_STRUCTURE)
	formInput =		_HTMLElementProto("input", 		bHasClosingTag=HTML_CLOSING_TAG_MAYBE,	tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	h1 =			_HTMLElementProto("h1",													tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	h2 =			_HTMLElementProto("h2",													tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	h3 =			_HTMLElementProto("h3",													tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	h4 =			_HTMLElementProto("h4",													tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	h5 =			_HTMLElementProto("h5",													tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	h6 =			_HTMLElementProto("h6",													tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	head =			_HTMLElementProto("head",												tagType=HTML_TAG_TYPE_STRUCTURE, implClass=HTML5HeadElement)
	header =		_HTMLElementProto("header",												tagType=HTML_TAG_TYPE_STRUCTURE)
	hr =			_HTMLElementProto("hr", 		bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_STRUCTURE)
	html =			_HTMLElementProto("html",												tagType=HTML_TAG_TYPE_STRUCTURE, implClass=HTML5RootElement)
	i =				_HTMLElementProto("i",													tagType=HTML_TAG_TYPE_INLINE_ALL)
	img =			_HTMLElementProto("img",		bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_INLINE_ALL)
	_input =		_HTMLElementProto("input",		bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_INLINE_CONTENT)			# problem
	ins =			_HTMLElementProto("ins",												tagType=HTML_TAG_TYPE_INLINE_ALL)
	# kbd =			_HTMLElementProto("kbd",												tagType=XXXXX)
	# keygen =		_HTMLElementProto("keygen",		bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=XXXXX)
	label =			_HTMLElementProto("label",		bHasClosingTag=HTML_CLOSING_TAG_ALWAYS,	tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	legend =		_HTMLElementProto("legend",												tagType=HTML_TAG_TYPE_STRUCTURE)
	li =			_HTMLElementProto("li",													tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	link =			_HTMLElementProto("link", 		bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	main =			_HTMLElementProto("main",												tagType=HTML_TAG_TYPE_STRUCTURE)
	_map =			_HTMLElementProto("map",												tagType=HTML_TAG_TYPE_STRUCTURE)			# problem
	mark =			_HTMLElementProto("mark",												tagType=HTML_TAG_TYPE_INLINE_ALL)
	# math =		_HTMLElementProto("math",												tagType=XXXXX)		# https://developer.mozilla.org/de/docs/Web/MathML/Element/math
	menu =			_HTMLElementProto("menu",												tagType=HTML_TAG_TYPE_STRUCTURE)
	menuitem =		_HTMLElementProto("menuitem",											tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	meta =			_HTMLElementProto("meta", 		bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	meter =			_HTMLElementProto("meter",												tagType=HTML_TAG_TYPE_INLINE_ALL)
	nav =			_HTMLElementProto("nav",												tagType=HTML_TAG_TYPE_STRUCTURE)
	_object =		_HTMLElementProto("object",												tagType=HTML_TAG_TYPE_STRUCTURE)		# problem
	ol =			_HTMLElementProto("ol",													tagType=HTML_TAG_TYPE_STRUCTURE)
	optgroup =		_HTMLElementProto("optgroup",											tagType=HTML_TAG_TYPE_STRUCTURE)
	option =		_HTMLElementProto("option", 	bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	output =		_HTMLElementProto("output",												tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	p =				_HTMLElementProto("p",													tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	param =			_HTMLElementProto("param", 		bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	picture =		_HTMLElementProto("picture",											tagType=HTML_TAG_TYPE_STRUCTURE)
	# pre =			_HTMLElementProto("pre",												tagType=XXXXX)
	progress =		_HTMLElementProto("progress",											tagType=HTML_TAG_TYPE_INLINE_ALL)
	q =				_HTMLElementProto("q",													tagType=HTML_TAG_TYPE_STRUCTURE)
	section =		_HTMLElementProto("section",											tagType=HTML_TAG_TYPE_STRUCTURE)
	s =				_HTMLElementProto("s",													tagType=HTML_TAG_TYPE_INLINE_ALL)
	samp =			_HTMLElementProto("samp",												tagType=HTML_TAG_TYPE_INLINE_ALL)
	script =		_HTMLElementProto("script",												tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	select =		_HTMLElementProto("select",												tagType=HTML_TAG_TYPE_STRUCTURE)
	small =			_HTMLElementProto("small",												tagType=HTML_TAG_TYPE_INLINE_ALL)
	source =		_HTMLElementProto("source", 	bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	span =			_HTMLElementProto("span",												tagType=HTML_TAG_TYPE_INLINE_ALL)
	strong =		_HTMLElementProto("strong",												tagType=HTML_TAG_TYPE_INLINE_ALL)
	# style =		_HTMLElementProto("style", 		bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=XXXXX)
	summary =		_HTMLElementProto("summary",											tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	sub =			_HTMLElementProto("sub",												tagType=HTML_TAG_TYPE_INLINE_ALL)
	sup =			_HTMLElementProto("sup",												tagType=HTML_TAG_TYPE_INLINE_ALL)
	# svg =			_HTMLElementProto("svg",												tagType=XXXXX)
	table =			_HTMLElementProto("table",												tagType=HTML_TAG_TYPE_STRUCTURE)
	textarea =		_HTMLElementProto("textarea",											tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	tbody =			_HTMLElementProto("tbody",												tagType=HTML_TAG_TYPE_STRUCTURE)
	td =			_HTMLElementProto("td",													tagType=HTML_TAG_TYPE_STRUCTURE)
	tfoot =			_HTMLElementProto("tfoot",												tagType=HTML_TAG_TYPE_STRUCTURE)
	th =			_HTMLElementProto("th",													tagType=HTML_TAG_TYPE_STRUCTURE)
	thead =			_HTMLElementProto("thead",												tagType=HTML_TAG_TYPE_STRUCTURE)
	time =			_HTMLElementProto("time",												tagType=HTML_TAG_TYPE_INLINE_ALL)
	title =			_HTMLElementProto("title",												tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	tr =			_HTMLElementProto("tr",													tagType=HTML_TAG_TYPE_STRUCTURE)
	track =			_HTMLElementProto("track", 		bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_INLINE_CONTENT)
	u =				_HTMLElementProto("u",													tagType=HTML_TAG_TYPE_INLINE_ALL)
	ul =			_HTMLElementProto("ul",													tagType=HTML_TAG_TYPE_STRUCTURE)
	var =			_HTMLElementProto("var",												tagType=HTML_TAG_TYPE_STRUCTURE)
	video =			_HTMLElementProto("video",												tagType=HTML_TAG_TYPE_STRUCTURE)
	wbr =			_HTMLElementProto("wbr",		bHasClosingTag=HTML_CLOSING_TAG_NEVER,	tagType=HTML_TAG_TYPE_INLINE_ALL)

	def __enter__(self) -> HTML5Scope:
		return self
	#

	def __exit__(self, exc_type, exc_val, exc_tb):
		pass
	#

	comment = _HTMLCommentProto()

	raw_html = _HTMLRawTextProto()

	raw_style_css = _HTMLRawCSSProto()

	style_css = _HTMLCSSProto()

	_text = _HTMLTextProto()

#










