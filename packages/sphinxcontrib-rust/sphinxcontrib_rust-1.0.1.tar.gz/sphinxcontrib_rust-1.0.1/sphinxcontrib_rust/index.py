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

"""Module for code related to generating the index of Rust items"""

from collections import defaultdict
from typing import Iterable

# noinspection PyProtectedMember
from sphinx.locale import _  # pylint:disable=protected-access
from sphinx.domains import Index, IndexEntry

import sphinxcontrib_rust
from sphinxcontrib_rust.items import RustItemType, SphinxIndexEntryType


class RustIndex(Index):
    """Class for implementing the index of Rust items.

    The class inherits from :py:class:`Index` and produces an index of the
    various items documented in the build. The index sections are the item
    types.
    """

    # pylint: disable=too-few-public-methods

    name = "items"
    localname = _("Index of Rust items")
    shortname = _("Rust items")

    # Quoting avoids a circular import
    domain: "sphinxcontrib_rust.RustDomain"

    def generate(
        self, docnames: Iterable[str] | None = None
    ) -> tuple[list[tuple[str, list[IndexEntry]]], bool]:
        """Generate the index content for a list of items of the same type.

        Args:
            :items: The items to include in the index.
            :subtype: The sub-entry related type. One of
                0 - A normal entry
                1 - A entry with subtypes.
                2 - A sub-entry

        Returns:
            A list of ``(key, list[IndexEntry])`` tuples that can be used as the
            content for generating the index.
        """
        content = defaultdict(list)
        for item_type, items in self.domain.items.items():

            for item in items:
                # Skip items that don't have to be indexed
                if item.index_entry_type == SphinxIndexEntryType.NONE:
                    continue

                # Skip items that are not from the provided list of docnames, if any.
                if docnames and item.docname not in docnames:
                    continue

                if item.index_entry_type == SphinxIndexEntryType.SUB_ENTRY:
                    # find the appropriate section for the item
                    index_section = {
                        # Structs which are sub-entries are enum variants
                        RustItemType.STRUCT: RustItemType.ENUM,
                        # Variable which are sub-entries are struct fields
                        RustItemType.VARIABLE: RustItemType.STRUCT,
                        # Types which are sub-entries are trait's local types
                        RustItemType.TYPE: RustItemType.TRAIT,
                        # Functions which are sub-entries are trait's members
                        RustItemType.FUNCTION: RustItemType.TRAIT,
                    }[item.type_].index_section_name
                else:
                    index_section = item_type.index_section_name

                content[index_section].append(item)

        # Remove any empty sections
        empty_sections = [s for s, i in content.items() if not i]
        for section in empty_sections:
            content.pop(section)

        # Sort items within sections by name so the nesting works properly.
        for section, items in content.items():
            items.sort(key=lambda i: i.name)

        return (
            sorted(
                (s, [i.make_index_entry() for i in items])
                for s, items in content.items()
            ),
            True,
        )
