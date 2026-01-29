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

//! Implementation of the ``rust:impl`` directive

use syn::{ItemImpl, Visibility};

use crate::directives::directive_options::{DirectiveOption, DirectiveVisibility, IndexEntryType};
use crate::directives::{extract_doc_from_attrs, order_items, Directive};
use crate::formats::{MdContent, MdDirective, RstContent, RstDirective};
use crate::nodes::{
    nodes_for_generics,
    nodes_for_path,
    nodes_for_type,
    nodes_for_where_clause,
    type_name,
    Node,
};

/// Struct to hold details for documenting an impl block.
#[derive(Clone, Debug)]
pub struct ImplDirective {
    /// The full Rust path to the impl block, used as the directive's name.
    pub(crate) name: String,
    /// The declared self type of the impl block.
    pub(crate) self_ty: String,
    /// The full path of the self type of the impl block.
    pub(crate) resolved_self_ty: String,
    /// The trait implemented in the impl block, if any.
    pub(crate) trait_: Option<String>,
    /// The full path of the trait implemented, if any.
    pub(crate) resolved_trait: Option<String>,
    /// The options for the directive.
    pub(crate) options: Vec<DirectiveOption>,
    /// The content for the directive.
    pub(crate) content: Vec<String>,
    /// The directives nested under this directive.
    pub(crate) items: Vec<Directive>,
}

/// Generate docutils nodes for the impl block's signature.
fn nodes_for_impl(item: &ItemImpl) -> Vec<Node> {
    let mut nodes = vec![];
    if item.unsafety.is_some() {
        nodes.extend_from_slice(&[Node::Keyword("unsafe"), Node::Space]);
    }
    nodes.extend_from_slice(&[Node::Keyword("impl")]);
    nodes.extend(nodes_for_generics(&item.generics));
    nodes.push(Node::Space);
    if let Some((bang, path, _)) = &item.trait_ {
        if bang.is_some() {
            nodes.push(Node::Operator("!"));
        }
        nodes.extend(nodes_for_path(path));
        nodes.extend_from_slice(&[Node::Space, Node::Keyword("for"), Node::Space]);
    }
    nodes.extend(nodes_for_type(&item.self_ty));
    if let Some(wc) = &item.generics.where_clause {
        nodes.extend(nodes_for_where_clause(wc));
    }
    nodes
}

impl ImplDirective {
    const DIRECTIVE_NAME: &'static str = "impl";

    pub(crate) fn from_item(
        parent_path: &str,
        item: &ItemImpl,
        inherited_visibility: &Option<&Visibility>,
    ) -> Self {
        let self_ty = type_name(&item.self_ty);

        let mut trait_ = String::new();
        if let Some((bang, path, _)) = &item.trait_ {
            if bang.is_some() {
                trait_ += "!";
            }
            trait_ += &*path.segments.last().unwrap().ident.to_string();
        };

        let options = vec![
            DirectiveOption::Index(IndexEntryType::None),
            DirectiveOption::Vis(DirectiveVisibility::Pub), // Updated later
            DirectiveOption::Layout(nodes_for_impl(item)),
            if trait_.is_empty() {
                DirectiveOption::Toc(format!("impl {self_ty}"))
            }
            else {
                DirectiveOption::Toc(format!("impl {trait_} for {self_ty}"))
            },
        ];

        let name = if trait_.is_empty() {
            format!("{parent_path}::{self_ty}")
        }
        else {
            format!("{parent_path}::{self_ty}::{trait_}")
        };
        let items = Directive::from_impl_items(&name, item.items.iter(), inherited_visibility);
        ImplDirective {
            name,
            self_ty,
            resolved_self_ty: String::new(),
            trait_: if trait_.is_empty() {
                None
            }
            else {
                Some(trait_)
            },
            resolved_trait: None,
            options,
            content: extract_doc_from_attrs(&item.attrs),
            items,
        }
    }

    /// Return the visibility of this directive.
    pub(crate) fn directive_visibility(&self) -> &DirectiveVisibility {
        if let DirectiveOption::Vis(v) = &self.options[1] {
            return v;
        }
        unreachable!("Impl: order of options changed")
    }

    pub(crate) fn set_directive_visibility(&mut self, visibility: &DirectiveVisibility) {
        self.options[1] = DirectiveOption::Vis(*visibility)
    }

    /// Change the parent module of the impl and its items.
    pub(crate) fn change_parent(&mut self, new_parent: &str) {
        if let Some(t) = &self.trait_ {
            self.name = format!("{new_parent}::{}::{t}", self.self_ty)
        }
        else {
            self.name = format!("{new_parent}::{}", self.self_ty);
        }
        for item in &mut self.items {
            item.change_parent(&self.name);
        }
    }

    pub(crate) fn for_item(&self, name: &str) -> bool {
        name == self.name
            || self.name.starts_with(&format!("{}::", name))
            || name == self.resolved_self_ty
    }

    pub(crate) fn for_trait(&self, name: &str, parent_name: &str) -> bool {
        match &self.trait_ {
            Some(trait_) => {
                name == format!("{parent_name}::{trait_}") // Trait from same file
                    || name == self.resolved_trait.as_ref().unwrap_or(&String::new())
            }
            _ => false,
        }
    }
}

impl RstDirective for ImplDirective {
    fn get_rst_text(self, level: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        let content_indent = Self::make_content_indent(level + 1);

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

        text
    }
}

impl MdDirective for ImplDirective {
    fn get_md_text(self, fence_size: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
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

        text.push(fence);
        text
    }

    fn fence_size(&self) -> usize {
        Self::calc_fence_size(&self.items)
    }
}
