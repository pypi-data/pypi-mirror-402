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

//! Module for various utility classes and structs.

use std::fs::read_to_string;
use std::path::{Path, PathBuf};

use cargo_toml::{Manifest, Product};

/// Check the provided paths for the Cargo.toml file.
///
/// Returns:
///     A Some value of the path that contained the Cargo manifest and the
///     associated manifest for the first path contains a ``Cargo.toml`` file.
pub(crate) fn check_for_manifest(paths: Vec<&Path>) -> Option<(PathBuf, CargoManifest)> {
    for path in paths {
        let manifest_path = path.join("Cargo.toml");
        if manifest_path.is_file() {
            return Some((
                path.into(),
                CargoManifest(Manifest::from_path(manifest_path).unwrap()),
            ));
        }
    }
    None
}

/// Struct for the source code files encountered when scanning the crate.
#[derive(Clone, Debug)]
pub(crate) struct SourceCodeFile {
    /// The path to the file.
    pub(crate) path: PathBuf,
    /// The name of the item in the file.
    pub(crate) item: String,
}

impl SourceCodeFile {
    /// Generate and return the AST for the file.
    pub(crate) fn ast(&self) -> syn::File {
        syn::parse_file(&read_to_string(&self.path).unwrap()).unwrap()
    }

    /// Get the parent directory of the file for the item.
    ///
    /// The item of the returned struct is the same as this struct's item.
    /// This is mainly used for ``mod.rs`` and ``lib.rs`` files, where the
    /// directory name determines the item's name.
    pub(crate) fn to_parent_directory(&self) -> Self {
        SourceCodeFile {
            path: self.path.parent().as_ref().unwrap().into(),
            item: self.item.clone(),
        }
    }

    /// Create an instance for the product in the crate.
    ///
    /// Args:
    ///     :prd: The product for which the file should be created.
    ///     :crate_dir: The path for the crate's directory, used to
    ///         generate the absolute path for the file.
    fn from_product(prd: &Product, crate_dir: &Path) -> Self {
        SourceCodeFile {
            path: crate_dir.join(prd.path.as_ref().unwrap()),
            item: prd.name.as_ref().unwrap().clone(),
        }
    }

    /// Returns the name of the crate from the item name.
    pub(crate) fn crate_name(&self) -> &str {
        &self.item[0..self.item.find("::").unwrap_or(self.item.len())]
    }
}

/// Newtype struct for the Cargo manifest from cargo_toml.
pub(crate) struct CargoManifest(Manifest);

impl CargoManifest {
    /// Get the library file for the crate, if any.
    pub(crate) fn lib_file(&self, crate_dir: &Path) -> Option<SourceCodeFile> {
        self.0
            .lib
            .as_ref()
            .map(|lib| SourceCodeFile::from_product(lib, crate_dir))
    }

    /// Get all the executable files in the crate.
    pub(crate) fn executable_files(&self, crate_dir: &Path) -> Vec<SourceCodeFile> {
        self.0
            .bin
            .iter()
            .map(|prd| SourceCodeFile::from_product(prd, crate_dir))
            .collect()
    }
}
