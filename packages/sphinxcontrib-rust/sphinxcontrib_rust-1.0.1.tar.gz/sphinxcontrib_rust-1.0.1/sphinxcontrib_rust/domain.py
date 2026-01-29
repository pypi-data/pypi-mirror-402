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

"""Module for the ``rust`` Sphinx domain for documentation Rust items"""

from collections import defaultdict
from typing import Optional, Type, Union, Iterable

from docutils.nodes import Element
from docutils.parsers.rst import Directive
from sphinx.addnodes import pending_xref
from sphinx.builders import Builder
from sphinx.domains import Domain, Index, ObjType
from sphinx.environment import BuildEnvironment
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.nodes import make_refnode
from sphinx.util.typing import RoleFunction

from sphinxcontrib_rust.directives import RustDirective
from sphinxcontrib_rust.index import RustIndex
from sphinxcontrib_rust.items import RustItem, RustItemType

LOGGER = logging.getLogger(__name__)


class RustXRefRole(XRefRole):
    """An :py:class:`XRefRole` extension for Rust roles"""

    def process_link(
        self,
        env: BuildEnvironment,
        refnode: Element,
        has_explicit_title: bool,
        title: str,
        target: str,
    ) -> tuple[str, str]:
        """Process the link by parsing the title and the target"""
        # pylint: disable=too-many-arguments

        if not has_explicit_title:
            # This is the most common case where
            # only the target is specified as the title like
            # `` :rust:struct:`~crate::module::Struct` ``
            # title == target in this case

            # ~ will use only the final part of the name as the title
            # instead of the full path.
            if title[0:1] == "~":
                _, _, title = title[1:].rpartition("::")

            # Remove the ~ from the target, only meaningful for titles.
            target = target.lstrip("~")

        return title, target


class RustDomain(Domain):
    """The Sphinx domain for the Rust programming language.

    The domain provides the various roles and directives that can be used in the Sphinx
    documentation for linking with Rust code.
    """

    name = "rust"
    label = "Rust"

    # The various object types provided by the domain
    object_types: dict[str, ObjType] = {
        t.value: t.get_sphinx_obj_type() for t in RustItemType
    }

    # The various directives add to Sphinx for documenting the Rust object types
    directives: dict[str, Type[Directive]] = {
        t.value: d for t, d in RustDirective.get_directives().items()
    }

    # The various roles added to Sphinx for referencing the Rust object types
    # any is a wildcard role for any type.
    roles: dict[str, Union[RoleFunction, XRefRole]] = {
        **{r: RustXRefRole() for _, r in RustItemType.iter_roles()},
        "any": RustXRefRole(),
    }

    # The indices for all the object types
    indices: list[Type[Index]] = [RustIndex]

    # The domain data created by Sphinx. This is here just for type annotation.
    data: dict[str, dict[RustItemType, list[RustItem]] | dict[str, dict[str, str]]]

    # Initial data for the domain, gets copied as self.data by Sphinx
    initial_data = {
        "items": {t: [] for t in RustItemType},
        "uses": defaultdict(dict),
    }

    # Bump this when the data format changes.
    data_version = 0

    @property
    def items(self) -> dict[RustItemType, list[RustItem]]:
        """Return the Rust items with in the documentation"""
        return self.data["items"]

    @property
    def uses(self) -> dict[str, dict[str, str]]:
        """Return the dict of use statements per document within the documentation"""
        return self.data["uses"]

    def get_objects(self) -> Iterable[tuple[str, str, str, str, str, int]]:
        for _, objs in self.items.items():
            for obj in objs:
                yield (
                    obj.name,
                    obj.display_text,
                    obj.type_.value,
                    obj.docname,
                    obj.anchor,
                    obj.priority,
                )

    def clear_doc(self, docname: str) -> None:
        for typ, objs in self.items.items():
            self.items[typ][:] = [o for o in objs if o.docname != docname]

    def find_item_by_name(
        self, name: str, typ: str | None = None
    ) -> Optional[RustItem]:
        """Find a matching item based on the name and item type.

        This function checks for an item with the provided name. If a type is specified,
        only items of that type are considered.

        Args:
            :name: The name of the item to find.

        Kwargs:
            :typ=None: The item type to search for. This must be a valid :py:class:`RustItemType`
                value.

        Returns:
            The :py:class:`RustItem` for the item if found, and `None` otherwise.
        """
        search_types = (
            [
                RustItemType.from_str(typ),
                RustItemType.USE,
            ]  # Always include USE directives
            if typ and typ != "any"
            else self.items.keys()
        )

        matches = set()
        for search_type in search_types:
            matches.update(o for o in self.items[search_type] if o.name == name)

        # No match, return None
        if not matches:
            return None

        # Just 1 match, return it.
        if len(matches) == 1:
            return list(matches)[0]

        # Multiple matches, prefer a match that is not an impl.
        # This is likely to happen with a ref that matches a struct and the impl.
        for match in matches:
            if match.type_ != RustItemType.IMPL:
                return match

        # Return the first one if everything is an impl.
        return list(matches)[0]

    def find_item(
        self, fromdocname: str, target: str, typ: str | None = None
    ) -> Optional[RustItem]:
        """Find a matching item based on a reference target and item type.

        This function checks for an item that matches the provided reference target.
        There are 3 cases for the target, which are checked in order of priority:

            1. The target matches an item name directly.
            2. The target is relative to the current doc and the
               reference is in the doc where it is defined.
            3. The target is relative to a use directive in the current doc.

        Once a check matches an item, the item is returned and other cases are
        not evaluated.

        Args:
            :fromdocname: The document name in which the reference was found.
            :target: The target for the reference.

        Kwargs:
            :typ=None: The item type to search for. This must be a valid :py:class:`RustItemType`
                value.

        Returns:
            The :py:class:`RustItem` for the item if found, and `None` otherwise.
        """
        # Disambiguate
        target, typ = RustItemType.disambiguated_target(target, default_type=typ)

        # Try and match with exact name first
        if match := self.find_item_by_name(target, typ):
            return match

        # Try and match within the module
        uses = self.uses[fromdocname]
        if "self" in uses:
            if match := self.find_item_by_name(f"{uses['self']}::{target}", typ):
                return match

        # Try and match against one of the uses in the doc
        used_name, sep, member = target.partition("::")
        if used_name in uses:
            match = self.find_item_by_name(f"{uses[used_name]}{sep}{member}", typ)

        return match

    def resolve_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        typ: str,
        target: str,
        node: pending_xref,
        contnode: Element,
    ) -> Element | None:
        """Resolve a reference to a Rust item with the directive type specified"""
        # pylint:disable=too-many-arguments
        if match := self.find_item(fromdocname, target, typ):
            # If the item was a re-exported name, find its target with the same type.
            if match.type_ == RustItemType.USE:
                match = self.find_item(match.docname, match.reexport_of, typ)
        return (
            make_refnode(
                builder,
                fromdocname,
                match.docname,
                match.name.replace("::", "-"),
                [contnode],
                match.name,
            )
            if match
            else None
        )

    def resolve_any_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        target: str,
        node: pending_xref,
        contnode: Element,
    ) -> list[tuple[str, Element]]:
        """Resolve a reference to a Rust item with an unspecified directive type"""
        # pylint:disable=too-many-arguments
        match = self.find_item(fromdocname, target)
        if not match:
            return []
        if match.type_ == RustItemType.USE:
            match = self.find_item(match.docname, match.reexport_of)
            if not match:
                return []
        element = make_refnode(
            builder,
            fromdocname,
            match.docname,
            match.name.replace("::", "-"),
            [contnode],
            match.name,
        )
        return [(f"rust:{match.type_.value}", element)]

    def merge_domaindata(self, docnames: list[str], otherdata: dict) -> None:
        for typ, objs in otherdata["items"].items():
            self.items[typ].extend(o for o in objs if o.docname in docnames)
        for doc, uses in otherdata["uses"].items():
            self.uses[doc].update(uses)
