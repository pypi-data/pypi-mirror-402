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

//! Implementation of the ``rust:module`` directive

use std::cmp::max;
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use syn::{ItemMod, Meta};

use crate::directives::directive_options::{DirectiveOption, DirectiveVisibility, IndexEntryType};
use crate::directives::{
    extract_doc_from_attrs,
    order_items,
    Directive,
    FileDirectives,
    ImplDirective,
    UseDirective,
};
use crate::formats::{Format, MdContent, MdDirective, RstContent, RstDirective};
use crate::utils::SourceCodeFile;

/// Struct to hold data for a module's documentation.
#[derive(Clone, Debug)]
pub struct ModuleDirective {
    /// The full path to the module.
    pub(crate) name: String,
    /// The options for the module directive.
    pub(crate) options: Vec<DirectiveOption>,
    /// The docstring for the module.
    pub(crate) content: Vec<String>,
    /// The identifier of the module (i.e. the final portion of name).
    pub(crate) ident: String,
    /// The source code file for the module.
    pub(crate) source_code_file: SourceCodeFile,
    /// The directives within the crate's document file.
    pub(crate) file_directives: FileDirectives,
}

/// Check if the module is a test module or not.
#[inline]
fn has_test_token(tokens: &str) -> bool {
    tokens.split(',').any(|t| t.trim() == "test")
}

/// Find the file for the module under the provided directory.
///
/// Args:
///     :module_ident: The identifier of the module.
///     :directory: The directory under which to find the module's file.
///
/// Returns:
///     A None value if neither ``<directory>/<module>.rs`` nor
///     ``<directory>/<module>/mod.rs`` exist, otherwise a Some value
///     for the path of the file.
fn find_file_under_dir(module_ident: &str, directory: &Path) -> Option<PathBuf> {
    // Check for <module>.rs in the directory.
    let mut mod_file = directory.join(format!("{module_ident}.rs"));
    if mod_file.is_file() {
        return Some(mod_file);
    }

    // Check <module>/mod.rs in the directory.
    mod_file = directory.join(module_ident).join("mod.rs");
    if mod_file.is_file() {
        return Some(mod_file);
    }

    None
}

/// Create a file path for the module's source code and documentation.
///
/// If the module is defined in its own file, the function will try to find the
/// file and return its path. Otherwise, it will return a hypothetical path as
/// if the module were defined in a ``mod.rs`` file in its own directory. This
/// is mainly to prevent conflicts with existing files of the same name.
fn get_module_file(module_ident: &str, parent_file: &SourceCodeFile) -> PathBuf {
    if parent_file.path.is_dir() {
        // Parent path is a directory. Check it or create a pseudo-path.
        find_file_under_dir(module_ident, &parent_file.path)
            .unwrap_or(parent_file.path.join(module_ident).join("mod.rs"))
    }
    else if parent_file.path.ends_with("mod.rs") {
        // Parent module is in a mod.rs file. Check the same directory for the module.
        let parent_dir = parent_file.path.parent().unwrap();
        find_file_under_dir(module_ident, parent_dir)
            .unwrap_or(parent_dir.join(module_ident).join("mod.rs"))
    }
    else {
        // Parent is a file. Check under a directory with the same name as the parent,
        // in the directory where the parent file exists.
        let parent_dir = parent_file
            .path
            .parent()
            .unwrap()
            .join(parent_file.path.file_stem().unwrap());
        find_file_under_dir(module_ident, &parent_dir)
            .unwrap_or(parent_dir.join(module_ident).join("mod.rs"))
    }
}

/// Determines if the module is a test module or not.
fn is_test_module(item_mod: &ItemMod) -> bool {
    // XXX: Find a better way to do this.
    for attr in &item_mod.attrs {
        if let Meta::List(meta) = &attr.meta {
            if meta.path.segments.len() == 1
                && meta.path.segments.first().unwrap().ident == "cfg"
                && has_test_token(&meta.tokens.to_string())
            {
                return true;
            }
        }
    }
    false
}

impl ModuleDirective {
    const DIRECTIVE_NAME: &'static str = "module";

    /// Create a :rust:struct:`ModuleDirective` from the item, if the module is
    /// not a test module.
    ///
    /// If the module's items are in a different file, the function will try to
    /// find the appropriate file and parse it for the items. This is done
    /// recursively for any submodules within the items.
    ///
    /// Args:
    ///     :parent_path: The path of the module's parent module or the crate
    ///         name.
    ///     :item: The ``ItemMod`` parsed out by ``syn``.
    ///
    /// Returns:
    ///     A ``Some`` value if the module is not a test module, otherwise
    ///     ``None``.
    pub(crate) fn from_item(parent_file: &SourceCodeFile, item: &ItemMod) -> Option<Self> {
        if is_test_module(item) {
            return None;
        }

        // Get the path for the module's file. If the module is defined inline,
        // create a new pseudo-path that'll be used to determine the output file.
        let source_code_file = SourceCodeFile {
            path: get_module_file(&item.ident.to_string(), parent_file),
            item: format!("{}::{}", &parent_file.item, item.ident),
        };

        // Get the items or parse them from the file
        let mod_items = item.content.as_ref().map(|(_, items)| items);
        let mut mod_attrs = item.attrs.clone();
        let file_directives = match mod_items {
            None => {
                let ast = source_code_file.ast();
                mod_attrs.extend(ast.attrs);
                FileDirectives::from_ast_items(&ast.items, &source_code_file)
            }
            Some(m) => FileDirectives::from_ast_items(m, &source_code_file),
        };

        Some(ModuleDirective {
            name: source_code_file.item.clone(),
            options: vec![
                DirectiveOption::Index(IndexEntryType::Normal),
                DirectiveOption::Vis(DirectiveVisibility::from(&item.vis)),
            ],
            content: extract_doc_from_attrs(&mod_attrs),
            ident: item.ident.to_string(),
            source_code_file,
            file_directives,
        })
    }

    /// Generate the text for the module's documentation file.
    pub(crate) fn text(self, format: &Format, max_visibility: &DirectiveVisibility) -> Vec<String> {
        let mut text = format.make_title(&format.make_inline_code(format!("mod {}", self.ident)));
        text.extend(format.format_directive(self, max_visibility));
        text
    }

    /// Filter out items that will not be documented due to visibility
    /// restrictions.
    ///
    /// The function recurses through all submodules and identifies items that
    /// will not be documented due to the configured visibility. As part of the
    /// filtering, it will also identify any re-exports that should be inlined.
    ///
    /// Returns:
    ///     A vec of directives that will not be documented.
    // noinspection DuplicatedCode
    pub(crate) fn filter_items(&mut self, max_visibility: &DirectiveVisibility) -> Vec<Directive> {
        let mut excluded_items = vec![];
        self.file_directives.modules.retain_mut(|module| {
            // Get any items that the submodules won't document.
            excluded_items.extend(module.filter_items(max_visibility));
            // Keep any submodule that meets the visibility criteria.
            module.directive_visibility() <= max_visibility
        });

        // Avoids issue with mutable and immutable references at the same time.
        let directive_visibility = *self.directive_visibility();

        // Gather all re-exports that might be documented.
        let mut reexports = vec![];
        for use_ in &mut self.file_directives.uses {
            if use_.reexport.is_some() && use_.directive_visibility() <= max_visibility {
                reexports.push(use_)
            }
        }

        if &directive_visibility > max_visibility {
            // The module won't be documented. Check for any items that should
            // be documented.
            while let Some(item) = self.file_directives.items.pop() {
                if item.directive_visibility() <= max_visibility {
                    excluded_items.push(item);
                }
            }
            // Check if any of the excluded items are reexported by this module.
            // Possible when a pub item is in a pvt module, reexported as
            // pub(crate) by a pub(crate) module, and then reexported again as
            // pub by the crate. In this case, we need to change the parent of
            // the excluded item before returning it.
            'item_loop: for item in excluded_items.iter_mut() {
                for reexport in &reexports {
                    if reexport.contains(item.name()) {
                        item.change_parent(&self.name);
                        continue 'item_loop;
                    }
                }
            }
            return excluded_items;
        }

        // If the module will be documented, claim ownership of any reexports
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

    /// Return the visibility of this directive.
    pub(crate) fn directive_visibility(&self) -> &DirectiveVisibility {
        if let DirectiveOption::Vis(v) = &self.options[1] {
            return v;
        }
        unreachable!("Module: order of options changed")
    }

    /// Change the parent module of the module.
    pub(crate) fn change_parent(&mut self, new_parent: &str) {
        self.name = format!("{new_parent}::{}", self.ident);
        for item in &mut self.file_directives.items {
            item.change_parent(&self.name);
        }
    }

    /// Collect all impl directives from self and any sub-modules.
    pub(crate) fn collect_impls(&mut self) -> Vec<ImplDirective> {
        let mut impls = vec![];
        impls.append(&mut self.file_directives.impls);

        for module in &mut self.file_directives.modules {
            impls.extend(module.collect_impls())
        }

        impls
    }

    /// Attach impl directives to the appropriate struct, enum or trait
    /// directive.
    ///
    /// Args:
    ///     :impls: The impl directives to claim from.
    ///
    /// Returns:
    ///     A vec of impl directives that were not claimed.
    pub(crate) fn claim_impls(&mut self, impls: Vec<ImplDirective>) -> Vec<ImplDirective> {
        self.file_directives.claim_impls(&self.name, impls)
    }
}

impl RstDirective for ModuleDirective {
    // noinspection DuplicatedCode
    fn get_rst_text(self, level: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        // Do not filter for visibility here. Modules are always documented.
        let content_indent = Self::make_content_indent(level);

        // Create the directive for the module.
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
                .map(|m| format!("{}/{}", &self.ident, m.ident)),
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

        for (name, item) in order_items(self.file_directives.items) {
            text.extend(Self::make_rst_section(name, level, item, max_visibility));
        }

        text
    }
}

impl MdDirective for ModuleDirective {
    // noinspection DuplicatedCode
    fn get_md_text(self, fence_size: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        // Do not filter for visibility here. Modules are always documented.
        let fence = Self::make_fence(max(fence_size, 4));

        // Create the directive for the module.
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
                .map(|m| format!("{}/{}", &self.ident, m.ident)),
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

        for (name, item) in order_items(self.file_directives.items) {
            text.extend(Self::make_md_section(
                name,
                fence_size,
                item,
                max_visibility,
            ));
        }
        text.push(fence);

        text
    }

    fn fence_size(&self) -> usize {
        Self::calc_fence_size(&self.file_directives.items)
    }
}
