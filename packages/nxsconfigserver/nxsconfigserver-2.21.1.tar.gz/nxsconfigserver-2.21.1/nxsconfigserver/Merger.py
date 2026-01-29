#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2017 DESY, Jan Kotanski <jkotan@mail.desy.de>
#
#    nexdatas is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    nexdatas is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with nexdatas.  If not, see <http://www.gnu.org/licenses/>.
#

""" Classes for merging DOM component trees """

import re
import sys

import xml.etree.ElementTree as et
from lxml.etree import XMLParser
import lxml.etree as etree
from .Errors import IncompatibleNodeError, UndefinedTagError


if sys.version_info > (3,):
    basestring = str
    unicode = str


def _tostr(text):
    """ converts text  to str type

    :param text: text
    :type text: :obj:`bytes` or :obj:`unicode`
    :returns: text in str type
    :rtype: :obj:`str`
    """
    if isinstance(text, str):
        return text
    elif sys.version_info > (3,):
        return str(text, encoding="utf8")
    else:
        return str(text)


def _toxml(node):
    """ provides xml content of the whole node

    :param node: DOM node
    :type node: :class:`xml.dom.Node`
    :returns: xml content string
    :rtype: :obj:`str`
    """
    if sys.version_info > (3,):
        xml = _tostr(et.tostring(node, encoding='unicode', method='xml'))
    else:
        xml = _tostr(et.tostring(node, encoding='utf8', method='xml'))
    if xml.startswith("<?xml version='1.0' encoding='utf8'?>"):
        xml = str(xml[38:])
    return xml


class Merger(object):

    """ merges the components
    """

    def __init__(self):
        """ consturctor
        """

        #: (:obj:`xml.etree.ElementTree.Element`) DOM root node
        self.__root = None
        #: (:obj:`bool`) do not merge node on false
        self.skip = False
        #: (:obj:`list` <:obj:`str`> ) tags which cannot have the same siblings
        self.singles = ['strategy', 'dimensions', 'definition',
                        'record', 'device', 'query', 'database',
                        'selection', 'sourceview']

        #: (:obj:`list` <:obj:`str`> ) tags removed when are empty
        self.tocut = ['NXtransformations', 'NXcollection']

        #: (:obj:`dict` <:obj:`str` , :obj:`tuple` <:obj:`str`>> ) \
        #:    allowed children
        self.children = {
            "attribute": ("datasource", "strategy", "enumeration",
                          "doc", "dimensions"),
            "definition": ("group", "field", "attribute", "link",
                           "component", "doc", "symbols"),
            "dimensions": ("dim", "doc"),
            "field": ("attribute", "datasource", "doc", "dimensions",
                      "enumeration", "strategy"),
            "group": ("group", "field", "attribute", "link", "component",
                      "doc", "vds"),
            "link": ("datasource", "strategy", "doc"),
            "dim": ("datasource", "strategy", "doc"),
            "vds": ("attribute", "datasource", "doc", "dimensions",
                    "enumeration", "strategy", "map"),
            "map": ("dimensions", "selection", "sourceview",
                    "datasource", "doc", "strategy"),
            "selection": ("slice", "slab", "doc"),
            "slab": ("datasource", "strategy", "doc"),
            "slice": ("datasource", "strategy", "doc"),
            "sourceview": ("dimensions", "selection", "doc"),
        }

        #: (:obj:`list` <:obj:`str`> ) with unique text
        self.uniqueText = ['field', 'attribute', 'query', 'strategy', 'result']

        #: (:obj:`list` <:obj:`str`> ) node which can have switched strategy
        self.switchable = ["field", "attribute"]

        #: (:obj:`list` <:obj:`str`> ) node which can have links
        self.linkable = ["field", "vds"]

        #: (:obj:`dict` <:obj:`str` , :obj:`str`> ) \
        #:     strategy modes to switch
        self.modesToSwitch = {
            "INIT": "STEP",
            "FINAL": "STEP"
        }

        #: (:obj:`list` <:obj:`str`> ) aliased to switch to STEP mode
        self.switchdatasources = []

        #: (:obj:`list` <:obj:`str`> ) aliased to add links
        self.linkdatasources = []

        #: (:obj:`list` <:obj:`str`> ) aliased to add extralinks
        self.extralinkdatasources = []

        #: (:obj:`list` <:obj:`str`> ) aliased to switch to CanFial mode
        self.canfaildatasources = []

        #: (:obj:`list` <:obj:`str`> ) extra link path
        self.extralinkpath = []

        #: (:obj:`list` <:obj:`str`> ) data link path
        self.linkpath = [("data", "NXdata")]

        #: (:obj:`str`) datasource label
        self.__dsvars = "$datasources."

    @classmethod
    def __getText(cls, node):
        """ collects text from text child nodes

        :param node: parent node
        :type node: :obj:`xml.etree.ElementTree.Element`
        """
        if node is not None:
            tnodes = ([node.text] if node.text else []) \
                     + [child.tail for child in node if child.tail]
            return unicode("\n".join(tnodes)).strip()
        return ""

    def __getAncestors(self, node, ancestors):
        """ gets ancestors form the xml tree

        :param node: dom node
        :type node: :obj:`xml.etree.ElementTree.Element`
        :param ancestors: list with NeXus path nodes (tag, name, type)
        :type ancestors: :obj:`list`< (:obj:`str`,:obj:`str`,:obj:`str`) >
        :returns: xml path
        :rtype: :obj:`str`
        """
        res = ""

        name = node.get("name")

        for an in ancestors:
            res += "/" + an[0]
            if an[1]:
                res += ":" + an[1]
        res += "/" + unicode(node.tag)
        if name:
            res += ":" + name
        return res

    def __areMergeable(self, elem1, elem2, ancestors, node):
        """ checks if two elements are mergeable

        :param elem1: first element
        :type elem1: :obj:`xml.etree.ElementTree.Element`
        :param elem2: second element
        :type elem2: :obj:`xml.etree.ElementTree.Element`
        :param ancestors: list with NeXus path nodes (tag, name, type)
        :type ancestors: :obj:`list`< (:obj:`str`,:obj:`str`,:obj:`str`) >
        :returns: bool varaible if two elements are mergeable
        :rtype: :obj:`bool`
        """

        if elem1.tag != elem2.tag:
            return False
        tagName = unicode(elem1.tag)
        status = True

        name1 = elem1.get("name")
        name2 = elem2.get("name")
        if name1 != name2 and name1 and name2:
            if tagName in self.singles:
                raise IncompatibleNodeError(
                    "Incompatible element attributes  %s: %s"
                    % (str(self.__getAncestors(elem1, ancestors)), str(name2)),
                    [elem1, elem2])
            return False

        tags = self.__checkAttributes(elem1, elem2)
        if tags:
            status = False
            if tagName in self.singles or (name1 and name1 == name2):
                if not self.skip:
                    if tags and tags[0] == ('TANGO', 'CLIENT'):
                        node.remove(elem2)
                    elif tags and tags[0] == ('CLIENT', 'TANGO'):
                        node.remove(elem1)
                    else:
                        raise IncompatibleNodeError(
                            "Incompatible element attributes  %s: %s %s"
                            % (str(self.__getAncestors(elem1, ancestors)),
                               str(node.get("name")),  str(tags)),
                            [elem1, elem2])
                else:
                    status = False

        if tagName in self.uniqueText:
            text1 = unicode(self.__getText(elem1)).strip()
            text2 = unicode(self.__getText(elem2)).strip()
            if text1 != text2 and text1 and text2:
                if not self.skip:
                    raise IncompatibleNodeError(
                        "Incompatible \n%s element value\n%s \n%s "
                        % (str(self.__getAncestors(elem1, ancestors)),
                           text1, text2),
                        [elem1, elem2])
                else:
                    status = False
        return status

    def __checkAttributes(self, elem1, elem2):
        """ checks if two elements are mergeable

        :param elem1: first element
        :type elem1: :obj:`xml.etree.ElementTree.Element`
        :param elem2: second element
        :type elem2: :obj:`xml.etree.ElementTree.Element`
        :returns: tags with not mergeable attributes
        :rtype: :obj:`list` <:obj:`tuple` <:obj:`str`>>
        """
        tags = []
        attr1 = elem1.attrib
        attr2 = elem2.attrib
        for i1 in attr1.keys():
            for i2 in attr2.keys():
                if i1 == i2 and attr1[i1] != attr2[i2]:
                    tags.append((str(attr1[i1]), str(attr2[i2])))
        return tags

    @classmethod
    def __mergeNodes(cls, elem1, elem2, parent):
        """ merges two dom elements

        :param elem1: first element
        :type elem1: :obj:`xml.etree.ElementTree.Element`
        :param elem2: second element
        :type elem2: :obj:`xml.etree.ElementTree.Element`
        :param parent: the given parent node
        :type parent: :obj:`xml.etree.ElementTree.Element`
        """
        attr2 = elem2.attrib
        texts = []
        toMove = []

        for i2, at2 in attr2.items():
            elem1.attrib[i2] = at2

        if cls.__getText(elem1) != cls.__getText(elem2):
            if elem1.text and unicode(elem1.text).strip():
                texts.append(unicode(elem1.text).strip())
            for tchild in elem1:
                if tchild.tail and unicode(tchild.tail).strip():
                    texts.append(unicode(tchild.tail).strip())

            if unicode(elem2.text).strip() not in texts:
                if elem2.text and unicode(elem2.text).strip():
                    toMove.append(elem2.text)
            for tchild in elem2:
                if unicode(tchild.tail).strip() not in texts:
                    if tchild.tail and unicode(tchild.tail).strip():
                        toMove.append(tchild.tail)
        for tchild in elem2:
            elem1.append(tchild)
        if elem2.tail and unicode(elem2.tail).strip() \
           and elem1.tail != elem2.tail and \
           elem2.tail != parent.text:
            if elem1.tail:
                elem1.tail += "\n" + elem2.tail
            else:
                elem1.tail = elem2.tail
        if toMove:
            if elem1.text:
                elem1.text += "\n" + "\n".join(toMove)
            else:
                elem1.text = "\n".join(toMove)

        parent.remove(elem2)

    def __mergeChildren(self, node, ancestors, entrynode=None,
                        datanode=None, linknode=None):
        """ merge the given node

        :param node: the given node
        :type node: :obj:`xml.etree.ElementTree.Element`
        :param ancestors: list with NeXus path nodes (tag, name, type)
        :type ancestors: :obj:`list`< (:obj:`str`,:obj:`str`,:obj:`str`) >
        :param entrynode: entry node
        :type entrynode: :class:`xml.etree.ElementTree.Element`
        :param datanode: data node
        :type datanode: :class:`xml.etree.ElementTree.Element`
        :param linknode: link node
        :type linknode: :class:`xml.etree.ElementTree.Element`
        """
        if node is not None and node.tag != "definition":
            newancestors = tuple(
                list(ancestors) +
                [(node.tag, node.get("name"), node.get("type"))])
            if entrynode is None:
                entrynode = node
        else:
            newancestors = ancestors
        if node is not None:

            children = list(node)
            c1 = 0
            if unicode(node.tag) in self.switchable and self.switchdatasources:
                # print("NODE", node.tag, node.get("name"))
                self.__switch(node)
            while c1 < len(children):
                child1 = children[c1]
                c2 = c1 + 1
                while c2 < len(children):
                    child2 = children[c2]
                    if child1 != child2:
                        if self.__areMergeable(
                                child1, child2,
                                ancestors, node):
                            self.__mergeNodes(child1, child2, node)
                            children.pop(c2)
                            c2 -= 1
                    c2 += 1
                c1 += 1

            nName = unicode(node.tag)

            for child in node:
                cName = unicode(child.tag)
                if nName and nName in self.children.keys():
                    if cName and cName not in self.children[nName]:
                        raise IncompatibleNodeError(
                            "Not allowed <%s> child of \n < %s > \n  parent"
                            % (cName,
                               self.__getAncestors(child, newancestors)),
                            [child])

                self.__mergeChildren(child, newancestors, entrynode,
                                     datanode, linknode)
                # if cName in self.switchable and self.switchdatasources:
                #     print("CHILD", child.tag, child.get("name"))
                #     self.__switch(child)
                if cName in self.linkable and self.linkdatasources:
                    datanode = self.__addlink(
                        child, newancestors, entrynode, datanode,
                        self.linkdatasources, self.linkpath)
                if cName in self.linkable and self.extralinkdatasources:
                    linknode = self.__addlink(
                        child, newancestors, entrynode, linknode,
                        self.extralinkdatasources, self.extralinkpath)
                if cName in self.switchable and self.canfaildatasources:
                    self.__canfail(child)

            children = list(node)
            c1 = 0
            while c1 < len(children):
                child = children[c1]
                if child.tag == "group":
                    cchildren = list(child)
                    elems = [cchildren[i]
                             for i in range(len(cchildren))]
                    if not elems and \
                       child.get("type") in self.tocut and \
                       (len(child.attrib.keys()) == 1 or
                        (len(child.attrib.keys()) == 2 and
                         "NX" + child.get("name") ==
                         child.get("type"))):
                        node.remove(child)
                c1 += 1

    def __getTextDataSource(self, node, dslist=None):
        """ find first datasources node and name in text nodes of the node

        :param node: the parent node
        :type node: :obj:`xml.etree.ElementTree.Element`
        :param dslist: list of datasources
        :type dslist: :obj:`list` <:obj:`str`>
        :returns: (node, name) of the searched datasource
        :rtype: (:obj:`str` , :obj:`str`)
        """
        dsname = None
        dsnode = None
        dslist = dslist or self.switchdatasources
        text = unicode(self.__getText(node)).strip()
        index = text.find(self.__dsvars)
        while index >= 0:
            try:
                finder = re.finditer(
                    r"[\w]+",
                    text[(index + len(self.__dsvars)):])
                if sys.version_info > (3,):
                    subc = finder.__next__().group(0)
                else:
                    subc = finder.next().group(0)
            except Exception:
                subc = ''
            name = subc.strip() if subc else ""
            if name in dslist:
                dsnode = node
                dsname = name
                break
            text = text[(index + len(name) + len(self.__dsvars) + 2):]
            index = text.find(self.__dsvars)
        return dsname, dsnode

    def __switch(self, node):
        """ switch the given node to step mode

        :param node: the given node
        :type node: :obj:`xml.etree.ElementTree.Element`
        """
        if node is not None:
            stnodes = []
            modes = []
            mode = None
            dsname = None
            dsnode = None

            dsname, dsnode = self.__getTextDataSource(node)

            for child in node:
                cName = unicode(child.tag)
                if cName == 'datasource':
                    dsname = child.get("name")
                    if dsname in self.switchdatasources:
                        dsnode = child
                    else:
                        dsname, dsnode = self.__getTextDataSource(child)
                    if dsnode is None:
                        for gchild in child:
                            gcName = unicode(gchild.tag)
                            if gcName == 'datasource':
                                gdsname = gchild.get("name")
                                if gdsname in self.switchdatasources:
                                    dsnode = child
                elif cName == 'strategy':
                    mode = child.get("mode")
                    if mode in self.modesToSwitch.keys():
                        stnodes.append(child)
                        modes.append(mode)
                    # else:
                    #     break
                # if stnode not None and dsnode is not None:
                #     break
            if stnodes and dsnode is not None:
                for si, stn in enumerate(stnodes):
                    mode = modes[si]
                    if mode in self.modesToSwitch.keys():
                        stn.attrib["mode"] = self.modesToSwitch[mode]
                        # print("SWITCH", node.get("name"), dsname, dsnode)

    def __canfail(self, node):
        """ switch the given node to canfail mode

        :param node: the given node
        :type node: :obj:`xml.etree.ElementTree.Element`
        """
        if node is not None:
            stnode = None
            dsname = None
            dsnode = None

            dsname, dsnode = self.__getTextDataSource(
                node, self.canfaildatasources)

            for child in node:
                cName = unicode(child.tag)
                if cName == 'datasource':
                    dsname = child.get("name")
                    if dsname in self.canfaildatasources:
                        dsnode = child
                    else:
                        dsname, dsnode = self.__getTextDataSource(
                            child, self.canfaildatasources)
                    if dsnode is None:
                        for gchild in child:
                            gcName = unicode(gchild.tag)
                            if gcName == 'datasource':
                                gdsname = gchild.get("name")
                                if gdsname in self.canfaildatasources:
                                    dsnode = child
                elif cName == 'strategy':
                    stnode = child
                if stnode is not None and dsnode is not None:
                    break
            if stnode is not None and dsnode is not None:
                stnode.attrib["canfail"] = "true"

    def __addlink(self, node, ancestors, entrynode, linknode, linkdatasources,
                  linkpath=None):
        """ add link in NXdata group

        :param node: the given node
        :type node: :obj:`xml.etree.ElementTree.Element`
        :param ancestors: list with NeXus path nodes (tag, name, type)
        :type ancestors: :obj:`list`< (:obj:`str`,:obj:`str`,:obj:`str`) >
        :param entrynode: root node
        :type entrynode: :class:`xml.etree.ElementTree.Element`
        :param linknode: the given link node
        :type linknode: :obj:`xml.etree.ElementTree.Element`
        :param linkpath: list with NeXus path (name, type)
        :type linkpath: :obj:`list` < (:obj:`str`,:obj:`str`) >
        :returns: the current link node
        :rtype: :obj:`xml.etree.ElementTree.Element`
        """
        if node is not None:
            dsname = None
            dsnode = None

            dsname, dsnode = self.__getTextDataSource(
                node, linkdatasources)
            for child in node:
                cName = unicode(child.tag)
                if cName == 'datasource':
                    dsname = child.get("name")
                    if dsname in linkdatasources:
                        dsnode = child
                    else:
                        dsname, dsnode = self.__getTextDataSource(
                            child, linkdatasources)
                if dsnode is not None:
                    break
            if dsname:
                dsname = dsname.replace(" ", "_").replace("/", "_").replace(
                    ":", "_").replace(".", "_").replace("\\", "_").replace(
                        ";", "_").lower()
            if dsnode is not None:
                path = []
                path = [(node.get("name"), dsname)]
                for anc in reversed(ancestors):
                    path.append((anc[1], anc[2]))
                linkfound = False
                if entrynode is not None:
                    if linknode is None:
                        # found linknode
                        parent = entrynode
                        for nm, tp in linkpath:
                            node = None
                            for gchild in parent:
                                if gchild.get("name") == nm \
                                   and gchild.get("type") == tp:
                                    node = gchild
                                    break
                            if node is None:
                                break
                            else:
                                parent = node
                        else:
                            linknode = parent

                    if linknode is not None:
                        for dchild in linknode:
                            if dchild.get("name") == dsname:
                                linkfound = True
                                break
                    if not linkfound:
                        linknode = self.__createLink(
                            entrynode, linknode, path, linkpath)
        return linknode

    def __createLink(self, entrynode, linknode, path, linkpath=None):
        """ create link on given node

        :param entrynode: root node
        :type entrynode: :class:`xml.etree.ElementTree.Element`
        :param linknode: the given link node
        :type linknode: :obj:`xml.etree.ElementTree.Element`
        :param path: list with NeXus path (name, type)
        :type path: :obj:`list` < (:obj:`str`,:obj:`str`) >
        :param linkpath: list with NeXus path (name, type)
        :type linkpath: :obj:`list` < (:obj:`str`,:obj:`str`) >
        :returns: the current link node
        :rtype: :obj:`xml.etree.ElementTree.Element`
        """
        if path:
            target, dsname = path[0]
            if target:
                if linknode is None:
                    linknode = entrynode
                    if linkpath is None:
                        linkpath = [("data", "NXdata")]
                    for nm, tp in linkpath:
                        for gchild in linknode:
                            if gchild.get("name") == nm \
                                  and gchild.get("type") == tp:
                                linknode = gchild
                                break
                        else:
                            node = etree.Element("group")
                            linknode.append(node)
                            linknode = node
                            linknode.attrib["type"] = tp
                            linknode.attrib["name"] = nm
                for gname, gtype in path[1:]:
                    target = "%s:%s/" % (gname, gtype) + target
                target = "/" + target
                if dsname:
                    link = etree.Element("link")
                    linknode.append(link)
                    link.attrib["target"] = "%s" % target
                    link.attrib["name"] = dsname
        return linknode

    def collect(self, components):
        """ collects the given components in one DOM tree

        :param components: given components
        :type components: :obj:`list` <:obj:`str`>
        """
        self.__root = None
        rootDef = None
        for cp in components:
            dcp = None
            if cp:
                if sys.version_info > (3,):
                    cp = bytes(cp, "UTF-8")
                dcp = et.fromstring(cp, parser=XMLParser(collect_ids=False))
            if dcp is None:
                continue

            if self.__root is None:
                self.__root = dcp
                if dcp.tag != "definition":
                    raise UndefinedTagError("<definition> not defined")
                rootDef = dcp
            else:
                if dcp.tag != "definition":
                    raise UndefinedTagError("<definition> not defined")
                for cd in dcp:
                    rootDef.append(cd)
                txt = self.__getText(dcp)
                if txt and unicode(txt).strip():
                    if rootDef.text != txt:
                        rootDef.text += "\n" + txt

    def toString(self):
        """ Converts DOM tree to string

        :returns: DOM tree in XML string
        :rtype: :obj:`str`
        """
        if self.__root is not None:
            if sys.version_info > (3,):
                return "<?xml version='1.0' encoding='utf8'?>" + \
                    _tostr(
                        et.tostring(
                            self.__root, encoding='unicode', method='xml'))
            else:
                return _tostr(
                    et.tostring(
                        self.__root, encoding='utf8', method='xml'))

    def merge(self):
        """ performs the merging operation
        """
        self.__mergeChildren(self.__root, ())


if __name__ == "__main__":
    pass
