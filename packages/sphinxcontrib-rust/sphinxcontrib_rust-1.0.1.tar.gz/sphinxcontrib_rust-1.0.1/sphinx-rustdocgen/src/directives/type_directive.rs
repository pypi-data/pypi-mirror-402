// sphinxcontrib_rust - Sphinx extension for the Rust programming language
// Copyright (C) 2024  Munir Contractor
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

//! Implementation of the ``rust:type`` directive

use syn::{ForeignItemType, ImplItemType, ItemType, TraitItemType, Visibility};

use crate::directives::directive_options::{DirectiveOption, DirectiveVisibility, IndexEntryType};
use crate::directives::{extract_doc_from_attrs, Directive};
use crate::formats::{MdContent, MdDirective, RstContent, RstDirective};
use crate::nodes::{nodes_for_generics, nodes_for_where_clause, Node};

/// Struct to hold the data for documenting type definitions.
#[derive(Clone, Debug)]
pub struct TypeDirective {
    /// The Rust path of the type.
    pub(crate) name: String,
    /// The identifier of the type.
    pub(crate) ident: String,
    /// The options of the directive.
    pub(crate) options: Vec<DirectiveOption>,
    /// The content of the directive.
    pub(crate) content: Vec<String>,
}

/// DRY macro to create :rust:struct:`TypeDirective` from various syn structs.
macro_rules! type_from_item {
    ($parent_path:expr, $item:expr, $vis:expr, $inherited:expr, $index:expr) => {{
        let name = format!("{}::{}", $parent_path, &$item.ident);

        let mut nodes = vec![
            Node::Keyword(TypeDirective::DIRECTIVE_NAME),
            Node::Space,
            Node::Name($item.ident.to_string()),
        ];
        nodes.extend(nodes_for_generics(&$item.generics));
        if let Some(wc) = &$item.generics.where_clause {
            nodes.extend(nodes_for_where_clause(wc));
        }

        let options = vec![
            DirectiveOption::Index($index),
            DirectiveOption::Vis(DirectiveVisibility::effective_visibility(&$vis, $inherited)),
            DirectiveOption::Layout(nodes),
        ];

        TypeDirective {
            name,
            ident: $item.ident.to_string(),
            options,
            content: extract_doc_from_attrs(&$item.attrs),
        }
    }};
}

impl TypeDirective {
    const DIRECTIVE_NAME: &'static str = "type";

    /// Create a type directive from a type definition.
    pub(crate) fn from_item(parent_path: &str, item: &ItemType) -> Directive {
        Directive::Type(type_from_item!(
            parent_path,
            item,
            item.vis,
            &None,
            IndexEntryType::Normal
        ))
    }

    /// Create a type directive from a type definition within an impl block.
    pub(crate) fn from_impl_item(
        parent_path: &str,
        item: &ImplItemType,
        inherited_visibility: &Option<&Visibility>,
    ) -> Directive {
        Directive::Type(type_from_item!(
            parent_path,
            item,
            item.vis,
            inherited_visibility,
            IndexEntryType::None
        ))
    }

    /// Create a type directive from a type definition within a trait
    /// definition.
    pub(crate) fn from_trait_item(
        parent_path: &str,
        item: &TraitItemType,
        inherited_visibility: &Option<&Visibility>,
    ) -> Directive {
        Directive::Type(type_from_item!(
            parent_path,
            item,
            Visibility::Inherited,
            inherited_visibility,
            IndexEntryType::SubEntry
        ))
    }

    /// Create a type directive from a foreign type definition.
    pub(crate) fn from_extern(parent_path: &str, item: &ForeignItemType) -> Directive {
        Directive::Type(type_from_item!(
            parent_path,
            item,
            item.vis,
            &None,
            IndexEntryType::Normal
        ))
    }

    /// Return the visibility of this directive.
    pub(crate) fn directive_visibility(&self) -> &DirectiveVisibility {
        if let DirectiveOption::Vis(v) = &self.options[1] {
            return v;
        }
        unreachable!("Type: order of options changed")
    }

    /// Change the parent module of the type.
    pub(crate) fn change_parent(&mut self, new_parent: &str) {
        self.name = format!("{new_parent}::{}", self.ident);
    }
}

impl RstDirective for TypeDirective {
    // noinspection DuplicatedCode
    fn get_rst_text(self, level: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        if self.directive_visibility() > max_visibility {
            return vec![];
        }
        let content_indent = Self::make_content_indent(level);

        let mut text =
            Self::make_rst_header(Self::DIRECTIVE_NAME, &self.name, &self.options, level);
        text.extend(self.content.get_rst_text(&content_indent));

        text
    }
}

impl MdDirective for TypeDirective {
    // noinspection DuplicatedCode
    fn get_md_text(self, fence_size: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        if self.directive_visibility() > max_visibility {
            return vec![];
        }
        let fence = Self::make_fence(fence_size);

        let mut text =
            Self::make_md_header(Self::DIRECTIVE_NAME, &self.name, &self.options, &fence);
        text.extend(self.content.get_md_text());

        text.push(fence);
        text
    }
}
