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

use std::collections::BTreeMap;

use ::syn;
use syn::{ItemUse, UseTree, Visibility};

use crate::directives::directive_options::DirectiveVisibility;
use crate::directives::{
    extract_doc_from_attrs,
    Directive,
    MdDirective,
    ModuleDirective,
    RstDirective,
};
use crate::formats::{MdOption, RstOption};

#[derive(Clone, Debug, Default)]
pub(crate) struct UsePathBuilder {
    pub(crate) path: Vec<String>,
    pub(crate) used_name: String,
}

/// Options for the use directive.
enum UseDirectiveOption {
    UsedName(String),
    Reexport(String),
}

impl RstOption for UseDirectiveOption {
    fn get_rst_text(&self, indent: &str) -> Option<String> {
        match self {
            UseDirectiveOption::UsedName(u) => Some(format!("{indent}:used_name: {u}")),
            UseDirectiveOption::Reexport(r) => Some(format!("{indent}:reexport: {r}")),
        }
    }
}

impl MdOption for UseDirectiveOption {
    fn get_md_text(&self) -> Option<String> {
        match self {
            UseDirectiveOption::UsedName(u) => Some(format!(":used_name: {u}")),
            UseDirectiveOption::Reexport(r) => Some(format!(":reexport: {r}")),
        }
    }
}

#[derive(Clone, Debug)]
pub struct UseDirective {
    pub(crate) paths: BTreeMap<String, String>,
    pub(crate) reexport: Option<String>,
    pub(crate) content: Vec<String>,
    directive_visibility: DirectiveVisibility,
}

impl UseDirective {
    const DIRECTIVE_NAME: &'static str = "use";

    /// Create a use directive for a path with the provided target.
    pub(crate) fn for_path(path: &str, target: &str) -> Self {
        UseDirective {
            paths: BTreeMap::from([(target.to_string(), path.to_string())]),
            reexport: None,
            content: vec![],
            directive_visibility: DirectiveVisibility::Pvt,
        }
    }

    /// Create a use directive using the provided used name to path map.
    pub(crate) fn for_use_paths(paths: BTreeMap<String, String>) -> Self {
        UseDirective {
            paths,
            reexport: None,
            content: vec![],
            directive_visibility: DirectiveVisibility::Pvt,
        }
    }

    /// Create a use directive and wrap it within the
    /// :rust:struct:`Directive::UseDirective` enum variant.
    pub(crate) fn from_item_as_directive(parent_path: &str, item: &ItemUse) -> Directive {
        Directive::Use(Self::from_item(parent_path, item))
    }

    /// Create a use directive from the AST item parsed by syn.
    pub(crate) fn from_item(parent_path: &str, item: &ItemUse) -> Self {
        // This is always the name of the crate being processed since the parent
        // path is either the crate name or the module path in which the use
        // statement appears. The module path will always begin with the crate
        // name.
        let crate_name = &parent_path[0..parent_path.find("::").unwrap_or(parent_path.len())];

        // Vec to hold use paths that are completely parsed out.
        let mut complete_paths = vec![];

        // Vec to hold use paths that are still being parsed out.
        // This is initialized with one empty path.
        let mut incomplete_paths = vec![UsePathBuilder::default()];

        // Stack of the items identified from the use paths.
        let mut item_stack = vec![&item.tree];

        while let Some(t) = item_stack.pop() {
            match t {
                UseTree::Path(p) => {
                    // Next ident from the path.
                    // Add this to the incomplete path at the top of the stack.

                    incomplete_paths
                        .last_mut()
                        .unwrap()
                        .path
                        .push(p.ident.to_string());
                    item_stack.push(&p.tree);
                }
                UseTree::Name(n) => {
                    // Imported a name. This completes the use path.

                    let mut use_path = incomplete_paths.pop().unwrap();

                    // Handle use paths that import self
                    let name = n.ident.to_string();
                    if name == "self" {
                        use_path.used_name.clone_from(use_path.path.last().unwrap());
                    }
                    else {
                        use_path.path.push(name.clone());
                        use_path.used_name = name;
                    }

                    // Handle use paths that start with crate or self
                    if use_path.path[0] == "crate" {
                        use_path.path[0] = crate_name.to_string();
                    }
                    else if use_path.path[0] == "self" {
                        use_path.path[0] = parent_path.to_string();
                    }

                    complete_paths.push(use_path);
                }
                UseTree::Rename(r) => {
                    // Imported and renamed. This completes the use path.

                    let mut use_path = incomplete_paths.pop().unwrap();
                    // Handle self imports
                    let name = r.ident.to_string();
                    if name != "self" {
                        use_path.path.push(name);
                    }
                    use_path.used_name = r.rename.to_string();
                    if use_path.path[0] == "crate" {
                        use_path.path[0] = crate_name.to_string();
                    }
                    complete_paths.push(use_path);
                }
                UseTree::Glob(_) => {
                    // Glob import. This completes the use path.
                    // Unsure what to do with the target here.
                    // For now, glob imports are just ignored.

                    incomplete_paths.pop();
                }
                UseTree::Group(g) => {
                    // Group of imports within curly braces.
                    // Create a copy of the current path on the stack for each
                    // item of the group and add back to the incomplete paths.
                    // Add all items from the group to the stack. In the next
                    // iteration of the loop, the last item from the group is
                    // fetched and processed until it terminates, and then the
                    // next item from the group is processed.

                    let last = incomplete_paths.pop().unwrap();
                    for _ in 0..g.items.len() {
                        incomplete_paths.push(last.clone());
                    }
                    for item in &g.items {
                        item_stack.push(item);
                    }
                }
            }
        }

        UseDirective {
            paths: complete_paths
                .into_iter()
                .map(|p| (p.used_name, p.path.join("::")))
                .collect(),
            reexport: if matches!(&item.vis, Visibility::Inherited) {
                None
            }
            else {
                Some(parent_path.into())
            },
            content: extract_doc_from_attrs(&item.attrs),
            directive_visibility: DirectiveVisibility::from(&item.vis),
        }
    }

    /// Resolve any relative paths using the list of modules provided.
    ///
    /// The method checks if any of the use paths are relative paths by
    /// comparing the first segment with the module's ident. If it matches,
    /// the path is updated to be an absolute path starting with the crate.
    pub(crate) fn resolve_relative_paths(&mut self, modules: &Vec<ModuleDirective>) {
        'path_loop: for path in self.paths.values_mut() {
            for module in modules {
                if path.starts_with(&format!("{}::", module.ident)) {
                    path.insert_str(
                        0,
                        &format!(
                            "{}::",
                            &module.name[0..module.name.rfind("::").unwrap_or(module.name.len())]
                        ),
                    );
                    continue 'path_loop;
                }
            }
        }
    }

    /// Check whether the directive contains the given path.
    ///
    /// This returns true if the ``item_path`` is one of the paths in the
    /// directive.
    pub(crate) fn contains(&self, item_path: &str) -> bool {
        self.paths.iter().any(|(_, path)| path == item_path)
    }

    /// Find the path for the given ident within the use directive, if any.
    pub(crate) fn find(&self, ident: &str) -> Option<&String> {
        self.paths
            .iter()
            .find(|&(used_name, _)| used_name == ident)
            .map(|(_, path)| path)
    }

    /// Return the visibility of this directive.
    pub(crate) fn directive_visibility(&self) -> &DirectiveVisibility {
        &self.directive_visibility
    }

    /// Inlines an item and returns it as a new ``(used_name, path)`` tuple.
    ///
    /// The new path is ``{reexport}::{used_name}`` of the old path. The used
    /// name for the new path is the same as that of the old path.
    ///
    /// Returns:
    ///     The function returns None if the directive is not a re-export or
    ///     a path matching the item was not found.
    pub(crate) fn inline(&mut self, item_name: &str) -> Option<(String, String)> {
        let mut found = None;
        if let Some(reexport) = &self.reexport {
            self.paths.retain(|used_name, path| {
                if path == item_name {
                    found = Some((used_name.clone(), format!("{reexport}::{used_name}")));
                    return false;
                }
                true
            });
        }
        found
    }
}

impl RstDirective for UseDirective {
    fn get_rst_text(self, level: usize, _: &DirectiveVisibility) -> Vec<String> {
        let mut text = vec![];
        for (used_name, path) in self.paths {
            let mut options = vec![UseDirectiveOption::UsedName(used_name)];
            if let Some(reexport) = &self.reexport {
                options.push(UseDirectiveOption::Reexport(reexport.clone()));
            }
            text.extend(Self::make_rst_header(
                Self::DIRECTIVE_NAME,
                path,
                &options,
                level,
            ));
        }

        text
    }
}

impl MdDirective for UseDirective {
    fn get_md_text(self, fence_size: usize, _: &DirectiveVisibility) -> Vec<String> {
        let fence = Self::make_fence(fence_size);
        let mut text = vec![];
        for (used_name, path) in self.paths {
            let mut options = vec![UseDirectiveOption::UsedName(used_name)];
            if let Some(reexport) = &self.reexport {
                options.push(UseDirectiveOption::Reexport(reexport.clone()));
            }
            text.extend(Self::make_md_header(
                Self::DIRECTIVE_NAME,
                path,
                &options,
                &fence,
            ));
            text.push(fence.clone());
        }

        text
    }
}
