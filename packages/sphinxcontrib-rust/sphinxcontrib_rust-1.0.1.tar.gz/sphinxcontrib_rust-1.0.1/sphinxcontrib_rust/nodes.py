# sphinxcontrib_rust - Sphinx extension for the Rust programming language
# Copyright (C) 2024  Munir Contractor
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Module for creating docutils nodes from the JSON in the layout option of the directives"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import docutils.nodes
from sphinx import addnodes


class NodeType(Enum):
    """Types of the nodes for the Rust items in the signatures"""

    # XXX: Python 3.11 has StrEnum that can be used here
    NAME = "name"
    LINK = "link"
    KEYWORD = "keyword"
    PUNCTUATION = "punctuation"
    SPACE = "space"
    NEWLINE = "newline"
    INDENT = "indent"
    OPERATOR = "operator"
    RETURNS = "returns"
    LITERAL = "literal"
    LIFETIME = "lifetime"

    @classmethod
    def from_str(cls, value: str) -> "NodeType":
        """Get the node type enum from the string value"""
        for node_type in NodeType:
            if node_type.value == value:
                return node_type
        raise ValueError(f"Invalid value '{value}' for node type")


@dataclass
class Node:
    """A node in the document signatures that represents a Rust item.

    The node is a dataclass that encapsulates the details of a Rust token
    and how to format it in the signature. The type of the node indicates which docutils
    element type is used for docutils node of the output. The value is the text to display
    in the node. It is required for all node types except ``SPACE``, ``NEWLINE`` and ``RETURNS``.
    The ``target`` is only used for ``LINK`` nodes to generate a link to the target.
    """

    type: NodeType
    value: Optional[str] = None
    target: Optional[str] = None

    # Conversion of node types to docutils node, except for link.
    NODE_TYPE_DICT = {
        NodeType.NAME: addnodes.desc_sig_name,
        NodeType.KEYWORD: addnodes.desc_sig_keyword,
        NodeType.PUNCTUATION: addnodes.desc_sig_punctuation,
        NodeType.SPACE: addnodes.desc_sig_space,
        NodeType.INDENT: addnodes.desc_sig_space,
        NodeType.OPERATOR: addnodes.desc_sig_operator,
        NodeType.RETURNS: addnodes.desc_sig_operator,
        NodeType.LITERAL: addnodes.desc_sig_literal_string,
        NodeType.LIFETIME: addnodes.desc_sig_keyword,
    }

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = NodeType.from_str(self.type)

    @property
    def text(self) -> str:
        """Get the text for the node"""
        return {
            NodeType.SPACE: " ",
            NodeType.INDENT: "    ",
            NodeType.RETURNS: "->",
        }.get(self.type, self.value)

    def to_docutils_node(self) -> docutils.nodes.Node:
        """Convert a node to the appropriate docutils node.

        Returns:
            The docutils node for self, with any children node added.

        Raises:
            :ValueError: If called with a node of type ``NodeType.NEWLINE``.
                The newline does not have corresponding docutils node and
                instead must be handled by using the ``addnodes.desc_signature_line``.
        """
        # Handle the LINK nodes specially
        if self.type == NodeType.LINK:
            refnode = addnodes.pending_xref(
                "",
                refdomain="rust",
                reftype=None,  # Resolves to any item type
                reftarget=self.target,
            )
            refnode += addnodes.desc_sig_name(text=self.text)
            return refnode

        # All other types can be directly converted into a docutils node.
        # Use functions as the dict value to avoid calling all of them when creating the dict.
        return Node.NODE_TYPE_DICT[self.type](text=self.text)

    @classmethod
    def create_signature(
        cls, name: str, nodes: list["Node"]
    ) -> tuple[bool, list[docutils.nodes.Node]]:
        """Create a Rust item signature under the ``signode`` from the given ``nodes``

        The method will also add the generated nodes as children of the given ``signode``
        properly accounting for any multiline signatures. In case of multiline signatures,
        the permalink is added to the first line.

        Args:
            :name: The name of the item whose signature is to be generated.
            :nodes: The list of nodes with the layout of the signature.

        Returns:
            A tuple, whose first element indicates whether the signature is multiline or
            not and the second element is the list of nodes to add as a children for the
            signature.
        """
        name_node = addnodes.desc_name(name)

        # Split into lines while converting to docutils nodes
        lines = [[]]
        for node in nodes:
            if node.type == NodeType.NEWLINE:
                lines.append([])
            else:
                lines[-1].append(node.to_docutils_node())

        # Check if we need to handle multiple lines or not
        nodes = []
        if len(lines) == 1:
            is_multiline = False
            # For just 1 line, add the line to the name node
            name_node += lines[0]
            nodes.append(name_node)
        else:
            is_multiline = True
            # For multiline, fetch the first line and make it a permalink line.
            # XXX: Naming was difficult here, but essentially the first line of the
            #      docutils node is added to name node, and the name node is made a
            #      child of desc_signature_line node. Sphinx requires that all child
            #      nodes of a multiline signature are desc_signature_line nodes.

            name_line = lines.pop(0)
            name_node += name_line
            name_line_node = addnodes.desc_signature_line(add_permalink=True)
            name_line_node += name_node
            nodes.append(name_line_node)

            # For all other lines, create a desc_signature_line node and add the
            # line nodes directly under it. No need for a name node for these lines.
            for line in lines:
                line_node = addnodes.desc_signature_line()
                line_node += line
                nodes.append(line_node)

        return is_multiline, nodes
