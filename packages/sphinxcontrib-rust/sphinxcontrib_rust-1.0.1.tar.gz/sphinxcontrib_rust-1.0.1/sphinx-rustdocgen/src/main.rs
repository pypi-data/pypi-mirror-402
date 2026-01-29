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

//! sphinx-rustdocgen is an executable to extract doc comments from Rust
//! crates. It is tightly coupled with the sphinxcontrib-rust extension and is
//! used by it during the Sphinx build process.
//!
//! Usage:
//!
//! .. code-block::
//!
//!    sphinx-rustdocgen <JSON config>
//!
//! See :rust:struct:`~sphinx_rustdocgen::Configuration` for the configuration
//! schema.

use std::env;

use sphinx_rustdocgen::traverse_crate;

const USAGE: &str = "sphinx-rustdocgen <JSON configuration>";

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 2 {
        panic!("Invalid number of arguments: {}\n\n{USAGE}", args.len());
    }

    traverse_crate(serde_json::from_str(&args[1]).unwrap())
}
