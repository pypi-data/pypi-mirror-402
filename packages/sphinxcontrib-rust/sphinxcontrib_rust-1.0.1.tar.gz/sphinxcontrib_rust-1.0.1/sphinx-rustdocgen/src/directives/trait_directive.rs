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

//! Implementation of the ``rust:trait`` directive

use syn::{ItemTrait, ItemTraitAlias};

use crate::directives::directive_options::{DirectiveOption, DirectiveVisibility, IndexEntryType};
use crate::directives::{extract_doc_from_attrs, order_items, Directive, ImplDirective};
use crate::formats::{MdContent, MdDirective, RstContent, RstDirective};
use crate::nodes::{nodes_for_generics, nodes_for_where_clause, Node};

/// Struct to hold details for documenting a trait.
#[derive(Clone, Debug)]
pub struct TraitDirective {
    /// The full Rust path of the trait, used as the name of the directive.
    pub(crate) name: String,
    /// The identifier for the trait.
    pub(crate) ident: String,
    /// The directive options to use.
    pub(crate) options: Vec<DirectiveOption>,
    /// The docstring for the trait.
    pub(crate) content: Vec<String>,
    /// Items within the trait.
    pub(crate) items: Vec<Directive>,
    /// Generic impls of the trait.
    pub(crate) impls: Vec<ImplDirective>,
}

impl TraitDirective {
    const DIRECTIVE_NAME: &'static str = "trait";

    /// Create a trait directive from the trait definition.
    // noinspection DuplicatedCode
    pub(crate) fn from_item(parent_path: &str, item: &ItemTrait) -> Directive {
        let name = format!("{}::{}", parent_path, item.ident);

        let mut nodes = vec![];
        if item.unsafety.is_some() {
            nodes.push(Node::Keyword("unsafe"));
            nodes.push(Node::Space);
        }
        nodes.push(Node::Keyword(Self::DIRECTIVE_NAME));
        nodes.push(Node::Space);
        nodes.push(Node::Name(item.ident.to_string()));
        nodes.extend(nodes_for_generics(&item.generics));
        if let Some(wc) = &item.generics.where_clause {
            nodes.extend(nodes_for_where_clause(wc));
        }

        let options = vec![
            DirectiveOption::Index(IndexEntryType::WithSubEntries),
            DirectiveOption::Vis(DirectiveVisibility::from(&item.vis)),
            DirectiveOption::Layout(nodes),
        ];

        let items = Directive::from_trait_items(&name, item.items.iter(), &Some(&item.vis));

        Directive::Trait(TraitDirective {
            name,
            ident: item.ident.to_string(),
            options,
            content: extract_doc_from_attrs(&item.attrs),
            items,
            impls: vec![],
        })
    }

    // noinspection DuplicatedCode
    /// Create a trait directive from a trait alias.
    pub(crate) fn from_alias(parent_path: &str, alias: &ItemTraitAlias) -> Directive {
        let name = format!("{}::{}", parent_path, alias.ident);

        let mut nodes = vec![
            Node::Keyword(Self::DIRECTIVE_NAME),
            Node::Space,
            Node::Name(alias.ident.to_string()),
        ];
        nodes.extend(nodes_for_generics(&alias.generics));
        if let Some(wc) = &alias.generics.where_clause {
            nodes.extend(nodes_for_where_clause(wc));
        }

        let options = vec![
            DirectiveOption::Index(IndexEntryType::Normal),
            DirectiveOption::Vis(DirectiveVisibility::from(&alias.vis)),
            DirectiveOption::Layout(nodes),
        ];

        Directive::Trait(TraitDirective {
            name,
            ident: alias.ident.to_string(),
            options,
            content: extract_doc_from_attrs(&alias.attrs),
            items: vec![],
            impls: vec![],
        })
    }

    /// Return the visibility of this directive.
    pub(crate) fn directive_visibility(&self) -> &DirectiveVisibility {
        if let DirectiveOption::Vis(v) = &self.options[1] {
            return v;
        }
        unreachable!("Trait: order of options changed")
    }

    /// Change the parent module of the trait and its items.
    pub(crate) fn change_parent(&mut self, new_parent: &str) {
        self.name = format!("{new_parent}::{}", self.ident);
        for item in &mut self.items {
            item.change_parent(&self.name);
        }
        for impl_ in &mut self.impls {
            impl_.change_parent(new_parent);
        }
    }

    /// Add the impl directive to the trait.
    ///
    /// The parent and visibility of the impl directive are updated along with
    /// the ownership.
    ///
    /// Args:
    ///     :impl\_: The :rust:struct:`ImplDirective` for the trait.
    pub(crate) fn add_impl(&mut self, mut impl_: ImplDirective) {
        impl_.change_parent(&self.name[0..self.name.rfind("::").unwrap()]);
        impl_.set_directive_visibility(self.directive_visibility());
        self.impls.push(impl_);
    }
}

impl RstDirective for TraitDirective {
    fn get_rst_text(self, level: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        if self.directive_visibility() > max_visibility {
            return vec![];
        }
        let content_indent = Self::make_content_indent(level);

        let mut text =
            Self::make_rst_header(Self::DIRECTIVE_NAME, &self.name, &self.options, level);
        text.extend(self.content.get_rst_text(&content_indent));

        for (section, items) in order_items(self.items) {
            text.extend(Self::make_rst_section(
                section,
                level,
                items,
                max_visibility,
            ));
        }

        text.extend(Self::make_rst_section(
            "Implemented for",
            level,
            self.impls.into_iter().map(Directive::Impl).collect(),
            max_visibility,
        ));

        text
    }
}

impl MdDirective for TraitDirective {
    fn get_md_text(self, fence_size: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        if self.directive_visibility() > max_visibility {
            return vec![];
        }
        let fence = Self::make_fence(fence_size);

        let mut text =
            Self::make_md_header(Self::DIRECTIVE_NAME, &self.name, &self.options, &fence);
        text.extend(self.content.get_md_text());

        for (section, items) in order_items(self.items) {
            text.extend(Self::make_md_section(
                section,
                fence_size,
                items,
                max_visibility,
            ));
        }

        text.extend(Self::make_md_section(
            "Implemented for",
            fence_size,
            self.impls.into_iter().map(Directive::Impl).collect(),
            max_visibility,
        ));

        text.push(fence);
        text
    }

    fn fence_size(&self) -> usize {
        [
            Self::calc_fence_size(&self.items),
            match self.impls.iter().map(ImplDirective::fence_size).max() {
                Some(s) => s + 1,
                None => 3,
            },
        ]
        .into_iter()
        .max()
        .unwrap()
    }
}
