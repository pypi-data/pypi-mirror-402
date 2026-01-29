"""
SYNOPSIS
========


DESCRIPTION
===========

"""

import copy
import logging
import re
from abc import ABC, abstractmethod
from collections.abc import MutableMapping
from datetime import datetime, timezone

import simplejson as json
from deprecated import deprecated
from lxml import etree

from .xmldict import asbool, d2xml, xml2d

try:
    # StringResult no longer available lxml > 5

    etree_result_types = (etree._ElementStringResult, etree._ElementUnicodeResult)

except (ImportError, AttributeError):
    etree_result_types = (etree._ElementUnicodeResult,)


log = logging.getLogger("bq.metadoc.formats")


# set following to True to force Metadoc everywhere
metadoc_everywhere = False


"""
Assume internal tree structure:

<RESERVED_TAGNAME uniq="00-xyz" name="..." type="image" usertype="cell image" unit="..."
 id="img1" path="..." owner="..." permission="..." storage="..." >    ...VALUE...
      <tag _id="09" name="NOT_RESERVED_TYPE" type="datetime" usertype="..." unit="..." id="..." >   ...VALUE...  </tag>
      ...
      <RESERVED_TAGNAME> ...VALUE... </RESERVED_TAGNAME>
      ...
</RESERVED_TAGNAME>


Assume external natural XML:

<VALID_XMLTAG .... >    ...value...
    <tag name="INVALID_XMLTAG" .... > ...VALUE... </tag>
    ...
    <VALID_XMLTAG .... > ...VALUE... </VALID_XMLTAG>
    ...
    <tag name="INVALID_XMLTAG" .... value="VALUE WITH SURROUNDING SPACES" />
    ...
</VALID_XMLTAG>


Assume external "tag-XML":

<RESERVED_TAGNAME ...  value="VALUE" >
    <tag name="NOT_RESERVED_TYPE" ...   value="VALUE" />
    ...
    <RESERVED_TAGNAME ...  value="VALUE" />
    ...
</RESERVED_TAGNAME>





The different converters work together as follows:

Convert from/to naturalxml:

NATURALXML str --> fromstring/deserialize --> NATURALXML etree* -->   naturalxml_to_tree  --> INTERNAL etree*
                   (resolves any empty                               (deals with leading/     (used in all internal ops;
                    string escapes)                                   trailing spaces in       ALL values in text nodes!)
                                                                      text nodes)

INTERNAL etree* -->   tree_to_naturalxml  -->  NATURALXML etree* -->  tostring/serialize  -->  NATURALXML str
                     (deals with leading/                             (escapes any empty
                      trailing spaces in                               text strings)
                      text nodes)


Convert from/to tagxml:

TAGXML str  -->  fromstring/deserialize  -->  TAGXML etree* -->  tagxml_to_tree  -->  INTERNAL etree*
                 (no special handling                            (moves values to
                  in this case)                                   text nodes)

INTERNAL etree* -->  tree_to_tagxml  -->  TAGXML etree* -->   tostring/serialize  -->  TAGXML str
                     (moves text nodes                        (no special handling
                      to value attr)                           in this case)


Convert from/to naturaljson:

NATURALJSON str  -->  json.load  -->  NATURALJSON struct  -->  d2xml  -->  NATURALXML etree*  -->  naturalxml_to_tree  -->  INTERNAL etree*
                                                              ("simulate"  (same as above ------> )
                                                               leading/
                                                               trailing space
                                                               escape)

INTERNAL etree*  -->  tree_to_naturalxml  -->  NATURALXML etree* -->  xml2d  -->  NATURALJSON struct  -->  json.dumps  -->  NATURALJSON str
                                      (<--------- same as above)     (resolve
                                                                      leading/
                                                                      trailing space
                                                                      escape)

Serialize/deserialize (for task communication):

INTERNAL etree* -->  tostring/serialize  -->  INTERNAL str
                     (escapes any empty
                      text strings)

INTERNAL str  -->  fromstring/deserialize -->  INTERNAL etree*
                   (resolves any empty
                    string escapes)


(* these etrees will be replaced with Metadoc eventually)
"""


# TODO: extract 'system types' from plugins at startup
RESERVED_TAGNAMES = {
    "resource",
    "system",
    "user",
    "_user",
    "mex",
    "module",
    "build",
    "sourcecode",
    "template",
    "dataset",
    "session",
    "tag",
    "gobject",
    # the following are not reserved because we currently store all of these gobjects as
    # <gobject type="line">coord1;coord2;...</gobject>
    # 'point', 'polyline', 'polygon', 'circle', 'ellipse', 'rectangle', 'square', 'line', 'label',
    "dream3d_pipeline",
    "bisque_pipeline",
    "cellprofiler_pipeline",
    "imagej_pipeline",
    "service",
    "image",
    "connoisseur",  # ML model
    "store",
    "mount",
    "dir",
    "file",
    "table",
    "tablecontainer",
    "text",
    "pdf",
    "html",
    "html_fragment",
    "molecule",
    "preference",
    "annotation",
    "acl",
    "group",
    "value",
    "container",  # used by dirs
    "response",  # used by imgsrv for responses
    "operations",  # used by imgsrv
    "format",  # used by imgsrv
    "codec",  # used by imgsrv
    "method",  # used by imgsrv
    "result",  # for query results
    "layer",  # layer used for named image layers
    "plotly",
    "future",
    "avia_config",  # client config resource
    "avia_project",  # project to build aa AVIA model for specific virus/strain/etc
    "avia_platemap",  # platemap resource (for ingester)
    "microplate",  # microplate with wells
}


#  Setup a default parser
#
#
XML_PARSER = etree.XMLParser(remove_comments=True)
etree.set_default_parser(XML_PARSER)


if metadoc_everywhere:

    def _tree_to_metadoc(tree):
        return Metadoc(et=tree)

else:

    def _tree_to_metadoc(tree):
        return tree


def _fromstring_fix_empty(s):
    res = etree.fromstring(s)
    # fix any escaped empty strings
    for kid in res.iter(tag=etree.Element):
        if kid.attrib.get("value") == "":
            del kid.attrib["value"]
            kid.text = ""
    return res


def _tostring_fix_empty(xml, encoding="unicode", **kw):
    # escape any empty strings (XML is not round-tripable for empty strings in text nodes!)
    # Unwrap Metadoc if present (duck typing to avoid circular import)
    if hasattr(xml, "node") and etree.iselement(xml.node):
        xml = xml.node

    inplace_changes = []
    for kid in xml.iter(tag=etree.Element):
        if kid.text == "":
            kid.text = None
            kid.set("value", "")
            inplace_changes.append(kid)
    res = etree.tostring(xml, encoding=encoding, **kw)
    for kid in inplace_changes:
        kid.text = ""
        del kid.attrib["value"]
    return res


def _text_to_number(val: str):
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val


def _text_to_native(val: str | None, ntype: str):
    if not val:
        return val
    match ntype:
        case "number":
            return _text_to_number(val)
        case "datetime":
            return datetime.fromisoformat(val)
        case "boolean":
            return asbool(val)
        case "list":
            return val.split(";")
        case "list[boolean]":
            return [asbool(tok) for tok in val.split(";")]
        case "list[number]":
            return [_text_to_number(tok) for tok in val.split(";")]
        case _:
            return val


def _native_to_text(val, attr: str | None = None) -> (str, str):
    if val is None:
        res = (None, None)
    elif isinstance(val, bool):
        res = (str(val).lower(), "boolean")
    elif isinstance(val, int | float):
        res = (str(val), "number")
    elif isinstance(val, datetime):
        if val.tzinfo is None or val.tzinfo.utcoffset(val) is None:
            # no timezone => assume UTC
            val = val.replace(tzinfo=timezone.utc)
        res = (val.isoformat(), "datetime")
    elif isinstance(val, list):
        if len(val) > 0 and isinstance(val[0], bool):
            res = (";".join(str(tok).lower() for tok in val), "list[boolean]")
        elif len(val) > 0 and isinstance(val[0], int | float):
            res = (";".join(str(tok) for tok in val), "list[number]")
        else:
            res = (";".join(str(tok) for tok in val), "list")
    else:
        res = (str(val), None)
    if attr in ("ts", "created"):
        if res[1] is None:
            try:
                # got string; check if it's a datetime
                datetime.fromisoformat(val)
                # yes it is
                res = (str(val), "datetime")
            except ValueError:
                pass
        if res[1] != "datetime":
            raise AttributeError(f'Attribute "{attr}" has to be of type datetime but got "{val}"')
    return res


def _adjust_attrs(attrs: dict) -> dict:
    return {k: _native_to_text(v, k)[0] for k, v in attrs.items()}


def _strip_attrs(doc):
    if isinstance(doc, dict):
        res = {k: _strip_attrs(v) for k, v in doc.items() if not k.startswith("@") or k == "@value"}
        if res == {}:
            res = None  # TODO: could be done for general d2xml/xml2d case that {}==None?
        elif set(res.keys()) == {"@value"}:
            # only @value left => make it direct value
            res = res["@value"]
    elif isinstance(doc, list):
        res = [_strip_attrs(item) for item in doc]
    else:
        res = doc
    return res


class InvalidFormat(ValueError):
    pass


def _clean_tree(elem, del_uri=True):
    res = copy.deepcopy(elem)
    _clean_tree_rec(res, del_uri=del_uri)
    return res


def _clean_tree_rec(elem, del_uri=True):
    elem.attrib.pop("_id", None)
    if del_uri is True:
        elem.attrib.pop("uri", None)
    for kid in elem:
        _clean_tree_rec(kid, del_uri=del_uri)


def _tree_to_naturalxml(tree, keep_text=False):
    """WARNING: MODIFIES TREE IN PLACE!"""
    for node in tree.iter(tag=etree.Element):
        if node.tag == "tag":
            try:
                node.tag = node.get("name", "tag")
                node.attrib.pop("name", None)
            except ValueError:
                pass
        if not keep_text and node.text is not None and node.text.strip() != node.text:
            # values surrounded by spaces are "escaped" with value= to avoid ambiguities
            node.set("value", node.text)
            node.text = None
    return tree


def _naturalxml_to_tree(tree, keep_text=False):
    """WARNING: MODIFIES TREE IN PLACE!"""
    for el in tree.iter(tag=etree.Element):
        if el.tag == "tag":
            try:
                _ = etree.Element(el.get("name", ""))
                raise InvalidFormat(f"Invalid natural XML (name {el.get('name')} should be tag)")
            except ValueError:
                pass
        elif el.tag not in RESERVED_TAGNAMES and "name" in el.attrib:
            raise InvalidFormat(f"Invalid natural XML (tag {el.tag} cannot have a name)")
        val = el.get("value")
        if val is not None:
            if val.strip() == val:
                raise InvalidFormat(
                    "Invalid natural XML (value attribute should be in text node, unless it has leading/trailing spaces)"
                )
            else:
                el.text = val
                el.attrib.pop("value")
        elif not keep_text and el.text is not None and el.text.strip() != el.text:
            # leading/trailing spaces are stripped from text nodes for convenience; if needed, use value= escape
            stripped = el.text.strip()
            el.text = stripped if stripped else None
        if el.tag not in RESERVED_TAGNAMES and el.tag != "tag":
            el.set("name", el.tag)
            el.tag = "tag"
    return tree


def _tree_to_tagxml(tree):
    """WARNING: MODIFIES TREE IN PLACE!"""
    for node in tree.iter(tag=etree.Element):
        if node.text is not None:
            node.set("value", node.text)
            node.text = None
    return tree


def _tagxml_to_tree(tree):
    """WARNING: MODIFIES TREE IN PLACE!"""
    for el in tree.iter(tag=etree.Element):
        if el.tag != "tag" and el.tag not in RESERVED_TAGNAMES:
            raise InvalidFormat(f"Invalid tag XML (tag {el.tag} should be name)")
        if el.tag == "tag" and el.get("name", "") in RESERVED_TAGNAMES:
            raise InvalidFormat(f"Invalid tag XML (name {el.get('name')} should be tag)")
        if el.text:
            if el.text.strip():
                raise InvalidFormat("Invalid tag XML (text node should be in 'value' attribute)")
            # leading/trailing spaces are stripped from text nodes for convenience
            el.text = None
        val = el.attrib.pop("value", None)
        if val is not None:
            el.text = val
    return tree


# -------------------------------------------------------------------------------------------------------------
# Formatters


class MetadocFormatter(ABC):
    """
    Abstract Strategy for Metadoc serialization.
    """

    @abstractmethod
    def dump(self, doc: "Metadoc") -> str | bytes | dict | list:
        pass

    @abstractmethod
    def load(self, data: str | bytes | dict | list) -> "Metadoc":
        pass


class TagXmlFormatter(MetadocFormatter):
    """
    Formatter for "System XML" (TagXML).

    In this format, values are primarily stored in the 'value' attribute of elements.

    Example Output:
        <resource name="test" value="some text">
            <tag name="child" value="123" />
        </resource>
    """

    def __init__(self, encoding: str = "unicode"):
        self.encoding = encoding

    def dump(self, doc: "Metadoc") -> str | bytes:
        clone = copy.deepcopy(doc.node)
        _tree_to_tagxml(clone)
        return _tostring_fix_empty(clone, encoding=self.encoding)

    def load(self, data: str | bytes) -> "Metadoc":
        try:
            if isinstance(data, str | bytes):
                node = _fromstring_fix_empty(data)
            else:
                node = copy.deepcopy(data)
        except etree.ParseError as exc:
            raise InvalidFormat("TagXmlFormatter.load") from exc
        _tagxml_to_tree(node)
        return Metadoc(et=node)


class NaturalXmlFormatter(MetadocFormatter):
    """
    Formatter for "Natural XML".

    In this format, values are stored in text nodes, and generic <tag name="foo">
    elements are unwrapped to <foo>.

    Example Output:
        <resource name="test">
            some text
            <child>123</child>
        </resource>
    """

    def __init__(self, encoding: str = "unicode", clean: bool = False):
        self.encoding = encoding
        self.clean = clean

    def dump(self, doc: "Metadoc") -> str | bytes:
        clone = copy.deepcopy(doc.node)
        if self.clean:
            _clean_tree_rec(clone)
        _tree_to_naturalxml(clone)
        return _tostring_fix_empty(clone, encoding=self.encoding)

    def load(self, data: str | bytes) -> "Metadoc":
        try:
            if isinstance(data, str | bytes):
                node = _fromstring_fix_empty(data)
            else:
                node = copy.deepcopy(data)
        except etree.ParseError as exc:
            raise InvalidFormat("NaturalXmlFormatter.load") from exc
        _naturalxml_to_tree(node)
        return Metadoc(et=node)


class NaturalJsonFormatter(MetadocFormatter):
    """
    Formatter for standard Dictionary-based JSON.

    This format is idiomatic for Python dictionaries but DOES NOT preserve document order
    for interleaved elements (e.g., A, B, A).

    Example Output:
        {
            "resource": {
                "@name": "test",
                "@value": "some text",
                "child": "123"
            }
        }
    """

    def __init__(
        self,
        as_object: bool = False,
        encoding: str = None,
        clean: bool = False,
        unwrap_root: bool = False,
        strip_attrs: bool = False,
    ):
        self.as_object = as_object
        self.encoding = encoding
        self.clean = clean
        self.unwrap_root = unwrap_root
        self.strip_attrs = strip_attrs

    def dump(self, doc: "Metadoc") -> str | bytes | dict | list:
        node = copy.deepcopy(doc.node)
        if self.clean:
            _clean_tree_rec(node)
        _tree_to_naturalxml(node, keep_text=True)
        data = xml2d(node, attribute_prefix="@", keep_tags=False)
        if self.unwrap_root and isinstance(data, dict) and len(data) == 1:
            data = data[list(data.keys())[0]]
        if self.strip_attrs:
            data = _strip_attrs(data)
        if self.as_object:
            return data
        s = json.dumps(data)
        return s.encode(self.encoding) if self.encoding else s

    def load(self, data: str | bytes | dict | list) -> "Metadoc":
        try:
            if isinstance(data, str | bytes):
                data = json.loads(data)
        except json.JSONDecodeError as exc:
            raise InvalidFormat("NaturalJsonFormatter.load") from exc
        return Metadoc(et=naturaljson_to_internal(data))


class OrderedJsonFormatter(MetadocFormatter):
    """
    Formatter for Ordered, Round-Trippable JSON.

    This format uses a list structure ('@children') to strictly preserve the order
    of child elements, making it safe for converting arbitrary XML documents.

    Example Output:
        {
            "resource": {
                "@name": "test",
                "@value": "some text",
                "@children": [
                    { "child": { "@value": "123" } }
                ]
            }
        }
    """

    def __init__(self, as_object: bool = False, encoding: str = None):
        self.as_object = as_object
        self.encoding = encoding

    def dump(self, doc: "Metadoc") -> str | bytes | dict | list:
        def node_to_ordered(n):
            # Extract attributes, excluding 'name' if it's the logical tag name
            attrs = {}
            for k, v in n.attrib.items():
                if n.tag == "tag" and k == "name":
                    continue
                attrs[f"@{k}"] = v

            if n.text:
                attrs["@value"] = n.text

            children = [{Metadoc(et=c).get_tag(): node_to_ordered(c)} for c in n]
            if children:
                attrs["@children"] = children

            # Simplify: if only text and no children/other attrs, return text directly
            if not children and len(attrs) == 1 and "@value" in attrs:
                return attrs["@value"]
            return attrs

        data = {doc.get_tag(): node_to_ordered(doc.node)}
        if self.as_object:
            return data
        s = json.dumps(data)
        return s.encode(self.encoding) if self.encoding else s

    def load(self, data: str | bytes | dict | list) -> "Metadoc":
        try:
            if isinstance(data, str | bytes):
                data = json.loads(data)
        except json.JSONDecodeError as exc:
            raise InvalidFormat("OrderedJsonFormatter.load") from exc
        if not isinstance(data, dict) or len(data) != 1:
            raise InvalidFormat("Ordered JSON must have a single root element")

        def ordered_to_doc(tag, val):
            if isinstance(val, str | int | float | bool):
                return Metadoc(tag=tag, value=val)

            attrs = {}
            children_data = []
            if isinstance(val, dict):
                for k, v in val.items():
                    if k == "@children":
                        children_data = v
                    elif k == "@value":
                        attrs["value"] = v
                    elif k.startswith("@"):
                        attrs[k[1:]] = v

            m = Metadoc(tag=tag, **attrs)
            for item in children_data:
                for ctag, cval in item.items():
                    m.add_child(ordered_to_doc(ctag, cval))
            return m

        root_tag = list(data.keys())[0]
        return ordered_to_doc(root_tag, data[root_tag])


def internal_to_naturaljson(xmldoc):
    return NaturalJsonFormatter(as_object=True).dump(Metadoc.convert(xmldoc))


def internal_to_tagjson(xmldoc):
    xmldoc = xmldoc.node if isinstance(xmldoc, Metadoc) else xmldoc
    return xml2d(_tree_to_tagxml(copy.deepcopy(xmldoc)), attribute_prefix="@", keep_tags=True)


def internal_to_naturalxml(xmldoc):
    # Legacy behavior: returns etree Element, NOT string
    doc = Metadoc.convert(xmldoc)
    clone = copy.deepcopy(doc.node)
    _tree_to_naturalxml(clone)
    return clone


def internal_to_tagxml(xmldoc):
    # Legacy behavior: returns etree Element, NOT string
    doc = Metadoc.convert(xmldoc)
    clone = copy.deepcopy(doc.node)
    _tree_to_tagxml(clone)
    return clone


def naturaljson_to_internal(jsondoc):
    return _tree_to_metadoc(
        _naturalxml_to_tree(d2xml(jsondoc, attribute_prefix="@", keep_value_attr=False), keep_text=True)
    )


def tagjson_to_internal(jsondoc):
    return _tree_to_metadoc(_tagxml_to_tree(d2xml(jsondoc, attribute_prefix="@", keep_value_attr=True)))


def naturalxml_to_internal(xmldoc):
    return _tree_to_metadoc(NaturalXmlFormatter().load(xmldoc).node)


def tagxml_to_internal(xmldoc):
    return _tree_to_metadoc(TagXmlFormatter().load(xmldoc).node)


# ----- TODO: GET RID OF THE FOLLOWING FCT EVENTUALLY (ONLY NEEDED TO TRANSITION LEGACY CODE MORE EASILY) ------
def anyxml_to_etree(tree):
    """Convert any XML format to proper internal etree. Only needed temporarily to clean up legacy code.
    WARNING: MODIFIES TREE IN PLACE!
    """
    if isinstance(tree, str):
        tree = etree.fromstring(tree)
    elif not isinstance(tree, etree._Element):
        # must be file like
        tree = etree.parse(tree).getroot()

    for el in tree.iter(tag=etree.Element):
        # Use Metadoc's normalization logic for each node
        # We wrap in a temporary Metadoc object to reuse its logic
        Metadoc(et=el)._normalize_node()

        # Post-normalization cleanup for legacy requirements
        if el.text is not None and el.text.strip() != el.text:
            # leading/trailing spaces are stripped from text nodes for convenience; if needed, use value= escape
            stripped = el.text.strip()
            el.text = stripped if stripped else None
    return tree


# -------------------------------------------------------------------------------------------------------------
# internal XML specific selectors... may be replaced later when switching everything to JSON


class Metadoc:
    """
    Class representing any nested metadata document.
    Interface is similar to :py:class:`xml.etree.ElementTree`.
    """

    class AttribProxy(MutableMapping):
        def __init__(self, doc):
            self.doc = doc

        def __iter__(self):  #!!! also add __next__
            yield from self.doc.node.attrib

        def __getitem__(self, key):
            if isinstance(key, int):
                raise IndexError("cannot get attribute by index")
            else:
                return self.doc.get_attr(key)

        def __setitem__(self, key, val):
            if isinstance(key, int):
                raise IndexError("cannot set attribute by index")
            else:
                self.doc.set_attr(key, val)

        def __delitem__(self, key):
            if isinstance(key, int):
                raise IndexError("cannot delete attribute by index")
            else:
                self.doc.del_attr(key)

        def __len__(self):
            return len(self.doc.node.attrib)

        def __contains__(self, key):
            return key in self.doc.node.attrib

    def __init__(self, et=None, parent=None, tag=None, **attrs):
        """
        Initialize a Metadoc wrapper around an XML node.

        This constructor handles three main cases:
        1. Wrapping an existing lxml Element:
           `Metadoc(et=my_element)`

        2. Creating a new root Element:
           `Metadoc(tag="my_tag", attr1="val1")`

        3. Creating a new child Element attached to a parent:
           `Metadoc(parent=parent_node, tag="child_tag", ...)`

        Args:
            et (etree._Element, optional): Existing lxml Element to wrap.
            parent (etree._Element, optional): Parent node to attach the new element to.
            tag (str, optional): Tag name for the new element.
            **attrs: Attributes to set on the new element.
        """
        # Phase 1: Node Acquisition
        if et is not None:
            # Wrap existing element
            self.node = et
            if parent is not None and self.node.getparent() is None:
                parent.append(self.node)
        else:
            # Create a new element
            # We use the user's tag initially; it will be normalized in Phase 2.
            # Refactored to avoid creating invalid XML tags and relying on normalization/exceptions
            target_tag = tag or "tag"
            if target_tag in RESERVED_TAGNAMES:
                # It is a reserved tag (e.g. 'resource', 'tag', 'image'), so use it directly.
                # It is assumed that all RESERVED_TAGNAMES are valid XML tags.
                node_tag = target_tag
                node_name = None
            else:
                # It is a custom tag or potentially invalid XML (e.g. 'my tag', 'user@domain').
                # We use generic 'tag' and set the name attribute.
                node_tag = "tag"
                node_name = target_tag

            if parent is None:
                self.node = etree.Element(node_tag)
            else:
                self.node = etree.SubElement(parent, node_tag)

            if node_name is not None:
                self.node.set("name", node_name)

        # Phase 2: Schema Normalization
        # Enforce Metadoc rules: reserved tags vs generic <tag name="...">
        # and move 'value' attributes to text nodes.
        # If we are wrapping, we extract existing state first.
        initial_value = attrs.pop("value", None)
        initial_type = attrs.pop("type", None)

        if et is not None:
            self._normalize_node()

        # Phase 3: Content Initialization
        # For new elements, apply attributes and values with type conversion.
        if et is None:
            # Apply initial attributes (native types -> strings)
            for k, v in attrs.items():
                self.set_attr(k, v)

            # Apply value and type
            if initial_type is not None:
                self.set_attr("type", initial_type)
            self.set_value(initial_value)

    def _normalize_node(self):
        """
        Ensure the underlying node adheres to the Metadoc internal schema.
        - Non-reserved tags are converted to <tag name="original_tag">.
        - 'tag' elements with a name in RESERVED_TAGNAMES are unwrapped.
        - 'value' attributes are moved to the text node.
        """
        node = self.node
        tag = node.tag

        # 1. Normalize Tag Name
        if tag == "tag":
            # If it's already a generic tag, check if it should be a reserved one
            name = node.get("name")
            if name in RESERVED_TAGNAMES:
                node.tag = node.attrib.pop("name")
        elif tag not in RESERVED_TAGNAMES:
            # If it's a custom tag, convert to generic <tag name="...">
            node.set("name", tag)
            node.tag = "tag"

        # 2. Normalize Value Content
        val = node.attrib.pop("value", None)
        if val is not None and not node.text:
            node.text = val

    def __getstate__(self):
        return self.serialize()

    def __setstate__(self, s):
        self.node = self.deserialize(s).node

    def dump(self, formatter: MetadocFormatter) -> str | bytes | dict | list:
        return formatter.dump(self)

    @classmethod
    def load(cls, data, formatter: MetadocFormatter) -> "Metadoc":
        return formatter.load(data)

    @staticmethod
    def convert(internal):
        if isinstance(internal, Metadoc):
            return internal
        if isinstance(internal, etree._Element):
            return Metadoc(et=internal)
        elif isinstance(internal, etree._ElementTree):
            return Metadoc(et=internal.getroot())
        elif isinstance(
            # internal, (etree._ElementUnicodeResult, etree._ElementStringResult)
            # StringResult no longer available lxml > 5
            internal,
            etree_result_types,
        ):
            return str(internal)
        elif isinstance(internal, list):
            return [Metadoc.convert(it) for it in internal]
        elif not internal:  # None, empty string ,or  empty list
            return None
        else:
            return (Metadoc.convert(it) for it in internal)

    @staticmethod
    def convert_back(metadoc):
        if metadoc_everywhere:
            return metadoc
        else:
            return metadoc.node

    @staticmethod
    def convert_to_etree(metadoc):
        return Metadoc.convert_back(metadoc)

    @staticmethod
    def from_tagxml(xmldoc: str) -> "Metadoc":
        """
        Create metadoc from "tag" XML string.

        Args:
            xmldoc: "tag" XML string

        Returns:
            created metadoc
        """
        return TagXmlFormatter().load(xmldoc)

    @staticmethod
    def from_tagxml_etree(xmldoc):
        return Metadoc(et=tagxml_to_internal(xmldoc))

    def to_tagxml(self) -> str:
        """
        Convert this metadoc to "tag" XML string.

        Returns:
            "tag" XML string
        """
        return self.dump(TagXmlFormatter())

    def to_tagxml_etree(self):
        return internal_to_tagxml(self.node)

    @staticmethod
    def from_naturalxml(xmldoc: str) -> "Metadoc":
        """
        Create metadoc from "natural" XML string.

        Args:
            xmldoc: "natural" XML string

        Returns:
            created metadoc
        """
        return NaturalXmlFormatter().load(xmldoc)

    @staticmethod
    def from_naturalxml_etree(xmldoc):
        return Metadoc(et=naturalxml_to_internal(xmldoc))

    def to_naturalxml(self) -> str:
        """
        Convert this metadoc to "natural" XML string.

        Returns:
            "natural" XML string
        """
        return self.dump(NaturalXmlFormatter())

    def to_naturalxml_etree(self):
        return internal_to_naturalxml(self.node)

    @staticmethod
    def from_dict(jsondict: dict) -> "Metadoc":
        """
        Create metadoc from JSON-like Python structure.

        Args:
            jsondoc: JSON-like Python structure

        Returns:
            created metadoc
        """
        return Metadoc(et=naturaljson_to_internal(jsondict))

    def to_dict(self) -> dict:
        """
        Convert this metadoc to JSON-like Python structure

        Returns:
            JSON-like Python structure of dicts and lists
        """
        return self.dump(NaturalJsonFormatter(as_object=True))

    @deprecated("Input moving dict to str.. use from_dict")
    def from_json(jsondict: dict):
        return Metadoc.from_dict(jsondict)

    @staticmethod
    def from_json_new(json_str: str | bytes) -> "Metadoc":
        """
        Create metadoc from a standard JSON string or bytes.

        Args:
            json_str: JSON string or bytes.

        Returns:
            created metadoc
        """
        return NaturalJsonFormatter().load(json_str)

    @deprecated("Return moving from dict to str.. use to_dict")
    def to_json(self):
        return self.to_dict()

    def to_json_new(self, encoding: str = None) -> str | bytes:
        """
        Convert this metadoc to a standard JSON string.

        Args:
            encoding: If provided (e.g. 'utf-8'), returns bytes. Otherwise returns str.

        Returns:
            JSON string or bytes.
        """
        return self.dump(NaturalJsonFormatter(encoding=encoding))

    @staticmethod
    def from_ordered_json(json_str: str | bytes | dict) -> "Metadoc":
        """
        Create metadoc from an Ordered JSON string, bytes, or dict.
        This format supports round-tripping document order and mixed content.

        Args:
            json_str: Ordered JSON string, bytes, or dict.

        Returns:
            created metadoc
        """
        return OrderedJsonFormatter().load(json_str)

    def to_ordered_json(self, encoding: str = None) -> str | bytes:
        """
        Convert this metadoc to an Ordered JSON string.
        This format supports round-tripping document order and mixed content.

        Args:
            encoding: If provided (e.g. 'utf-8'), returns bytes. Otherwise returns str.

        Returns:
            Ordered JSON string or bytes.
        """
        return self.dump(OrderedJsonFormatter(encoding=encoding))

    def as_xml(self) -> str:
        """
        Get tags in metadoc as "natural" XML string.
        This is NOT round-tripable through from_naturalxml!

        Returns:
            "natural" XML string
        """
        return self.dump(NaturalXmlFormatter(clean=True))

    def as_dict(self, strip_attributes: bool = False) -> dict:
        """
        Get all tags in metadoc as a dictionary.
        This is NOT round-tripable through from_json!

        Args:
            strip_attributes: if True, removes all attributes (keys starting with "@")

        Returns:
            dict
        """
        return self.dump(
            NaturalJsonFormatter(as_object=True, clean=True, unwrap_root=True, strip_attrs=strip_attributes)
        )

    def clean(self) -> "Metadoc":
        """
        Return a "cleaned" version of the doc (i.e., stripped URIs and IDs).

        Returns:
            cleaned doc
        """
        return Metadoc(et=_clean_tree(self.node))

    def __iter__(self):  #!!! also add __next__
        for kid in self.node:
            yield Metadoc(et=kid)

    def __getitem__(self, ix):
        return Metadoc(et=self.node[ix])

    def __len__(self):
        return len(self.node)

    def __getattr__(self, name):
        if name == "node":
            return self.__dict__[name]
        if name == "text":
            return self.get_value_str()
        if name == "value":
            return self.get_value()
        if name == "tag":
            return self.get_tag()
        if name == "type":
            return self.get_attr("type")
        if name == "name":
            return self.get_attr("name")
        if name == "attrib":
            return self.AttribProxy(self)
        raise AttributeError(f'\'unknown Metadoc attribute "{name}"')

    def __setattr__(self, name, val):
        if name == "node":
            self.__dict__[name] = val
            return
        if name == "text" or name == "value":
            self.set_value(val)
            return
        if name == "type":
            self.set_attr("type", val)
            return
        if name == "name":
            self.set_attr("name", val)
            return
        if name == "tag":
            self.node.tag = val
            return
        raise AttributeError(f'unknown Metadoc attribute "{name}"')

    def get_tag(self):
        if self.node.tag == "tag":
            return self.node.get("name", "tag")
        else:
            return self.node.tag

    def get_value(self):  #!!! also add get_path()
        return _text_to_native(self.node.text, self.node.get("type"))

    def get_value_str(self):
        return self.node.text

    def set_value(self, val):
        txt, ntype = _native_to_text(val)
        self.node.text = txt
        if ntype is not None and "type" not in self.node.attrib:
            self.node.set("type", ntype)

    def get_attr(self, attr, default=None):
        if attr == "value":
            res = self.get_value()
            return res if res is not None else default
        else:
            if attr in ("created", "ts"):
                ntype = "datetime"
            else:
                ntype = None
            res = self.node.get(attr)
            return _text_to_native(res, ntype) if res is not None else default

    def get_attr_str(self, attr, default=None):
        if attr == "value":
            res = self.get_value_str()
            return res if res is not None else default
        else:
            res = self.node.get(attr)
            return res if res is not None else default

    get = get_attr_str  # alias for etree legacy

    def del_attr(self, attr):
        if attr == "value":
            self.node.text = None
        else:
            del self.node.attrib[attr]

    def set_attr(self, attr, val):
        if attr == "value":
            self.set_value(val)
        else:
            txt, _ = _native_to_text(val, attr)
            self.node.set(attr, txt)

    set = set_attr  # alias for etree legacy

    def keys(self):
        return self.node.keys()

    def get_docid(self):
        return self.node.get("resource_uniq")

    def get_parent(self):
        parent = self.node.getparent()
        return Metadoc(et=parent) if parent is not None else None

    @staticmethod
    def create_doc(tag, **attrs):
        return Metadoc(tag=tag, **attrs)

    def add_sibling(self, tag, **attrs):
        return Metadoc(parent=self.node.getparent(), tag=tag, **attrs)

    def add_tag(self, tag, **attrs):
        return Metadoc(parent=self.node, tag=tag, **attrs)

    def replace_with(self, doc):
        if self.node.getparent() is not None:
            self.node.getparent().replace(self.node, doc.node)

    def delete(self):
        if self.node.getparent() is not None:
            self.node.getparent().remove(self.node)

    def add_child(self, newchild):
        self.node.append(newchild.node)
        return newchild

    append = add_child  # alias for etree legacy

    def extend(self, newchildren):
        self.node.extend(kid.node for kid in newchildren)

    def iter(self, tag=None):
        for node in self.node.iter(tag=tag):
            yield Metadoc(et=node)

    @staticmethod
    def from_etree_like_string(s):
        res = anyxml_to_etree(s)
        # fix any escaped empty strings
        for kid in res.iter(tag=etree.Element):
            if kid.attrib.get("value") == "":
                del kid.attrib["value"]
                kid.text = ""
        return Metadoc(et=res)

    def to_etree_like_string(self):
        # escape any empty strings (XML is not round-tripable for empty strings in text nodes!)
        return _tostring_fix_empty(self.node, encoding="unicode")

    deserialize = from_tagxml
    serialize = to_tagxml

    def __str__(self):
        return self.to_etree_like_string()
        # TODO: better return as JSON

    def __repr__(self):
        return f"metadoc:{self.to_etree_like_string()}"
        # TODO: better return as JSON

    def _path_to_xpath(self, path):
        path = path.strip()
        if re.match(
            r"""^[\w"']""", path
        ):  # TODO: right now every tag has to start with '/' otherwise the regex below won't work
            path = "./" + path

        # split into quoted and non-quoted parts
        QUOTED_STRING = re.compile("(\\\\?[\"']).*?\\1")  # a pattern to match strings between quotes
        result = []  # a store for the result pieces
        head = 0  # a search head reference
        for match in QUOTED_STRING.finditer(path):
            # process everything until the current quoted match and add it to the result
            unquoted_part = path[head : match.start()]
            quoted_part = match[0]
            if unquoted_part.endswith("/"):
                # slash followed by quoted is escaped tag name, include it
                unquoted_part = unquoted_part + quoted_part
                quoted_part = ""
            result.append(self._path_to_xpath_single(unquoted_part))
            result.append(quoted_part)  # add the quoted match verbatim to the result
            head = match.end()  # move the search head to the end of the quoted match
        if head < len(path):  # if the search head is not at the end of the string
            # process the rest of the string and add it to the result
            result.append(self._path_to_xpath_single(path[head:]))
        return "".join(result)  # join back the result pieces and return them

    def _path_to_xpath_single(self, path):
        res = ""
        path_pos = 0
        p = re.compile(r"""@[\w -]+|/[^"'/.*@[\]]+|/"[^"]+"|/'[^']+'""")  # allow to escape tag names with " or '
        for m in p.finditer(path):
            pos = m.start()
            end = m.end()
            tok = m.group().strip()
            if tok == "@value":
                new_tok = " text()"
            elif tok[0] == "@":
                new_tok = " " + tok
            elif tok[0] == "/":
                newname = tok[1:].strip()
                if newname.startswith('"') or newname.startswith("'"):
                    newname = newname[1:-1]
                if newname not in RESERVED_TAGNAMES:
                    new_tok = f'/tag[@name="{newname}"]'
                else:
                    new_tok = tok
            res += path[path_pos:pos] + new_tok
            path_pos = end
        res += path[path_pos:]
        return res

    def path_query(self, path: str) -> list["Metadoc"]:
        """
        Select nodes in this metadoc based on a path selector.

        Args:
            path: path query (e.g., ``'//my tag/another tag with spaces[@attr = "...."]'``)
        """

        # generic path query (Xpath/JSONpath compatible)
        # e.g.: '//my tag/another tag with spaces[@attr = "...."]'
        # becomes '//tag[@name="my tag"]/tag[@name="another tag with spaces"][@attr = "...."]' for Xpath
        # becomes '$..['my tag']['another tag with spaces'][?(@.attr = "....")]' for JSONpath
        xpath = self._path_to_xpath(path)
        log.debug("path_query %s -> %s", path, xpath)
        return Metadoc.convert(self.node.xpath(xpath))

    def xpath(self, xpath):
        # legacy... these are likely using "tag[@name='xxx']", so should work as is
        return Metadoc.convert(self.node.xpath(xpath))

    findall = xpath  # alias for etree legacy

    def find(self, xpath):
        # legacy... these are likely using "tag[@name='xxx']", so should work as is
        res = self.node.find(xpath)
        return Metadoc(et=res) if res is not None else None


# -------------------------------------------------------------------------------------------------------------
