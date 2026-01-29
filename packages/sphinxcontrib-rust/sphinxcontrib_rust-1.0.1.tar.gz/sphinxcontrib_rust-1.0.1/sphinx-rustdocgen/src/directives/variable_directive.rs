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

//! Implementation of the ``rust:variable`` directive

use syn::{
    Fields,
    ForeignItemStatic,
    ImplItemConst,
    ItemConst,
    ItemStatic,
    TraitItemConst,
    Visibility,
};

use crate::directives::directive_options::{DirectiveOption, DirectiveVisibility, IndexEntryType};
use crate::directives::{extract_doc_from_attrs, Directive};
use crate::formats::{MdContent, MdDirective, RstContent, RstDirective};
use crate::nodes::{nodes_for_type, Node};

/// Struct to hold the data for documenting variables and struct fields.
#[derive(Clone, Debug)]
pub struct VariableDirective {
    /// The Rust path of the variable or field.
    pub(crate) name: String,
    /// The identifier of the variable or field.
    pub(crate) ident: String,
    /// The options for the directive.
    pub(crate) options: Vec<DirectiveOption>,
    /// The content of the directive.
    pub(crate) content: Vec<String>,
}

/// DRY macro to create :rust:struct:`VariableDirective` from various ``syn``
/// structs.
macro_rules! var_from_item {
    ($item:expr, $parent_path:expr, $vis:expr, $inherited:expr, $prefix:expr, $index:expr) => {{
        let name = format!("{}::{}", $parent_path, &$item.ident);
        let mut nodes = vec![
            Node::Keyword($prefix),
            Node::Space,
            Node::Name($item.ident.to_string()),
            Node::Punctuation(": "),
        ];
        nodes.extend(nodes_for_type(&$item.ty));

        let options = vec![
            DirectiveOption::Index($index),
            DirectiveOption::Vis(DirectiveVisibility::effective_visibility(&$vis, $inherited)),
            DirectiveOption::Toc(format!("{} {}", $prefix, &$item.ident)),
            DirectiveOption::Layout(nodes),
        ];

        VariableDirective {
            name,
            ident: $item.ident.to_string(),
            options,
            content: extract_doc_from_attrs(&$item.attrs),
        }
    }};
}

impl VariableDirective {
    const DIRECTIVE_NAME: &'static str = "variable";

    /// Create variable directives from the fields of a struct or enum variant.
    pub(crate) fn from_fields(
        parent_path: &str,
        fields: &Fields,
        inherited_visibility: &Option<&Visibility>,
        index_entry_type: IndexEntryType,
    ) -> Vec<Self> {
        if let Fields::Named(named_fields) = fields {
            named_fields
                .named
                .iter()
                .map(|f| {
                    let mut nodes = vec![
                        Node::Name(f.ident.as_ref().unwrap().to_string()),
                        Node::Punctuation(": "),
                    ];
                    nodes.extend(nodes_for_type(&f.ty));
                    let options = vec![
                        DirectiveOption::Index(index_entry_type),
                        DirectiveOption::Vis(DirectiveVisibility::effective_visibility(
                            &f.vis,
                            inherited_visibility,
                        )),
                        DirectiveOption::Toc(format!("{}", f.ident.as_ref().unwrap())),
                        DirectiveOption::Layout(nodes),
                    ];

                    VariableDirective {
                        name: format!("{}::{}", parent_path, f.ident.as_ref().unwrap()),
                        ident: f.ident.as_ref().unwrap().to_string(),
                        options,
                        content: extract_doc_from_attrs(&f.attrs),
                    }
                })
                .collect()
        }
        else {
            Vec::new()
        }
    }

    /// Create a variable directive for a static variable.
    pub(crate) fn from_static(parent_path: &str, item: &ItemStatic) -> Directive {
        Directive::Variable(var_from_item!(
            item,
            parent_path,
            item.vis,
            &None,
            "static",
            IndexEntryType::Normal
        ))
    }

    /// Create a variable directive for a const variable.
    pub(crate) fn from_const(parent_path: &str, item: &ItemConst) -> Directive {
        Directive::Variable(var_from_item!(
            item,
            parent_path,
            item.vis,
            &None,
            "const",
            IndexEntryType::Normal
        ))
    }

    /// Create a variable directive for a const variable within an impl block.
    pub(crate) fn from_impl_const(
        parent_path: &str,
        item: &ImplItemConst,
        inherited_visibility: &Option<&Visibility>,
    ) -> Directive {
        Directive::Variable(var_from_item!(
            item,
            parent_path,
            item.vis,
            inherited_visibility,
            "const",
            IndexEntryType::None
        ))
    }

    /// Create a variable directive for a const variable within a trait
    /// definition.
    pub(crate) fn from_trait_const(
        parent_path: &str,
        item: &TraitItemConst,
        inherited_visibility: &Option<&Visibility>,
    ) -> Directive {
        Directive::Variable(var_from_item!(
            item,
            parent_path,
            Visibility::Inherited,
            inherited_visibility,
            "const",
            IndexEntryType::None
        ))
    }

    /// Create a variable directive for a foreign static variable.
    pub(crate) fn from_extern_static(parent_path: &str, item: &ForeignItemStatic) -> Directive {
        Directive::Variable(var_from_item!(
            item,
            parent_path,
            item.vis,
            &None,
            "extern static",
            IndexEntryType::Normal
        ))
    }

    /// Return the visibility of this directive.
    pub(crate) fn directive_visibility(&self) -> &DirectiveVisibility {
        if let DirectiveOption::Vis(v) = &self.options[1] {
            return v;
        }
        unreachable!("Variable: order of options changed")
    }

    /// Change the parent directive of the variable.
    pub(crate) fn change_parent(&mut self, new_parent: &str) {
        self.name = format!("{new_parent}::{}", self.ident);
    }
}

impl RstDirective for VariableDirective {
    // noinspection DuplicatedCode
    fn get_rst_text(self, level: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        if self.directive_visibility() > max_visibility {
            return vec![];
        }
        let content_indent = Self::make_indent(level + 1);

        let mut text =
            Self::make_rst_header(Self::DIRECTIVE_NAME, &self.name, &self.options, level);
        text.extend(self.content.get_rst_text(&content_indent));

        text
    }
}

impl MdDirective for VariableDirective {
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
