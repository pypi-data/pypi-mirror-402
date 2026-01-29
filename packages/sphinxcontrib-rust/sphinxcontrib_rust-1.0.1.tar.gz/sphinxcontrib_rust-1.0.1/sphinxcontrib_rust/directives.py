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

"""Module for all the directive classes of the Rust domain"""

import json
from abc import ABC, abstractmethod
from typing import Sequence, Type

from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.addnodes import desc_signature
from sphinx.directives import ObjDescT, ObjectDescription
from sphinx.util import logging
from sphinx.util.nodes import make_id

# Used to avoid a circular import with the domain module.
import sphinxcontrib_rust
from sphinxcontrib_rust.items import RustItem, RustItemType, SphinxIndexEntryType
from sphinxcontrib_rust.nodes import Node, NodeType

LOGGER = logging.getLogger(__name__)


class RustDirective(ABC, ObjectDescription[Sequence[str]]):
    """Base class for Rust directives.

    This class implements most of the logic for the directives. For each directive,
    there is a subclass that overrides any directive specific behaviour.

    The input for the directives is generated with the Rust code in
    :rust:module:`sphinx_rustdocgen::directives`
    """

    option_spec = {
        "index": lambda arg: SphinxIndexEntryType(int(arg)),
        "vis": directives.unchanged,
        "toc": directives.unchanged,
        "layout": directives.unchanged,
    }

    @property
    @abstractmethod
    def rust_item_type(self) -> RustItemType:
        """The Rust object type for the directive"""
        raise NotImplementedError

    @classmethod
    def get_directives(cls) -> dict[RustItemType, Type["RustDirective"]]:
        """Get all the directives for the object types"""
        return {
            RustItemType.CRATE: RustCrateDirective,
            RustItemType.ENUM: RustEnumDirective,
            RustItemType.EXECUTABLE: RustExecutableDirective,
            RustItemType.FUNCTION: RustFunctionDirective,
            RustItemType.IMPL: RustImplDirective,
            RustItemType.MACRO: RustMacroDirective,
            RustItemType.MODULE: RustModuleDirective,
            RustItemType.STRUCT: RustStructDirective,
            RustItemType.TRAIT: RustTraitDirective,
            RustItemType.TYPE: RustTypeDirective,
            RustItemType.USE: RustUseDirective,
            RustItemType.VARIABLE: RustVariableDirective,
        }

    def add_target_and_index(
        self, name: Sequence[str], sig: str, signode: desc_signature
    ) -> None:
        """Adds the item to the domain and generates the index for it.

        This is called after :py:func:`handle_signature` has executed.

        Args:
            :name: The name of the item, which is the return value from
                :py:func:`handle_signature`.
            :sig: The argument to the directive, which is the Rust path
                of the item set by the Rust doc generator.
            :signode: The docutils node of the for item.
        """
        node_id = make_id(self.env, self.state.document, "", sig)
        signode["ids"].append(node_id)

        item = RustItem(
            name=sig,
            display_text=self.options.get("toc", name[-1]),
            type_=self.rust_item_type,
            docname=self.env.docname,
            anchor="-".join(name),  # Need to join with - for HTML anchors
            index_entry_type=self.options["index"],
            index_text=self.options.get(
                "toc", f"{self.rust_item_type.display_text} {name[-1]}"
            ),
            index_descr=(
                self.content[0]
                if self.content and not self.content[0].startswith("..")
                else ""
            ),
        )

        # Add to the domain
        domain = self.env.get_domain("rust")
        try:
            # This has to be imported from package at runtime to avoid circular imports.
            assert isinstance(domain, sphinxcontrib_rust.RustDomain)
        except AssertionError:
            LOGGER.exception(
                "Expected 'rust' domain to be of class %s, but found %s",
                sphinxcontrib_rust.RustDomain.__class__,
                domain.__class__,
            )
            raise

        domain.items[self.rust_item_type].append(item)

        if item.index_entry_type != SphinxIndexEntryType.NONE:
            # indexnode is created by the ``index`` directive and has one attribute,
            # ``entries``.  Its value is a list of 5-tuples of ``(entrytype, entryname,
            # target, ignored, key)``.

            # *entrytype* is one of "single", "pair", "double", "triple".

            # *key* is categorization characters (usually a single character) for
            # general index page. For the details of this, please see also:
            # :rst:dir:`glossary` and issue #2320 in Sphinx.

            self.indexnode["entries"].append(("single", sig, node_id, "", None))

    def handle_signature(self, sig: str, signode: addnodes.desc_signature) -> ObjDescT:
        """Handle the directive and generate its display signature.

        The display signature is what is displayed instead of the directive name and
        options in the generated output. The ``:sig:`` option of the directive is used
        to override the provided ``sig`` value. If the option is not set, the item type
        and the final component of the path are used.

        Raising ``ValueError`` will put the ``sig`` value into a single node, which
        is what the super implementation does.

        Args:
            :sig: The argument of the directive as set during doc generation, not the
                ``:sig:`` option. The Rust side of the code will put the full Rust path
                of the item as the argument.
            :signode: The docutils node for the item, to which the display signature nodes
                should be appended.

        Returns:
            The path for the object, which is a tuple of the Rust path components and
            defines the hierarchy of the object for indexing.
        """
        signode.path = tuple(sig.split("::"))

        if "layout" in self.options:
            layout = [Node(**n) for n in json.loads(self.options["layout"])]
        else:
            layout = [
                Node(NodeType.KEYWORD, value=self.rust_item_type.display_text),
                Node(NodeType.SPACE),
                Node(NodeType.NAME, value=signode.path[-1]),
            ]

        is_multiline, nodes = Node.create_signature(signode, layout)
        signode.is_multiline = is_multiline
        signode += nodes

        return signode.path

    def _object_hierarchy_parts(
        self, sig_node: addnodes.desc_signature
    ) -> tuple[str, ...]:
        """Returns the hierarchy of the object for indexing and de-duplication.

        Args:
            :sig_node: The docutils node of the for item.

        Returns:
            A tuple of the Rust path for the item, as set during the
            doc generation.
        """
        return sig_node.path

    def _toc_entry_name(self, sig_node: addnodes.desc_signature) -> str:
        """Generate the TOC entry for the item.

        For most directives, this is just the item type and identifier of the
        item. The ``:toc:`` option is set during doc generation where that is
        not sufficient (``impl`` blocks) or not desired (enum variants).

        Args:
            sig_node: The docutils node for the item.

        Returns:
            The text to display for the item in the TOC and sidebar.
        """
        return self.options.get(
            "toc", f"{self.rust_item_type.display_text} {sig_node.path[-1]}"
        )


class RustCrateDirective(RustDirective):
    """Directive for handling crate documentation"""

    @property
    def rust_item_type(self) -> RustItemType:
        return RustItemType.CRATE

    def _toc_entry_name(self, sig_node: addnodes.desc_signature) -> str:
        return ""


class RustEnumDirective(RustDirective):
    """Directive for handling enum documentation"""

    @property
    def rust_item_type(self) -> RustItemType:
        return RustItemType.ENUM


class RustExecutableDirective(RustDirective):
    """Directive for handling executable documentation"""

    @property
    def rust_item_type(self) -> RustItemType:
        return RustItemType.EXECUTABLE

    def _toc_entry_name(self, sig_node: addnodes.desc_signature) -> str:
        return ""


class RustFunctionDirective(RustDirective):
    """Directive for handling function documentation"""

    @property
    def rust_item_type(self) -> RustItemType:
        return RustItemType.FUNCTION


class RustImplDirective(RustDirective):
    """Directive for handling impl documentation"""

    @property
    def rust_item_type(self) -> RustItemType:
        return RustItemType.IMPL


class RustMacroDirective(RustDirective):
    """Directive for handling macro documentation"""

    @property
    def rust_item_type(self) -> RustItemType:
        return RustItemType.MACRO


class RustModuleDirective(RustDirective):
    """Directive for handling module documentation"""

    @property
    def rust_item_type(self) -> RustItemType:
        return RustItemType.MODULE

    def _toc_entry_name(self, sig_node: addnodes.desc_signature) -> str:
        return ""


class RustStructDirective(RustDirective):
    """Directive for handling struct documentation"""

    @property
    def rust_item_type(self) -> RustItemType:
        return RustItemType.STRUCT


class RustTraitDirective(RustDirective):
    """Directive for handling trait documentation"""

    @property
    def rust_item_type(self) -> RustItemType:
        return RustItemType.TRAIT


class RustTypeDirective(RustDirective):
    """Directive for handling type documentation"""

    @property
    def rust_item_type(self) -> RustItemType:
        return RustItemType.TYPE


class RustUseDirective(RustDirective):
    """Directive for handling the use statements in the file.

    This is a meta-directive that does not add content. Instead, it adds the used names for
    the document to the domain data and any re-exports to the domain items.

    .. note::

       This inherits from :py:class:`RustDirective` only to make it easier to work with.
       It does not behave like other directives.
    """

    @property
    def rust_item_type(self) -> RustItemType:
        return RustItemType.USE

    has_content = False
    option_spec = {
        "used_name": directives.unchanged_required,
        "reexport": directives.unchanged,
    }

    def run(self):
        try:
            signature = self.get_signatures()[0]
        except IndexError as ex:
            raise ValueError("Expected signature for use directive") from ex

        domain = self.env.get_domain("rust")
        try:
            # This has to be imported from package at runtime to avoid circular imports.
            assert isinstance(domain, sphinxcontrib_rust.RustDomain)
        except AssertionError:
            LOGGER.exception(
                "Expected 'rust' domain to be of class %s, but found %s",
                sphinxcontrib_rust.RustDomain.__class__,
                domain.__class__,
            )
            raise

        used_name = self.options["used_name"]
        domain.uses[self.env.docname][used_name] = signature
        if reexport := self.options.get("reexport"):
            item = RustItem(
                name=f"{reexport}::{used_name}",
                display_text="",
                type_=self.rust_item_type,
                docname=self.env.docname,
                index_entry_type=SphinxIndexEntryType.NONE,
                reexport_of=signature,
            )
            domain.items[self.rust_item_type].append(item)

        return []


class RustVariableDirective(RustDirective):
    """Directive for handling type documentation"""

    @property
    def rust_item_type(self) -> RustItemType:
        return RustItemType.VARIABLE
