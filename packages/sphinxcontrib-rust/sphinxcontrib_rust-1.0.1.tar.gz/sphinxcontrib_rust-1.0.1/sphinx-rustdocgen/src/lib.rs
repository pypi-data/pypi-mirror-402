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

//! Library for the sphinx-rustdocgen executable.
//!
//! It consists of functions to extract content from the AST and
//! to write the content to an RST or MD file. The crate is tested on itself,
//! so all the documentation in the crate is in RST. The tests for Markdown
//! are done on the dependencies.

// pub(crate) mainly to test re-exports
pub(crate) mod directives;
mod formats;
mod nodes;
mod utils;

use std::fs::{create_dir_all, File};
use std::io::Write;
use std::path::{Path, PathBuf};

use serde::Deserialize;

use crate::directives::{CrateDirective, DirectiveVisibility, ExecutableDirective};
use crate::formats::Format;
// pub(crate) mainly to test re-exports
pub(crate) use crate::utils::{check_for_manifest, SourceCodeFile};

/// Struct to hold the deserialized configuration passed from Python.
#[derive(Clone, Debug, Deserialize)]
pub struct Configuration {
    /// The name of the crate.
    crate_name: String,
    /// The directory containing the Cargo.toml file for the crate.
    crate_dir: PathBuf,
    /// The directory under which to create the crate's documentation.
    /// A new directory is created under this directory for the crate.
    doc_dir: PathBuf,
    /// Rebuild document for all files, even if it has not changed.
    #[serde(default)]
    force: bool,
    /// The format to use for the output.
    #[serde(default)]
    format: Format,
    /// The required visibility of the items to include.
    #[serde(default)]
    visibility: DirectiveVisibility,
    /// Whether to remove the src/ directory when generating the docs or not.
    strip_src: bool,
}

impl Configuration {
    /// Canonicalize the crate directory and return it.
    fn get_canonical_crate_dir(&self) -> PathBuf {
        // Canonicalize, which also checks that it exists.
        let crate_dir = match self.crate_dir.canonicalize() {
            Ok(d) => d,
            Err(e) => panic!("Could not find directory {}", e),
        };
        if !crate_dir.is_dir() {
            panic!("{} is not a directory", crate_dir.to_str().unwrap());
        }
        crate_dir
    }
}

/// Runtime version of the configuration after validation and normalizing.
struct RuntimeConfiguration {
    /// The name of the crate in the configuration.
    crate_name: String,
    /// The crate's root directory, the one which contains ``Cargo.toml``.
    crate_dir: PathBuf,
    /// The crate's src/ directory, if one is found and ``strip_src`` is true.
    src_dir: Option<PathBuf>,
    /// The directory under which to write the documents.
    doc_dir: PathBuf,
    /// Whether to rewrite all the documents, even the ones that are unchanged.
    force: bool,
    /// The format of the docstrings.
    format: Format,
    /// Only document items with visibility less than this.
    max_visibility: DirectiveVisibility,
    /// The executables within the crate that will be documented.
    executables: Vec<SourceCodeFile>,
    /// The crate's library to document, if any.
    lib: Option<SourceCodeFile>,
}

impl RuntimeConfiguration {
    /// Write a documentation file for the provided source file path and
    /// content.
    ///
    /// Args:
    ///     :source_file_path: The path of the source file corresponding to the
    ///         content.
    ///     :content_fn: A function to extract the content for the file.
    fn write_doc_file<F: for<'a> FnOnce(&'a Format, &'a DirectiveVisibility) -> Vec<String>>(
        &self,
        source_file_path: &Path,
        content_fn: F,
    ) {
        let rel_path = source_file_path
            .strip_prefix(self.src_dir.as_ref().unwrap_or(&self.crate_dir))
            .unwrap_or(source_file_path);

        // For mod.rs files, the output file name is the parent directory name.
        // Otherwise, it is same as the file name.
        let mut doc_file = if rel_path.ends_with("mod.rs") {
            rel_path.parent().unwrap().to_owned()
        }
        else {
            rel_path
                .parent()
                .unwrap()
                .join(rel_path.file_stem().unwrap())
        };

        // Add the extension for the file.
        doc_file.set_extension(self.format.extension());

        // Convert to absolute path.
        // Cannot use canonicalize here since it will error.
        let doc_file = self.doc_dir.join(doc_file);

        // Create the directories for the output document.
        create_dir_all(doc_file.parent().unwrap()).unwrap();

        // If file doesn't exist or the module file has been modified since the
        // last modification of the doc file, create/truncate it and rebuild the
        // documentation.
        if self.force
            || !doc_file.exists()
            || doc_file.metadata().unwrap().modified().unwrap()
                < source_file_path.metadata().unwrap().modified().unwrap()
        {
            log::debug!("Writing docs to file {}", doc_file.to_str().unwrap());
            let mut doc_file = File::create(doc_file).unwrap();
            for line in content_fn(&self.format, &self.max_visibility) {
                writeln!(&mut doc_file, "{line}").unwrap();
            }
        }
        else {
            log::debug!("Docs are up to date")
        }
    }
}

impl From<Configuration> for RuntimeConfiguration {
    /// Create a validated and normalized version of the
    /// :rust:struct:`Configuration`.
    fn from(config: Configuration) -> Self {
        // Canonicalize, which also checks that it exists.
        let crate_dir = config.get_canonical_crate_dir();

        // Check if the crate dir contains Cargo.toml
        // Also, check parent to provide backwards compatibility for src/ paths.
        let (crate_dir, manifest) =
            match check_for_manifest(vec![&crate_dir, crate_dir.parent().unwrap()]) {
                None => panic!(
                    "Could not find Cargo.toml in {} or its parent directory",
                    crate_dir.to_str().unwrap()
                ),
                Some(m) => m,
            };
        let executables = manifest.executable_files(&crate_dir);
        let lib = manifest.lib_file(&crate_dir);

        // The output docs currently strip out the src from any docs. To prevent
        // things from breaking, that behavior is preserved. It may cause issues
        // for crates that have a src dir and also files outside of it. However,
        // that will likely be rare. Hence, the new configuration option.
        let src_dir = crate_dir.join("src");
        let src_dir = if src_dir.is_dir() && config.strip_src {
            Some(src_dir)
        }
        else {
            None
        };

        // Add the crate's directory under the doc dir and create it.
        let doc_dir = config.doc_dir.join(&config.crate_name);
        create_dir_all(&doc_dir).unwrap();

        RuntimeConfiguration {
            crate_dir,
            crate_name: config.crate_name,
            src_dir,
            doc_dir: doc_dir.canonicalize().unwrap(),
            force: config.force,
            format: config.format,
            max_visibility: config.visibility,
            executables,
            lib,
        }
    }
}

// noinspection DuplicatedCode
/// Traverse the crate and extract the docstrings for the items.
///
/// Args:
///     :config: The configuration for the crate.
pub fn traverse_crate(config: Configuration) {
    let runtime: RuntimeConfiguration = config.into();

    log::debug!(
        "Extracting docs for crate {} from {}",
        &runtime.crate_name,
        runtime.crate_dir.to_str().unwrap()
    );
    log::debug!(
        "Generated docs will be stored in {}",
        runtime.doc_dir.to_str().unwrap()
    );

    if let Some(file) = &runtime.lib {
        let mut lib = CrateDirective::new(file);
        lib.filter_items(&runtime.max_visibility);

        // TODO: Remove the cloning here
        let mut modules = lib.file_directives.modules.clone();
        while let Some(module) = modules.pop() {
            for submodule in &module.file_directives.modules {
                modules.push(submodule.clone());
            }

            runtime.write_doc_file(&module.source_code_file.path.clone(), |f, v| {
                module.text(f, v)
            });
        }

        runtime.write_doc_file(&file.path, |f, v| lib.text(f, v));
    }

    for file in &runtime.executables {
        let mut exe = ExecutableDirective::new(file);
        exe.filter_items(&runtime.max_visibility);

        let mut modules = exe.0.file_directives.modules.clone();
        while let Some(module) = modules.pop() {
            for submodule in &module.file_directives.modules {
                modules.push(submodule.clone());
            }

            runtime.write_doc_file(&module.source_code_file.path.clone(), |f, v| {
                module.text(f, v)
            });
        }

        runtime.write_doc_file(&file.path, |f, v| exe.text(f, v));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_self() {
        // Test just extracts the documents for the current crate. This avoids
        // creating unnecessary test files when the source code itself can be
        // used.
        traverse_crate(Configuration {
            crate_name: String::from("sphinx-rustdocgen"),
            crate_dir: Path::new(".").to_owned(),
            doc_dir: Path::new("../docs/crates").to_owned(),
            format: Format::Rst,
            visibility: DirectiveVisibility::Pvt,
            force: true,
            strip_src: true,
        })
    }

    #[test]
    fn test_markdown() {
        traverse_crate(Configuration {
            crate_name: String::from("test_crate"),
            crate_dir: Path::new("../tests/test_crate").to_owned(),
            doc_dir: Path::new("../tests/test_crate/docs/crates").to_owned(),
            format: Format::Md,
            visibility: DirectiveVisibility::Pvt,
            force: true,
            strip_src: true,
        })
    }
}
