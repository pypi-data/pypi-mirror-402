"""A high-level abstraction layer for creating and editing XML documents.

This module provides the following class definitions:

* XDocument - A defined class for creating, loading, and saving an XML document
* XElement  - A defined class which represents an XML document element
"""

__version__ = '1.3.1'

import os
from typing import Any, List, Union
from xml.dom.minidom import getDOMImplementation, Document, Element, Text
import defusedxml.minidom as defused


class XElement:
    """A class which represents an XML document element."""

    def __init__(self, document: Document, node: Element):
        """Create a new XML document element.

        Parameters
        ----------
        document: Document
            The XML document
        node: Element
            The XML document node
        """
        self._doc = document
        self._node = node

    def __eq__(self, other: Any) -> bool:
        """Test for identical XElements (self == other)."""
        return isinstance(other, XElement) and other.node == self._node

    def __repr__(self) -> str:
        """Generate a string representation of the XElement."""
        return f'{type(self).__name__}: <{self.name}>'

    def __str__(self) -> str:
        """Generate a description string of the XElement."""
        return f'{type(self).__name__}: <{self.name}>'

    @property
    def attributes(self) -> List[str]:
        """Get a list of all the attributes of this element."""
        attribute_list: List[str] = []
        if self._node.hasAttributes():
            for name in self._get_attributes().keys():
                value = self.read_attribute(name)
                attribute_list.append(f'{name}="{value}"')
        return attribute_list

    @property
    def children(self) -> List['XElement']:
        """Get a list of all the child elements of this element."""
        child_list: List[XElement] = []
        for node in self._node.childNodes:
            if isinstance(node, Element):
                child_list.append(XElement(self._doc, node))
        return child_list

    @property
    def first_attribute(self) -> str:
        """Get the first attribute of this element."""
        return '' if not self._node.hasAttributes() else self.attributes[0]

    @property
    def first_child(self) -> Union['XElement', None]:
        """Get the first child element of this element."""
        return None if not self.has_children else self.children[0]

    @property
    def has_attributes(self) -> bool:
        """True if this element has at least one attribute."""
        return self._node.hasAttributes()

    @property
    def has_children(self) -> bool:
        """True if this element has at least one child element."""
        return any(isinstance(node, Element) for node in self._node.childNodes)

    @property
    def last_attribute(self) -> str:
        """Get the last attribute of this element."""
        return '' if not self._node.hasAttributes() else self.attributes[-1]

    @property
    def last_child(self) -> Union['XElement', None]:
        """Get the last child element of this element."""
        return None if not self.has_children else self.children[-1]

    @property
    def level(self) -> int:
        """Get the zero-based depth of this element in the hierarchy."""
        level = 0
        parent = self._node.parentNode
        while isinstance(parent, Element):
            level += 1
            parent = parent.parentNode
        return level

    @property
    def name(self) -> str:
        """Get/Set the name of this element."""
        return self._node.tagName

    @name.setter
    def name(self, text: str) -> None:
        """Get/Set the name of this element."""
        if self._node != self._doc.documentElement:
            self._node.tagName = self._node.nodeName = text.strip()

    @property
    def node(self) -> Element:
        """Get the internal XML document node of this element."""
        return self._node

    @property
    def parent(self) -> Union['XElement', None]:
        """Get the parent element of this element."""
        parent = None
        if isinstance(self._node.parentNode, Element):
            parent = XElement(self._doc, self._node.parentNode)
        return parent

    @property
    def value(self) -> str:
        """Get/Set the text content of this element."""
        text = ''
        first_child = self._node.firstChild
        if isinstance(first_child, Text):
            text = first_child.nodeValue
        return '' if '\n' in text else text

    @value.setter
    def value(self, text: str) -> None:
        """Get/Set the text content of this element."""
        if self._node != self._doc.documentElement:
            first_child = self._node.firstChild
            if isinstance(first_child, Text):
                first_child.nodeValue = text
                if not (text or self.has_children) and self.parent is not None:
                    self.parent.replace_element(self, self.clone(False))
            elif text:  # Insert a new text field
                self._node.insertBefore(
                    self._doc.createTextNode(text), first_child
                )

    def add(self, name: str, attr: str = '', value: Any = None) -> 'XElement':
        """Create and add a new child element.

        Parameters
        ----------
        name : str
            The name of the child element
        attr : str
            The name of the optional attribute
        value : Any
            The value of the optional attribute

        Returns
        -------
        XElement
            The newly created child element
        """
        node = self._doc.createElement(name.strip())
        attr = '' if attr is None else attr.strip()
        text = '' if value is None else str(value)
        if attr and text:
            node.setAttributeNode(self._doc.createAttribute(attr))
            node.setAttribute(attr, text)
        return self.add_element(XElement(self._doc, node))

    def add_comment(self, text_field: str) -> None:
        """Create and add a comment to the element.

        Parameters
        ----------
        text_field : str
            The text field of the comment
        """
        node = self._doc.createComment(text_field.replace('--', '').strip())
        self._append_formatted_element(node)

    def add_element(self, element: 'XElement') -> 'XElement':
        """Add an existing element as a child element.

        Parameters
        ----------
        element : XElement
            The existing element

        Returns
        -------
        XElement
            The added child element
        """
        if element is not None:
            self._append_formatted_element(element.node)
        return element

    def clone(self, deep: bool = True) -> 'XElement':
        """Create and return a copy of this element.

        Parameters
        ----------
        deep : bool
            if True, include all the descendant elements (default = True)

        Returns
        -------
            A copy of this element
        """
        element = XElement(self._doc, self._node)
        if deep or self._node.hasAttributes():
            clone = self._node.cloneNode(deep)
        else:
            clone = self._doc.createElement(self._node.tagName)
            if isinstance(self._node.firstChild, Text):
                text = self._node.firstChild.nodeValue
                if text and '\n' not in text:
                    clone.appendChild(self._doc.createTextNode(text))

        if clone is not None:
            element = XElement(self._doc, clone)
        if not deep and self.has_attributes:
            element.remove_all()
        return element

    def find_child(self, name: str) -> Union['XElement', None]:
        """Find the first child of this element with the specified name.

        Parameters
        ----------
        name : str
            The specified name of the child element

        Returns
        -------
        XElement | None
            The first matching child element if found, otherwise None
        """
        element = None
        name = name.strip()
        for node in self._node.childNodes:
            if isinstance(node, Element) and node.tagName == name:
                element = XElement(self._doc, node)
                break
        return element

    def find_descendants(self, name: str = '*') -> List['XElement']:
        """Find all the descendants of this element with the specified name.

        Parameters
        ----------
        name : str
            The specified name (include all descendants if the name is '*')

        Returns
        -------
        List[XElement]
            A list of all descendant elements with the specified name
        """
        node_list = self._node.getElementsByTagName(name.strip())
        return [XElement(self._doc, node) for node in node_list]

    def insert_element(
        self, ref_element: 'XElement', new_element: 'XElement'
    ) -> 'XElement':
        """Insert a new child element before the referenced child element.

        Parameters
        ----------
        ref_element : XElement
            The existing referenced child
        new_element : XElement
            The element to be inserted

        Returns
        -------
        XElement
            The newly inserted child element
        """
        if not (new_element is None or ref_element is None):
            ref_node = ref_element.node
            level = ref_element.level
            if ref_node in self._node.childNodes:
                self._indent_children(level, new_element.node)
                self._node.insertBefore(new_element.node, ref_node)
                self._node.insertBefore(self._new_line(level), ref_node)
            else:
                self._append_formatted_element(new_element.node)
        return new_element

    def read_attribute(self, name: str) -> str:
        """Read the value of the named attribute.

        Parameters
        ----------
        name : str
            The name of the attribute

        Returns
        -------
        str
            The value of the attribute if found, otherwise an empty string
        """
        text = ''
        name = name.strip()
        if self._node.hasAttribute(name):
            text = self._node.getAttribute(name)
        return text

    def read_child(self, name: str, default: Any = None) -> Any:
        """Read the value of the named child element.

        The default parameter value type determines the return value type. When
        the default parameter is None, the return value type is a string.

        Parameters
        ----------
        name : str
            The name of the child element
        default : Any
            The default return value (None equates to an empty string)

        Returns
        -------
        Any
            The value of the child if found, otherwise the default value
        """
        text = ''
        result: Any = '' if default is None else default
        element = self.find_child(name)
        if element is not None:
            text = element.value
        if text:
            try:
                if isinstance(default, bool):
                    result = text.strip().lower() == 'true'
                elif isinstance(default, int):
                    result = round(float(text))
                elif isinstance(default, float):
                    result = float(text)
                else:
                    result = text
            except ValueError:
                pass  # Return the default value
        return result

    def remove(self, name: str) -> Union['XElement', None]:
        """Remove the named child element.

        Parameters
        ----------
        name : str
            The name of the child element

        Returns
        -------
        XElement | None
            The removed child element if successful, otherwise None
        """
        child_element = self.find_child(name)
        if child_element is not None:
            child_element = self.remove_element(child_element)
        return child_element

    def remove_all(self) -> None:
        """Remove all children and comments from this element."""
        for element in self.children:
            self.remove_element(element)
        self._collapse_element()

    def remove_all_attributes(self) -> None:
        """Remove all attributes from this element."""
        while self._node.hasAttributes():
            attribute_node = list(self._get_attributes().values())[0]
            self._node.removeAttributeNode(attribute_node)

    def remove_attribute(self, name: str) -> None:
        """Remove the named attribute from this element.

        Parameters
        ----------
        name : str
            The name of the attribute
        """
        name = name.strip()
        if self._node.hasAttribute(name):
            attribute_node = self._get_attributes()[name]
            self._node.removeAttributeNode(attribute_node)

    def remove_element(self, element: 'XElement') -> Union['XElement', None]:
        """Remove the specified child element.

        Parameters
        ----------
        element : XElement
            The specified child element

        Returns
        -------
        XElement | None
            The removed child element if successful, otherwise None
        """
        old_element = None
        if element is not None:
            if element.node in self._node.childNodes:
                previous_node = element.node.previousSibling
                if isinstance(previous_node, (Element, Text)):
                    self._node.removeChild(previous_node).unlink()
                old_node = self._node.removeChild(element.node)
                old_element = XElement(self._doc, old_node)
            if all(isinstance(node, Text) for node in self._node.childNodes):
                self._collapse_element()
        return old_element

    def replace_element(
        self, old_element: 'XElement', new_element: 'XElement'
    ) -> 'XElement':
        """Replace an existing child element with a new child element.

        Parameters
        ----------
        old_element : XElement
            The existing child element
        new_element : XElement
            The replacement child element

        Returns
        -------
        XElement
            The new child element
        """
        if not (new_element is None or old_element is None):
            if old_element.node in self._node.childNodes:
                self._indent_children(old_element.level, new_element.node)
                self._node.replaceChild(new_element.node, old_element.node)
        return new_element

    def write_attribute(self, name: str, value: Any) -> None:
        """Write a new value to the named attribute.

        Parameters
        ----------
        name : str
            The name of the attribute (the attribute is added if not present)
        value : Any
            The new value of the attribute
        """
        name = name.strip()
        text = '' if value is None else str(value)
        if name and text and self._node is not self._doc.documentElement:
            if not self._node.hasAttribute(name):
                self._node.setAttributeNode(self._doc.createAttribute(name))
            self._node.setAttribute(name, text)

    def write_child(self, name: str, value: Any) -> None:
        """Write a new value to the named child element.

        Parameters
        ----------
        name : str
            The name of the child element (a new element is added if not found)
        value : Any
            The new value of the named child element
        """
        name = name.strip()
        text = '' if value is None else str(value)
        element = self.find_child(name)
        if element is not None:
            element.value = text
        elif name:  # Create and append a new element with a text field
            node = self._doc.createElement(name)
            if text:
                node.appendChild(self._doc.createTextNode(text))
            self._append_formatted_element(node)

    def _append_formatted_element(self, node: Any) -> None:
        """Append the element with the appropriate formatting TextNodes."""
        if self._node.hasChildNodes():
            last_node = self._node.lastChild
            if isinstance(last_node, (Element, Text)):
                self._node.removeChild(last_node).unlink()
        level = self.level
        self._node.appendChild(self._new_line(level + 1))
        self._indent_children(level + 1, node)
        self._node.appendChild(node)
        self._node.appendChild(self._new_line(level))

    def _collapse_element(self) -> None:
        """Fully collapse this element."""
        if self.parent is not None:
            self.parent.replace_element(self, self.clone(False))
        elif self._node is self._doc.documentElement:
            while self._node.lastChild is not None:
                self._node.removeChild(self._node.lastChild)

    def _get_attributes(self) -> dict:
        """Get the current dictionary of the attribute nodes."""
        # noinspection PyProtectedMember
        # pylint: disable=protected-access
        return self._node._attrs  # type: ignore

    def _indent_children(self, level: int, node: Element) -> None:
        """Format the children nodes with the correct indentation."""
        if len(node.childNodes) > 1:
            for child in node.childNodes:
                if isinstance(child, Text) and '\n' in child.nodeValue:
                    text = '\n'.ljust(2 * level + 3)
                    value = text[0:-2] if child == node.lastChild else text
                    # noinspection PyTypeChecker
                    child.nodeValue = value
                elif isinstance(child, Element):
                    self._indent_children(level + 1, child)

    def _new_line(self, level: int) -> Text:
        """Create a 'newline' formatting TextNode with correct indentation."""
        return self._doc.createTextNode('\n'.ljust(2 * level + 1))


class XDocument:
    """A class for creating, loading, and saving an XML document."""

    _filename: str  # The XML document filename
    _doc: Document  # The XML document
    _root: Element  # The XML document root element

    def __init__(
        self,
        filename: str,
        root_name: str = '',
        comment: str = '',
        details: Any = None,
    ):
        """Create an XML document from the specified XML document file.

        If the specified XML document file does not exist, a new XML document
        is created, initialized, and saved as a new XML document file.

        Parameters
        ----------
        filename : str
            The full filename of the specified XML document file
        root_name : str
            The optional XML document root name (the default is the class name)
        comment : str
            The optional XML document comment text string
        details: Any
            The optional initialization details for the derived subclass
        """
        root_name = '' if root_name is None else root_name.strip()
        comment = '' if comment is None else comment.replace("--", "").strip()
        self._root_name = type(self).__name__ if not root_name else root_name
        self._comment = comment
        self._details = details
        self._initialize = True
        self.load(filename)
        self._initialize = False

    def _subclass_details(self) -> None:
        """Provide the initialization details for the derived subclass.

        This method is only called during the class initialization when the
        specified XML document file does not exist. Overriding this method
        allows the user to provide the default implementation details
        in the user's derived subclass.
        """
        if self._details is not None:
            pass  # Add the default implementation details here

    @property
    def root(self) -> XElement:
        """Get the root element of the XML document."""
        return XElement(self._doc, self._root)

    def create_element(self, name: str) -> XElement:
        """Create a new element for the XML document.

        Parameters
        ----------
        name : str
            The name of the element

        Returns
        -------
        XElement
            The newly created element for the XML document
        """
        node = self._doc.createElement(name.strip())
        return XElement(self._doc, node)

    def load(self, filename: str) -> None:
        """Load a new XML document from the specified XML document file.

        If the specified XML document file does not exist, this method
        creates an 'empty' XML document which contains only the root element.

        Parameters
        ----------
        filename : str
            The full filename of the specified XML document file
        """
        self._filename = filename
        if os.path.isfile(filename):  # Read the XML document file
            self._doc = defused.parse(self._filename)
            root_node = self._doc.documentElement
            if isinstance(root_node, Element):
                self._root = root_node

        else:  # Create a new default XML document
            ipl = getDOMImplementation()
            if ipl is not None:
                self._doc = ipl.createDocument(None, self._root_name, None)
                root_node = self._doc.documentElement
                if isinstance(root_node, Element):
                    self._root = root_node
                    if self._initialize:  # Provide the subclass details
                        self._subclass_details()
                        self.save()

    def save(self, filename: str = '') -> None:
        """Save the XML document to the specified XML document file.

        Parameters
        ----------
        filename : str
            The optional filename (the default is the current filename)
        """
        output: str = self._doc.toxml()
        header = output.find('?>')
        body_start = header + 2
        xml_body = output[body_start:]
        if self._initialize and self._comment:
            xml_body = f'<!--{self._comment}-->' + xml_body
        output = output[0:header] + 'encoding="utf-8"?>\n' + xml_body

        header = output.find('\n')
        if output[header + 2] == '!':
            comment = output.find('-->') + 3
            output = output[0:comment] + '\n' + output[comment:]

        utf_8_bom = bytes([0xEF, 0xBB, 0xBF]).decode()
        filename = self._filename if not filename else filename
        with open(filename, 'w', encoding='utf-8') as new_xml:
            new_xml.write(utf_8_bom + output)
