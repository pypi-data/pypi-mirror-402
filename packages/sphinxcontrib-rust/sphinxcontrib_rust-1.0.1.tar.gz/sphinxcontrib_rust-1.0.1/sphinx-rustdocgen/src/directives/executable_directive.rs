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

//! Implementation of the ``rust:executable`` directive.

use crate::directives::directive_options::{DirectiveOption, DirectiveVisibility};
use crate::directives::{order_items, CrateDirective, Directive, MdDirective, RstDirective};
use crate::formats::{Format, MdContent, RstContent};
use crate::nodes::Node;
use crate::utils::SourceCodeFile;

/// Struct to hold data required for documenting an executable.
///
/// The data and processing required is pretty much the same as that for a
/// crate. Only the output directive is different. Hence, this is a newtype
/// around the :rust:struct:`CrateDirective`.
#[derive(Clone, Debug)]
pub struct ExecutableDirective(pub(crate) CrateDirective);

impl ExecutableDirective {
    const DIRECTIVE_NAME: &'static str = "executable";

    /// Create a new ``ExecutableDirective`` for the executable from the source
    /// file.
    pub(crate) fn new(source_code_file: &SourceCodeFile) -> ExecutableDirective {
        let mut inner = CrateDirective::new(source_code_file);
        inner.options.extend([
            DirectiveOption::Layout(vec![Node::Name(source_code_file.item.to_string())]),
            DirectiveOption::Toc(source_code_file.item.to_string()),
        ]);
        ExecutableDirective(inner)
    }

    /// Generate the text for the executable's documentation file.
    pub(crate) fn text(self, format: &Format, max_visibility: &DirectiveVisibility) -> Vec<String> {
        let mut text = format.make_title(&self.0.name);
        text.extend(format.format_directive(self, max_visibility));
        text
    }

    pub(crate) fn filter_items(&mut self, max_visibility: &DirectiveVisibility) -> Vec<Directive> {
        self.0.filter_items(max_visibility)
    }
}

impl RstDirective for ExecutableDirective {
    // noinspection DuplicatedCode
    fn get_rst_text(self, level: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        // Do not filter for visibility here. Executables are always documented.
        let content_indent = Self::make_content_indent(level);

        // Create the directive for the exe.
        let mut text =
            Self::make_rst_header(Self::DIRECTIVE_NAME, &self.0.name, &self.0.options, level);
        text.extend(self.0.content.get_rst_text(&content_indent));

        for use_ in self.0.file_directives.uses {
            text.extend(use_.get_rst_text(level + 1, max_visibility));
        }

        text.extend(Self::make_rst_toctree(
            &content_indent,
            "Modules",
            Some(1),
            self.0
                .file_directives
                .modules
                .iter()
                .map(|m| m.ident.as_str()),
        ));

        for (name, items) in order_items(self.0.file_directives.items) {
            text.extend(Self::make_rst_section(name, level, items, max_visibility));
        }

        text
    }
}

impl MdDirective for ExecutableDirective {
    // noinspection DuplicatedCode
    fn get_md_text(self, fence_size: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        // Do not filter for visibility here. Executables are always documented.
        let fence = Self::make_fence(fence_size);

        // Create the directive for the exe.
        let mut text =
            Self::make_md_header(Self::DIRECTIVE_NAME, &self.0.name, &self.0.options, &fence);
        text.extend(self.0.content.get_md_text());

        for use_ in self.0.file_directives.uses {
            text.extend(use_.get_md_text(3, max_visibility));
        }

        text.extend(Self::make_md_toctree(
            3,
            "Modules",
            Some(1),
            self.0
                .file_directives
                .modules
                .iter()
                .map(|m| m.ident.as_str()),
        ));

        for (name, items) in order_items(self.0.file_directives.items) {
            text.extend(Self::make_md_section(
                name,
                fence_size,
                items,
                max_visibility,
            ));
        }

        text
    }

    fn fence_size(&self) -> usize {
        Self::calc_fence_size(&self.0.file_directives.items)
    }
}
