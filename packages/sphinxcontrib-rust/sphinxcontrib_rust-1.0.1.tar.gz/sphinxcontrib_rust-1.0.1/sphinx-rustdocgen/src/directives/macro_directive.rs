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

//! Implementation of the ``rust:macro`` directive

use syn::ItemMacro;

use crate::directives::directive_options::{DirectiveOption, DirectiveVisibility, IndexEntryType};
use crate::directives::{extract_doc_from_attrs, Directive};
use crate::formats::{MdContent, MdDirective, RstContent, RstDirective};

#[derive(Clone, Debug)]
pub struct MacroDirective {
    pub(crate) name: String,
    pub(crate) ident: String,
    pub(crate) options: Vec<DirectiveOption>,
    pub(crate) content: Vec<String>,
}

impl MacroDirective {
    const DIRECTIVE_NAME: &'static str = "macro";

    pub(crate) fn from_item(parent_path: &str, item: &ItemMacro) -> Option<Directive> {
        let ident = item.ident.as_ref()?;
        let name = format!("{}::{}", parent_path, ident);

        let is_exported = item
            .attrs
            .iter()
            .any(|a| !a.path().segments.is_empty() && a.path().segments[0].ident == "macro_export");

        let vis = if is_exported {
            DirectiveVisibility::Pub
        }
        else {
            DirectiveVisibility::Pvt
        };

        let options = vec![
            DirectiveOption::Index(IndexEntryType::Normal),
            DirectiveOption::Vis(vis),
        ];

        Some(Directive::Macro(MacroDirective {
            name,
            ident: ident.to_string(),
            options,
            content: extract_doc_from_attrs(&item.attrs),
        }))
    }

    /// Return the visibility of this directive.
    pub(crate) fn directive_visibility(&self) -> &DirectiveVisibility {
        if let DirectiveOption::Vis(v) = &self.options[1] {
            return v;
        }
        unreachable!("Macro: order of options changed")
    }

    /// Change the parent module of the macro.
    pub(crate) fn change_parent(&mut self, new_parent: &str) {
        self.name = format!("{new_parent}::{}", self.ident);
    }
}

impl RstDirective for MacroDirective {
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

impl MdDirective for MacroDirective {
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
