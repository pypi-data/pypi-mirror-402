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

//! Implementation of the ``rust:crate`` directive.

use std::collections::BTreeMap;

use crate::directives::directive_options::{DirectiveOption, DirectiveVisibility, IndexEntryType};
use crate::directives::{
    extract_doc_from_attrs,
    order_items,
    Directive,
    FileDirectives,
    UseDirective,
};
use crate::formats::{Format, MdContent, MdDirective, RstContent, RstDirective};
use crate::utils::SourceCodeFile;

/// Struct to hold data required for documenting a crate.
#[derive(Clone, Debug)]
pub struct CrateDirective {
    /// The name of the crate.
    pub(crate) name: String,
    /// The options for the crate directive.
    pub(crate) options: Vec<DirectiveOption>,
    /// The docstring for the crate's lib.rs file.
    pub(crate) content: Vec<String>,
    /// The directives within the crate's document file.
    pub(crate) file_directives: FileDirectives,
}

impl CrateDirective {
    const DIRECTIVE_NAME: &'static str = "crate";

    /// Create a new ``CrateDirective`` for the crate from the source file.
    pub(crate) fn new(source_code_file: &SourceCodeFile) -> Self {
        let ast = source_code_file.ast();

        let file_directives =
            FileDirectives::from_ast_items(&ast.items, &source_code_file.to_parent_directory());

        CrateDirective {
            name: source_code_file.item.clone(),
            options: vec![DirectiveOption::Index(IndexEntryType::Normal)],
            content: extract_doc_from_attrs(&ast.attrs),
            file_directives,
        }
    }

    /// Generate the text for the crate's documentation file.
    pub(crate) fn text(self, format: &Format, max_visibility: &DirectiveVisibility) -> Vec<String> {
        let mut text = format.make_title(&format!("Crate {}", format.make_inline_code(&self.name)));
        text.extend(format.format_directive(self, max_visibility));
        text
    }

    /// Filter out items that will not be documented due to visibility
    /// restrictions.
    ///
    /// The function goes through all modules and identifies items that will
    /// not be documented due to the configured visibility. As part of the
    /// filtering, it will also identify any re-exports that should be inlined.
    ///
    /// Returns:
    ///     A vec of directives that will not be documented.
    // noinspection DuplicatedCode
    pub(crate) fn filter_items(&mut self, max_visibility: &DirectiveVisibility) -> Vec<Directive> {
        self.identify_impl_parents();

        let mut excluded_items = vec![];
        self.file_directives.modules.retain_mut(|module| {
            // Get any items that the submodules won't document.
            excluded_items.extend(module.filter_items(max_visibility));
            // Keep any submodule that meets the visibility criteria.
            module.directive_visibility() <= max_visibility
        });

        let mut reexports = vec![];
        for use_ in &mut self.file_directives.uses {
            if use_.reexport.is_some() && use_.directive_visibility() <= max_visibility {
                reexports.push(use_)
            }
        }

        // Crate is always documented, so claim ownership of any reexports
        // from the excluded items and return the rest of them.
        let mut not_documented = vec![];
        let mut inlined = BTreeMap::new();
        'item_loop: for mut item in excluded_items {
            for reexport in &mut reexports {
                if reexport.contains(item.name()) {
                    if !matches!(item, Directive::Impl(_)) {
                        let (k, v) = reexport.inline(item.name()).unwrap();
                        inlined.insert(k, v);
                    }
                    item.change_parent(&self.name);
                    item.add_content(reexport.content.clone());
                    self.file_directives.items.push(item);
                    continue 'item_loop;
                }
            }
            not_documented.push(item);
        }
        self.file_directives
            .uses
            .push(UseDirective::for_use_paths(inlined));

        not_documented
    }

    /// Collect all impl directive and move them under appropriate parent.
    ///
    /// The new parent for the impl directive is the struct or enum
    /// that is its self type, or the trait that is being implemented. If both
    /// the self type and trait are in the crate, the self type is preferred
    /// as the parent.
    pub(crate) fn identify_impl_parents(&mut self) {
        let mut impls = vec![];
        impls.append(&mut self.file_directives.impls);

        for module in &mut self.file_directives.modules {
            impls.extend(module.collect_impls());
        }
        self.file_directives.claim_impls(&self.name, impls);
    }
}

impl RstDirective for CrateDirective {
    // noinspection DuplicatedCode
    fn get_rst_text(self, level: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        // Do not filter for visibility here. Crates are always documented.
        let content_indent = Self::make_content_indent(level);

        // Create the directive for the crate.
        let mut text =
            Self::make_rst_header(Self::DIRECTIVE_NAME, &self.name, &self.options, level);
        text.extend(self.content.get_rst_text(&content_indent));

        text.extend(Self::make_rst_toctree(
            &content_indent,
            "Modules",
            Some(1),
            self.file_directives
                .modules
                .iter()
                .map(|m| m.ident.as_str()),
        ));

        let mut reexports = vec![];
        for use_ in self.file_directives.uses {
            if use_.reexport.is_some() && use_.directive_visibility() <= max_visibility {
                for path in use_.paths.values() {
                    reexports.push((path.clone(), use_.content.clone()));
                }
            }
            text.extend(use_.get_rst_text(level + 1, max_visibility));
        }
        text.extend(Self::make_rst_list(
            &content_indent,
            "Re-exports",
            &reexports,
        ));

        for (name, items) in order_items(self.file_directives.items) {
            text.extend(Self::make_rst_section(name, level, items, max_visibility));
        }

        text
    }
}

impl MdDirective for CrateDirective {
    // noinspection DuplicatedCode
    fn get_md_text(self, fence_size: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        // Do not filter for visibility here. Crates are always documented.
        let fence = Self::make_fence(fence_size);

        // Create the directive for the crate.
        let mut text =
            Self::make_md_header(Self::DIRECTIVE_NAME, &self.name, &self.options, &fence);
        text.extend(self.content.get_md_text());

        text.extend(Self::make_md_toctree(
            3,
            "Modules",
            Some(1),
            self.file_directives
                .modules
                .iter()
                .map(|m| m.ident.as_str()),
        ));

        let mut reexports = vec![];
        for use_ in self.file_directives.uses {
            if use_.reexport.is_some() && use_.directive_visibility() <= max_visibility {
                for path in use_.paths.values() {
                    reexports.push((path.clone(), use_.content.clone()));
                }
            }
            text.extend(use_.get_md_text(3, max_visibility));
        }
        text.extend(Self::make_md_list(3, "Re-exports", &reexports));

        for (name, items) in order_items(self.file_directives.items) {
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
        Self::calc_fence_size(&self.file_directives.items)
    }
}
