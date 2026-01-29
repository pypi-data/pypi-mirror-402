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

//! Implementation of the ``rust:enum`` directive

use syn::ItemEnum;

use crate::directives::directive_options::{DirectiveOption, DirectiveVisibility, IndexEntryType};
use crate::directives::struct_directive::StructDirective;
use crate::directives::{extract_doc_from_attrs, Directive, ImplDirective};
use crate::formats::{MdContent, MdDirective, RstContent, RstDirective};
use crate::nodes::{nodes_for_generics, nodes_for_where_clause, Node};

/// Struct to hold data for documenting an enum
#[derive(Clone, Debug)]
pub struct EnumDirective {
    /// The full Rust path of the enum, used as the name of the directive.
    pub(crate) name: String,
    /// The identifier for the enum.
    pub(crate) ident: String,
    /// The directive options to use.
    pub(crate) options: Vec<DirectiveOption>,
    /// The docstring for the enum.
    pub(crate) content: Vec<String>,
    /// The variants within the enum.
    pub(crate) variants: Vec<StructDirective>,
    /// Items within impl blocks for the enum.
    pub(crate) self_impls: Vec<ImplDirective>,
    /// Trait impls for the enum.
    pub(crate) trait_impls: Vec<ImplDirective>,
}

impl EnumDirective {
    const DIRECTIVE_NAME: &'static str = "enum";

    /// Create a new ``Directive::Enum`` from a ``syn::ItemEnum``
    ///
    /// Args:
    ///     :parent_path: The full path of the module the enum is in.
    ///     :item: The ``syn::ItemEnum`` to parse.
    ///
    /// Returns:
    ///     A new ``Directive::Enum``, which contains the parsed
    ///     ``EnumDirective`` in it.
    pub(crate) fn from_item(parent_path: &str, item: &ItemEnum) -> Directive {
        let name = format!("{}::{}", parent_path, item.ident);
        let variants = item
            .variants
            .iter()
            .map(|v| StructDirective::from_variant(&name, v, &Some(&item.vis)))
            .collect();

        let mut nodes = vec![
            Node::Keyword(EnumDirective::DIRECTIVE_NAME),
            Node::Space,
            Node::Name(item.ident.to_string()),
        ];
        nodes.extend(nodes_for_generics(&item.generics));
        if let Some(wc) = &item.generics.where_clause {
            nodes.extend(nodes_for_where_clause(wc));
        }

        let options = vec![
            DirectiveOption::Index(IndexEntryType::WithSubEntries),
            DirectiveOption::Vis(DirectiveVisibility::from(&item.vis)),
            DirectiveOption::Layout(nodes),
        ];

        Directive::Enum(EnumDirective {
            name,
            ident: item.ident.to_string(),
            options,
            content: extract_doc_from_attrs(&item.attrs),
            variants,
            self_impls: vec![],
            trait_impls: vec![],
        })
    }

    /// Return the visibility of this directive.
    pub(crate) fn directive_visibility(&self) -> &DirectiveVisibility {
        if let DirectiveOption::Vis(v) = &self.options[1] {
            return v;
        }
        unreachable!("Enum: order of options changed")
    }

    /// Change the parent module of the enum and its variants.
    pub(crate) fn change_parent(&mut self, new_parent: &str) {
        self.name = format!("{new_parent}::{}", self.ident);
        for variant in &mut self.variants {
            variant.change_parent(&self.name);
        }
        for impl_ in &mut self.self_impls {
            impl_.change_parent(new_parent);
        }
        for impl_ in &mut self.trait_impls {
            impl_.change_parent(new_parent);
        }
    }

    /// Add the impl directive to the enum.
    ///
    /// The parent and visibility of the impl directive are updated along with
    /// the ownership.
    ///
    /// Args:
    ///     :impl\_: The :rust:struct:`ImplDirective` for the enum.
    // noinspection DuplicatedCode
    pub(crate) fn add_impl(&mut self, mut impl_: ImplDirective) {
        // Set parent to the enum's parent for proper naming.
        impl_.change_parent(&self.name[0..self.name.rfind("::").unwrap()]);
        impl_.set_directive_visibility(self.directive_visibility());
        if impl_.trait_.is_some() {
            self.trait_impls.push(impl_);
        }
        else {
            self.self_impls.push(impl_);
        }
    }
}

impl RstDirective for EnumDirective {
    fn get_rst_text(self, level: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        if self.directive_visibility() > max_visibility {
            return vec![];
        }
        let content_indent = Self::make_indent(level + 1);

        let mut text =
            Self::make_rst_header(Self::DIRECTIVE_NAME, &self.name, &self.options, level);
        text.extend(self.content.get_rst_text(&content_indent));

        for variant in self.variants {
            text.extend(variant.get_rst_text(level + 1, max_visibility));
        }

        text.extend(Self::make_rst_section(
            "Implementations",
            level,
            self.self_impls.into_iter().map(Directive::Impl).collect(),
            max_visibility,
        ));

        text.extend(Self::make_rst_section(
            "Traits implemented",
            level,
            self.trait_impls.into_iter().map(Directive::Impl).collect(),
            max_visibility,
        ));

        text
    }
}

impl MdDirective for EnumDirective {
    fn get_md_text(self, fence_size: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        if self.directive_visibility() > max_visibility {
            return vec![];
        }
        let fence = Self::make_fence(fence_size);

        let mut text =
            Self::make_md_header(Self::DIRECTIVE_NAME, &self.name, &self.options, &fence);
        text.extend(self.content.get_md_text());

        for variant in self.variants {
            text.extend(variant.get_md_text(fence_size - 1, max_visibility));
        }

        text.extend(Self::make_md_section(
            "Implementations",
            fence_size,
            self.self_impls.into_iter().map(Directive::Impl).collect(),
            max_visibility,
        ));

        text.extend(Self::make_md_section(
            "Traits implemented",
            fence_size,
            self.trait_impls.into_iter().map(Directive::Impl).collect(),
            max_visibility,
        ));

        text.push(fence);
        text
    }

    fn fence_size(&self) -> usize {
        [
            match self.variants.iter().map(StructDirective::fence_size).max() {
                Some(s) => s + 1,
                None => 3,
            },
            match self.trait_impls.iter().map(ImplDirective::fence_size).max() {
                Some(s) => s + 1,
                None => 3,
            },
            match self.self_impls.iter().map(ImplDirective::fence_size).max() {
                Some(s) => s + 1,
                None => 3,
            },
        ]
        .into_iter()
        .max()
        .unwrap()
    }
}
