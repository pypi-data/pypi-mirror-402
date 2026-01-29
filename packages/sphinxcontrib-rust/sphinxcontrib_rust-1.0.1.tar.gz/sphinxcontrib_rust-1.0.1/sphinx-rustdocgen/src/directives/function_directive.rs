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

//! Implementation of the ``rust:function`` directive

use syn::{FnArg, ForeignItemFn, ImplItemFn, ItemFn, Signature, TraitItemFn, Visibility};

use crate::directives::directive_options::{DirectiveOption, DirectiveVisibility, IndexEntryType};
use crate::directives::{extract_doc_from_attrs, Directive};
use crate::formats::{MdContent, MdDirective, RstContent, RstDirective};
use crate::nodes::{
    nodes_for_abi_opt,
    nodes_for_generics,
    nodes_for_pat_type,
    nodes_for_return_type,
    nodes_for_type,
    nodes_for_where_clause,
    Node,
};

/// Struct to hold data for documenting a function.
#[derive(Clone, Debug)]
pub struct FunctionDirective {
    /// The full Rust path of the function.
    pub(crate) name: String,
    /// The identifier of the function.
    pub(crate) ident: String,
    /// The directive options to use.
    pub(crate) options: Vec<DirectiveOption>,
    /// The docstring for the function.
    pub(crate) content: Vec<String>,
}

/// Generate docutils node layout for the function from its signature
fn nodes_for_fn_signature(signature: &Signature) -> Vec<Node> {
    let mut nodes = Vec::new();
    if signature.constness.is_some() {
        nodes.push(Node::Keyword("const"));
        nodes.push(Node::Space);
    }
    if signature.asyncness.is_some() {
        nodes.push(Node::Keyword("async"));
        nodes.push(Node::Space);
    }
    if signature.unsafety.is_some() {
        nodes.push(Node::Keyword("unsafe"));
        nodes.push(Node::Space);
    }
    nodes.extend(nodes_for_abi_opt(&signature.abi));
    nodes.extend_from_slice(&[
        Node::Keyword("fn"),
        Node::Space,
        Node::Name(signature.ident.to_string()),
    ]);

    // Nodes for generics
    if !signature.generics.params.is_empty() {
        nodes.extend(nodes_for_generics(&signature.generics));
    }

    // Nodes for arguments
    nodes.push(Node::Punctuation("("));
    for arg in &signature.inputs {
        match arg {
            FnArg::Receiver(r) => {
                if let Some((_, lt_opt)) = &r.reference {
                    nodes.push(Node::Punctuation("&"));
                    if let Some(lt) = lt_opt {
                        nodes.push(Node::Lifetime(lt.to_string()));
                        nodes.push(Node::Space);
                    }
                }
                if r.mutability.is_some() {
                    nodes.push(Node::Keyword("mut"));
                    nodes.push(Node::Space);
                }
                nodes.push(Node::Keyword("self"));
                if r.colon_token.is_some() {
                    nodes.push(Node::Punctuation(":"));
                    nodes.extend(nodes_for_type(&r.ty));
                }
            }
            FnArg::Typed(t) => nodes.extend(nodes_for_pat_type(t)),
        }
        nodes.push(Node::Punctuation(", "));
    }

    // If variadic, add the "..." otherwise remove the last ", ".
    if signature.variadic.is_some() {
        nodes.push(Node::Punctuation("..."));
    }
    else if !signature.inputs.is_empty() {
        nodes.pop();
    }
    // Closing parenthesis
    nodes.push(Node::Punctuation(")"));

    // Return type
    nodes.extend(nodes_for_return_type(&signature.output));

    // Nodes for where clause
    if let Some(wc) = &signature.generics.where_clause {
        nodes.extend(nodes_for_where_clause(wc))
    }

    nodes
}

/// DRY macro to parse the different item types.
macro_rules! func_from_item {
    ($parent_path:expr, $item:expr, $vis:expr, $inherited:expr, $index:expr) => {{
        let sig = &$item.sig;
        let options = vec![
            DirectiveOption::Index($index),
            DirectiveOption::Vis(DirectiveVisibility::effective_visibility(&$vis, $inherited)),
            DirectiveOption::Layout(nodes_for_fn_signature(sig)),
        ];

        FunctionDirective {
            name: format!("{}::{}", $parent_path, $item.sig.ident),
            ident: $item.sig.ident.to_string(),
            options,
            content: extract_doc_from_attrs(&$item.attrs),
        }
    }};
}

impl FunctionDirective {
    const DIRECTIVE_NAME: &'static str = "function";

    /// Create a new ``Directive::Function`` from a ``syn::ItemFn``.
    ///
    /// Args:
    ///     :parent_path: The full path of the module the function is in.
    ///     :item: The ``syn::ItemFn`` reference to parse.
    ///     :inherited_visibility: The visibility of the parent module.
    ///
    /// Returns:
    ///     A new ``Directive::Function`` value, which contains the parsed
    ///     ``FunctionDirective`` in it.
    pub(crate) fn from_item(parent_path: &str, item: &ItemFn) -> Directive {
        Directive::Function(func_from_item!(
            parent_path,
            item,
            item.vis,
            &None,
            IndexEntryType::Normal
        ))
    }

    /// Create a new ``Directive::Function`` from a ``syn::ImplItemFn``.
    ///
    /// Args:
    ///     :parent_path: The full path of the impl block the function is in.
    ///     :item: The ``syn::ImplItemFn`` reference to parse.
    ///     :inherited_visibility: The visibility of the impl block.
    ///
    /// Returns:
    ///     A new ``Directive::Function`` value, which contains the parsed
    ///     ``FunctionDirective`` in it.
    pub(crate) fn from_impl_item(
        parent_path: &str,
        item: &ImplItemFn,
        inherited_visibility: &Option<&Visibility>,
    ) -> Directive {
        Directive::Function(func_from_item!(
            parent_path,
            item,
            item.vis,
            inherited_visibility,
            IndexEntryType::None
        ))
    }

    /// Create a new ``Directive::Function`` from a ``syn::TraitItemFn``.
    ///
    /// Args:
    ///     :parent_path: The full path of the trait the function is in.
    ///     :item: The ``syn::TraitItemFn`` reference to parse.
    ///     :inherited_visibility: The visibility of the trait.
    ///
    /// Returns:
    ///     A new ``Directive::Function`` value, which contains the parsed
    ///     ``FunctionDirective`` in it.
    pub(crate) fn from_trait_item(
        parent_path: &str,
        item: &TraitItemFn,
        inherited_visibility: &Option<&Visibility>,
    ) -> Directive {
        Directive::Function(func_from_item!(
            parent_path,
            item,
            &Visibility::Inherited,
            inherited_visibility,
            IndexEntryType::SubEntry
        ))
    }

    /// Create a new ``Directive::Function`` from a ``syn::ForeignItemFn``.
    ///
    /// Args:
    ///     :parent_path: The full path of the trait the function is in.
    ///     :item: The ``syn::ForeignItemFn`` reference to parse.
    ///     :inherited_visibility: The visibility of the parent module.
    ///
    /// Returns:
    ///     A new ``Directive::Function`` value, which contains the parsed
    ///     ``FunctionDirective`` in it.
    pub(crate) fn from_extern(parent_path: &str, item: &ForeignItemFn) -> Directive {
        Directive::Function(func_from_item!(
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
        unreachable!("Function: order of options changed")
    }

    /// Change the parent directive of the function.
    pub(crate) fn change_parent(&mut self, new_parent: &str) {
        self.name = format!("{new_parent}::{}", self.ident)
    }
}

impl RstDirective for FunctionDirective {
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

impl MdDirective for FunctionDirective {
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
