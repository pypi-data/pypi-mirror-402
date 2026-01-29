###################################################################################
# Indirection layer to convert all etree occurances quickly to Metadoc.
# Simply replace
#     from lxml import etree
# with
#     from bq.metadoc import etree
###################################################################################


from bq.metadoc.formats import (
    _fromstring_fix_empty,
    _tostring_fix_empty,
    metadoc_everywhere,
)



from lxml.etree import ParseError, XMLSyntaxError # noqa: F401
from lxml.etree import parse as _xml_parse # noqa: F401

if not metadoc_everywhere:
    from lxml.builder import E
    from lxml.etree import (
        XML,
        Element,
        ElementTree,
        SubElement,
        _Element,
        _ElementTree,
    )
    from lxml.etree import fromstring as _xml_fromstring # noqa: F401
    from lxml.etree import tostring as _xml_tostring # noqa: F401

    def fromstring(s):
        return _fromstring_fix_empty(s)

    def tostring(xml, **kw):
        # escape any empty strings (XML is not round-tripable for empty strings in text nodes!)
        return _tostring_fix_empty(xml, **kw)

    def parse(f):
        res = _xml_parse(f).getroot()
        # fix any escaped empty strings
        for kid in res.iter(tag=Element):
            if kid.attrib.get("value") == "":
                del kid.attrib["value"]
                kid.text = ""
        return ElementTree(res)

else:
    from functools import partial

    from lxml.builder import E as _XML_E # noqa: F401

    from bq.metadoc.formats import Metadoc

    _Element = Metadoc

    class ElementTree:
        def __init__(self, root):
            self.root = root

        def getroot(self):
            return self.root

    _ElementTree = ElementTree

    def Element(tag, **kw):
        return Metadoc(tag=tag, **kw)

    def SubElement(node, tag, **kw):
        return node.add_tag(tag, **kw)

    def fromstring(s):
        return Metadoc.from_etree_like_string(s)

    def parse(f):
        return ElementTree(Metadoc.from_etree_like_string(f))

    XML = fromstring

    def tostring(xml, **kw):
        return xml.to_etree_like_string()

    class ElementMaker:
        def __call__(self, tag, *children, **attr):
            res = Metadoc(tag=tag, **attr)
            for kid in children:
                res.add_child(kid)
            return res

        def __getattr__(self, tag):
            return partial(self, tag)

    E = ElementMaker()
