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

//! Implementation of the ``rust:struct`` directive

use syn::{Fields, Generics, ItemStruct, ItemUnion, Variant, Visibility};

use crate::directives::directive_options::{DirectiveOption, DirectiveVisibility, IndexEntryType};
use crate::directives::variable_directive::VariableDirective;
use crate::directives::{extract_doc_from_attrs, Directive, ImplDirective};
use crate::formats::{MdContent, MdDirective, RstContent, RstDirective};
use crate::nodes::{nodes_for_generics, nodes_for_type, nodes_for_where_clause, Node};

/// Struct to hold details for documenting a struct or a union.
#[derive(Clone, Debug)]
pub struct StructDirective {
    /// The full Rust path of the struct, used as the name of the directive.
    pub(crate) name: String,
    /// The identifier for the struct.
    pub(crate) ident: String,
    /// The directive options to use.
    pub(crate) options: Vec<DirectiveOption>,
    /// The docstring for the struct.
    pub(crate) content: Vec<String>,
    /// The fields of the struct, named or unnamed.
    pub(crate) fields: Vec<VariableDirective>,
    /// Items within impl blocks for the struct/union.
    pub(crate) self_impls: Vec<ImplDirective>,
    /// Trait impls for the struct/union.
    pub(crate) trait_impls: Vec<ImplDirective>,
}

/// DRY macro to create the nodes for the directive's layout.
macro_rules! make_nodes {
    ($ident:expr, $fields:expr, $generics:expr, $item_keyword:expr) => {{
        let mut nodes = if let Some(keyword) = $item_keyword {
            vec![
                Node::Keyword(keyword),
                Node::Space,
                Node::Name($ident.to_string()),
            ]
        }
        else {
            vec![Node::Name($ident.to_string())]
        };

        if let Some(generics) = $generics {
            nodes.extend(nodes_for_generics(generics));
        }

        if let Fields::Unnamed(fields) = &$fields {
            nodes.push(Node::Punctuation("("));
            for field in &fields.unnamed {
                nodes.extend(nodes_for_type(&field.ty));
                nodes.push(Node::Punctuation(", "));
            }
            nodes.pop();
            nodes.push(Node::Punctuation(")"));
        }

        if let Some(generics) = $generics {
            if let Some(wc) = &generics.where_clause {
                nodes.extend(nodes_for_where_clause(wc));
            }
        }

        nodes
    }};
}

impl StructDirective {
    const DIRECTIVE_NAME: &'static str = "struct";

    /// Create a struct directive for an enum variant.
    pub(crate) fn from_variant(
        parent_path: &str,
        variant: &Variant,
        inherited_visibility: &Option<&Visibility>,
    ) -> StructDirective {
        let name = format!("{}::{}", parent_path, variant.ident);

        let options = vec![
            DirectiveOption::Index(IndexEntryType::SubEntry),
            DirectiveOption::Vis(DirectiveVisibility::from(inherited_visibility.unwrap())),
            DirectiveOption::Toc(variant.ident.to_string()),
            DirectiveOption::Layout(make_nodes!(
                variant.ident,
                variant.fields,
                None::<&Generics>,
                None
            )),
        ];

        let fields = VariableDirective::from_fields(
            &name,
            &variant.fields,
            inherited_visibility,
            IndexEntryType::None,
        );

        StructDirective {
            name,
            ident: variant.ident.to_string(),
            options,
            content: extract_doc_from_attrs(&variant.attrs),
            fields,
            self_impls: vec![],
            trait_impls: vec![],
        }
    }

    /// Create a struct directive for a struct.
    pub(crate) fn from_item(parent_path: &str, item: &ItemStruct) -> Directive {
        let name = format!("{}::{}", parent_path, item.ident);

        let options = vec![
            DirectiveOption::Index(IndexEntryType::WithSubEntries),
            DirectiveOption::Vis(DirectiveVisibility::from(&item.vis)),
            DirectiveOption::Toc(format!("struct {}", &item.ident)),
            DirectiveOption::Layout(make_nodes!(
                item.ident,
                item.fields,
                Some(&item.generics),
                Some(Self::DIRECTIVE_NAME)
            )),
        ];

        let fields =
            VariableDirective::from_fields(&name, &item.fields, &None, IndexEntryType::SubEntry);

        Directive::Struct(StructDirective {
            name,
            ident: item.ident.to_string(),
            options,
            content: extract_doc_from_attrs(&item.attrs),
            fields,
            self_impls: vec![],
            trait_impls: vec![],
        })
    }

    /// Create a struct directive for a union.
    pub(crate) fn from_union(parent_path: &str, item: &ItemUnion) -> Directive {
        let name = format!("{parent_path}::{}", item.ident);
        let fields = Fields::Named(item.fields.clone());

        let options = vec![
            DirectiveOption::Index(IndexEntryType::WithSubEntries),
            DirectiveOption::Vis(DirectiveVisibility::from(&item.vis)),
            DirectiveOption::Toc(format!("union {}", item.ident)),
            DirectiveOption::Layout(make_nodes!(
                item.ident,
                fields,
                Some(&item.generics),
                Some("union")
            )),
        ];

        let fields =
            VariableDirective::from_fields(&name, &fields, &None, IndexEntryType::SubEntry);

        Directive::Struct(StructDirective {
            name,
            ident: item.ident.to_string(),
            options,
            content: extract_doc_from_attrs(&item.attrs),
            fields,
            self_impls: vec![],
            trait_impls: vec![],
        })
    }

    /// Return the visibility of this directive.
    pub(crate) fn directive_visibility(&self) -> &DirectiveVisibility {
        if let DirectiveOption::Vis(v) = &self.options[1] {
            return v;
        }
        unreachable!("Struct: order of options changed")
    }

    /// Change the parent module of the struct and its items.
    pub(crate) fn change_parent(&mut self, new_parent: &str) {
        self.name = format!("{new_parent}::{}", self.ident);
        for field in &mut self.fields {
            field.change_parent(&self.name);
        }
        for impl_ in &mut self.self_impls {
            impl_.change_parent(new_parent);
        }
        for impl_ in &mut self.trait_impls {
            impl_.change_parent(new_parent);
        }
    }

    /// Add the impl directive to the struct.
    ///
    /// The parent and visibility of the impl directive are updated along with
    /// the ownership.
    ///
    /// Args:
    ///     :impl\_: The :rust:struct:`ImplDirective` for the struct.
    // noinspection DuplicatedCode
    pub(crate) fn add_impl(&mut self, mut impl_: ImplDirective) {
        // Set parent to the struct's parent for proper naming.
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

impl RstDirective for StructDirective {
    fn get_rst_text(self, level: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        if self.directive_visibility() > max_visibility {
            return vec![];
        }
        let content_indent = Self::make_content_indent(level);

        let mut text =
            Self::make_rst_header(Self::DIRECTIVE_NAME, &self.name, &self.options, level);
        text.extend(self.content.get_rst_text(&content_indent));

        for field in self.fields {
            text.extend(field.get_rst_text(level + 1, max_visibility));
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

impl MdDirective for StructDirective {
    fn get_md_text(self, fence_size: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        if self.directive_visibility() > max_visibility {
            return vec![];
        }
        let fence = Self::make_fence(fence_size);

        let mut text =
            Self::make_md_header(Self::DIRECTIVE_NAME, &self.name, &self.options, &fence);
        text.extend(self.content.get_md_text());

        for field in self.fields {
            text.extend(field.get_md_text(fence_size - 1, max_visibility));
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

    // noinspection DuplicatedCode
    fn fence_size(&self) -> usize {
        [
            match self.fields.iter().map(VariableDirective::fence_size).max() {
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
