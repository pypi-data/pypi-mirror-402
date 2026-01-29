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

//! Module for handling the output formats supported.

use std::fmt::Display;
use std::str::FromStr;

use serde::Deserialize;

use crate::directives::{Directive, DirectiveVisibility};

/// Generate title decoration string for RST or fence for MD.
///
/// Args:
///     :ch: The character to use.
///     :len: The length of the decoration required.
///
/// Returns:
///     A string of length ``len`` composed entirely of ``ch``.
fn generate_decoration(ch: char, len: usize) -> String {
    let mut decoration = String::with_capacity(len);
    for _ in 0..len {
        decoration.push(ch);
    }
    decoration
}

/// Supported formats for the docstrings
#[derive(Copy, Clone, Debug, Default, Deserialize, Hash, PartialEq, Eq)]
pub(crate) enum Format {
    /// Markdown format
    #[serde(rename(deserialize = "md"))]
    Md,
    /// reStructuredText format
    #[default]
    #[serde(rename(deserialize = "rst"))]
    Rst,
}

impl Format {
    /// Acceptable text values for Md variant, case-insensitive.
    const MD_VALUES: [&'static str; 3] = ["md", ".md", "markdown"];
    /// Acceptable text values for Rst variant, case-insensitive.
    const RST_VALUES: [&'static str; 3] = ["rst", ".rst", "restructuredtext"];

    /// Returns the extension for the format, without the leading ".".
    pub fn extension(&self) -> &'static str {
        match self {
            Format::Md => Self::MD_VALUES[0],
            Format::Rst => Self::RST_VALUES[0],
        }
    }

    /// Convert the provided text to an inline code representation of the text
    /// specific to the format.
    pub(crate) fn make_inline_code<D: Display>(&self, text: D) -> String {
        match self {
            Format::Md => format!("`{text}`"),
            Format::Rst => format!("``{text}``"),
        }
    }

    /// Make a format specific document title using the provided title string.
    pub(crate) fn make_title(&self, title: &str) -> Vec<String> {
        match self {
            Format::Md => {
                vec![format!("# {title}"), String::new()]
            }
            Format::Rst => {
                let decoration = generate_decoration('=', title.len());
                vec![
                    decoration.clone(),
                    title.to_string(),
                    decoration,
                    String::new(),
                ]
            }
        }
    }

    /// Get format specific content for the directive for the output file.
    ///
    /// The function assumes that the directive is the top level directive of
    /// the output file and generates the content accordingly.
    ///
    /// Args:
    ///     :directive: The directive to get the content for, typically a
    ///         ``Crate`` or ``Module`` directive.
    ///
    /// Returns:
    ///     A vec of strings which are the lines of the document.
    pub(crate) fn format_directive<T>(
        &self,
        directive: T,
        max_visibility: &DirectiveVisibility,
    ) -> Vec<String>
    where
        T: RstDirective + MdDirective,
    {
        match self {
            Format::Md => {
                let fence_size = directive.fence_size();
                directive.get_md_text(fence_size, max_visibility)
            }
            Format::Rst => directive.get_rst_text(0, max_visibility),
        }
    }
}

impl FromStr for Format {
    type Err = String;

    /// Parses the string into an enum value, or panics.
    ///
    /// If the string is ``md``, ``.md`` or ``markdown``, the function
    /// returns ``Md``. If the string is ``rst``, ``.rst`` or
    /// ``restructuredtext``, the function returns ``Rst``. Comparison is
    /// case-insensitive.
    ///
    /// Args:
    ///     :value: The value to parse.
    ///
    /// Returns:
    ///     The parsed enum value as the Ok value, or unit type as the Err.
    fn from_str(value: &str) -> Result<Self, Self::Err> {
        let value_lower = value.to_lowercase();
        if Self::RST_VALUES.contains(&&*value_lower) {
            Ok(Format::Rst)
        }
        else if Self::MD_VALUES.contains(&&*value_lower) {
            Ok(Format::Md)
        }
        else {
            Err(format!("Not a valid format value: {value}"))
        }
    }
}

/// Trait for directives that can be written as RST content
pub(crate) trait RstDirective {
    const INDENT: &'static str = "   ";

    /// Generate RST text with the given level of indentation.
    ///
    /// Implementations must provide a vec of the lines of the content of the
    /// item and all its members.
    ///
    /// Args:
    ///     :level: The level of indentation for the content. Use the
    ///         ``make_indent`` and ``make_content_indent`` functions to get
    ///         the actual indentation string.
    ///     :max_visibility: Include only items with visibility up to the
    ///         defined level.
    ///
    /// Returns:
    ///     The RST text for the documentation of the item and its members.
    fn get_rst_text(self, level: usize, max_visibility: &DirectiveVisibility) -> Vec<String>;

    /// Make a string for indenting the directive.
    ///
    /// Args:
    ///     :level: The level of the indentation.
    ///
    /// Returns:
    ///     A string that is ``Self::INDENT`` repeated ``level`` times.
    fn make_indent(level: usize) -> String {
        let mut indent = String::with_capacity(Self::INDENT.len() * level);
        for _ in 0..level {
            indent += Self::INDENT;
        }
        indent
    }

    /// Make a string for indenting the directive's content and options
    ///
    /// Args:
    ///     :level: The level of the indentation.
    ///
    /// Returns:
    ///     A string that is ``Self::INDENT`` repeated ``level + 1`` times.
    fn make_content_indent(level: usize) -> String {
        Self::make_indent(level + 1)
    }

    /// Make the RST directive header from the directive, name and options.
    ///
    /// Args:
    ///     :directive: The RST directive to make the header for.
    ///     :name: The name of the directive.
    ///     :options: The directive options to add.
    ///     :level: The indentation level of the directive.
    ///
    /// Returns:
    ///     A Vec of the directive's header lines.
    fn make_rst_header<O: RstOption, D: Display, E: Display>(
        directive: D,
        name: E,
        options: &[O],
        level: usize,
    ) -> Vec<String> {
        let indent = &Self::make_indent(level);
        let option_indent = &Self::make_indent(level + 1);
        let mut header = Vec::with_capacity(3 + options.len());
        header.push(String::new());
        header.push(
            format!("{indent}.. rust:{directive}:: {name}")
                .trim_end()
                .to_string(),
        );
        options
            .iter()
            .filter_map(|o| o.get_rst_text(option_indent))
            .for_each(|t| header.push(t));
        header.push(String::new());
        header
    }

    /// Make a ``toctree`` directive for RST documents.
    ///
    /// Args:
    ///     :indent: The indentation for the directive.
    ///     :caption: The caption for the ``toctree``.
    ///     :maxdepth: The desired ``maxdepth`` of the ``toctree``. If None,
    ///         the ``:maxdepth:`` option will not be set.
    ///     :tree: The ``toctree`` entries.
    fn make_rst_toctree<I: Display, T: Iterator<Item = I>>(
        indent: &str,
        caption: &str,
        max_depth: Option<u8>,
        tree: T,
    ) -> Vec<String> {
        let tree: Vec<I> = tree.collect();
        if tree.is_empty() {
            return Vec::new();
        }

        let mut toc_tree = vec![
            String::new(),
            format!("{indent}.. rubric:: {caption}"),
            format!("{indent}.. toctree::"),
        ];
        if let Some(md) = max_depth {
            toc_tree.push(format!("{indent}{}:maxdepth: {md}", Self::INDENT));
        }
        toc_tree.push(String::new());

        for item in tree {
            toc_tree.push(format!("{indent}{}{item}", Self::INDENT));
        }
        toc_tree.push(String::new());
        toc_tree
    }

    /// Make section in an RST document with the given title and items.
    ///
    /// Args:
    ///     :section: The title of the section.
    ///     :level: The indentation level of the section.
    ///     :items: The items to include in the section.
    ///     :max_visibility: The max visibility of the items to include.
    ///
    /// Returns:
    ///     The RST text for the section.
    fn make_rst_section(
        section: &str,
        level: usize,
        items: Vec<Directive>,
        max_visibility: &DirectiveVisibility,
    ) -> Vec<String> {
        let indent = Self::make_content_indent(level);
        let mut section = vec![
            String::new(),
            format!("{indent}.. rubric:: {section}"),
            String::new(),
        ];
        for item in items {
            section.extend(item.get_rst_text(level + 1, max_visibility))
        }
        // If nothing was added to the section, return empty vec.
        if section.len() > 3 {
            section
        }
        else {
            Vec::new()
        }
    }

    /// Make an RST list of items.
    ///
    /// Args:
    ///     :indent: The indentation for the list items.
    ///     :title: The title for the list.
    ///     :items: A vec of item name and content tuples.
    ///
    /// Returns:
    ///     Lines of RST text for the list, with the title.
    fn make_rst_list(indent: &str, title: &str, items: &[(String, Vec<String>)]) -> Vec<String> {
        if items.is_empty() {
            return vec![];
        }

        let mut text = vec![format!("{indent}.. rubric:: {title}"), String::new()];
        for (item, content) in items {
            text.push(format!("{indent}* :rust:any:`{item}`"));
            text.extend(content.iter().map(|l| format!("{indent}  {l}")));
        }
        text
    }
}

/// Trait for directives that can be written as MD content
pub(crate) trait MdDirective {
    const DEFAULT_FENCE_SIZE: usize = 4;

    /// Generate MD text with the given fence size.
    ///
    /// Implementations must provide a vec of the lines of the content of the
    /// item and all its members.
    ///
    /// Args:
    ///     :fence_size: The size of the fence for the directive. Use the
    ///         ``make_fence`` function to get the actual fence string.
    ///     :max_visibility: Include only items with visibility up to the
    ///         defined level.
    ///
    /// Returns:
    ///     The MD text for the documentation of the item and its members.
    fn get_md_text(self, fence_size: usize, max_visibility: &DirectiveVisibility) -> Vec<String>;

    /// Make a string for the fences for the directive.
    ///
    /// Args:
    ///     :fence_size: The size of the fence, must be at least 3.
    ///
    /// Returns:
    ///     A string of colons of length ``fence_size``.
    ///
    /// Panics:
    ///     If the ``fence_size`` is less than 3.
    fn make_fence(fence_size: usize) -> String {
        if fence_size < 3 {
            panic!("Invalid fence size {fence_size}. Must be >= 3");
        }
        generate_decoration(':', fence_size)
    }

    /// Calculate the fence size required for the item.
    ///
    /// The ``items`` are the members of the current item. So, for
    /// a struct, these will be the list of its fields, for an enum,
    /// the variants, for a module, the items defined in it, etc.
    ///
    /// The fence size for the item is 1 + the max fence size of all
    /// its members. If it has no members, the fence size is the default fence
    /// size. So, the returned value is the minimum fence size required to
    /// properly document the item and its members in Markdown.
    ///
    /// Args:
    ///     :items: Items which are members of the current item.
    ///
    /// Returns:
    ///     The minimum fence size required to document the item and all its
    ///     nested items.
    fn calc_fence_size(items: &[Directive]) -> usize {
        match items.iter().map(Directive::fence_size).max() {
            Some(s) => s + 1,
            None => Self::DEFAULT_FENCE_SIZE,
        }
    }

    /// Make the MD directive header from the directive, name and options.
    ///
    /// Args:
    ///     :directive: The MD directive to make the header for.
    ///     :name: The name of the directive.
    ///     :options: The directive options to add.
    ///     :fence: The fence to use for the directive.
    ///
    /// Returns:
    ///     A Vec of the directive's header lines.
    fn make_md_header<O: MdOption, D: Display, E: Display>(
        directive: D,
        name: E,
        options: &[O],
        fence: &str,
    ) -> Vec<String> {
        let mut header = Vec::with_capacity(2 + options.len());
        header.push(
            format!("{fence}{{rust:{directive}}} {name}")
                .trim_end()
                .to_string(),
        );
        options
            .iter()
            .filter_map(|o| o.get_md_text())
            .for_each(|t| header.push(t));
        header.push(String::new());
        header
    }

    /// Make a ``toctree`` directive for MD documents.
    ///
    /// Args:
    ///     :fence_size: The fence size for the directive.
    ///     :caption: The caption for the ``toctree``.
    ///     :maxdepth: The desired ``maxdepth`` of the ``toctree``. If None,
    ///         the ``:maxdepth:`` option will not be set.
    ///     :tree: The ``toctree`` entries.
    fn make_md_toctree<I: Display, T: Iterator<Item = I>>(
        fence_size: usize,
        caption: &str,
        max_depth: Option<u8>,
        tree: T,
    ) -> Vec<String> {
        let tree: Vec<I> = tree.collect();
        if tree.is_empty() {
            return Vec::new();
        }

        let fence = Self::make_fence(fence_size);
        let mut toc_tree = vec![
            String::new(),
            format!("{fence}{{rubric}} {caption}"),
            fence.clone(),
            format!("{fence}{{toctree}}"),
        ];
        if let Some(md) = max_depth {
            toc_tree.push(format!(":maxdepth: {md}"));
        }
        toc_tree.push(String::new());
        for item in tree {
            toc_tree.push(item.to_string());
        }
        toc_tree.push(fence);
        toc_tree
    }

    /// Make section in an MD document with the given title and items.
    ///
    /// Args:
    ///     :section: The title of the section.
    ///     :fence_size: The fence size of the section.
    ///     :items: The items to include in the section.
    ///     :max_visibility: The max visibility of the items to include.
    ///
    /// Returns:
    ///     The MD text for the section.
    fn make_md_section(
        section: &str,
        fence_size: usize,
        items: Vec<Directive>,
        max_visibility: &DirectiveVisibility,
    ) -> Vec<String> {
        let fence = Self::make_fence(3);
        let mut section = vec![
            String::new(),
            format!("{fence}{{rubric}} {section}"),
            fence,
            String::new(),
        ];
        for item in items {
            section.extend(item.get_md_text(fence_size - 1, max_visibility))
        }
        // If nothing was added to the section, return empty vec.
        if section.len() > 4 {
            section
        }
        else {
            Vec::new()
        }
    }

    /// Make an MD list of items.
    ///
    /// Args:
    ///     :fence_size: The fence size for the list title.
    ///     :title: The title for the list.
    ///     :items: A vec of item name and content tuples.
    ///
    /// Returns:
    ///     Lines of MD text for the list, with the title.
    fn make_md_list(
        fence_size: usize,
        title: &str,
        items: &[(String, Vec<String>)],
    ) -> Vec<String> {
        if items.is_empty() {
            return vec![];
        }

        let fence = Self::make_fence(fence_size);
        let mut text = vec![format!("{fence}{{rubric}} {title}"), fence, String::new()];
        for (item, content) in items {
            text.push(format!(
                "* {{rust:any}}`{item}`{}",
                if content.is_empty() {
                    ""
                }
                else {
                    "  "
                }
            ));
            text.extend(content.iter().map(|l| format!("  {l}")));
        }
        text
    }

    /// Return the fence size required for documenting the item.
    ///
    /// The default implementation returns ``4``, which allows for members
    /// with no items to create sections within the docstrings, that do not
    /// show up in the ``toctree``.
    ///
    /// Implementations may use
    /// :rust:fn:`MdDirective::calc_fence_size`
    /// to override this, when there are nested items present.
    fn fence_size(&self) -> usize {
        Self::DEFAULT_FENCE_SIZE
    }
}

/// Trait for RST directive options.
pub(crate) trait RstOption {
    /// Return the RST text for the option.
    fn get_rst_text(&self, indent: &str) -> Option<String>;
}

/// Trait for MD directive options
pub(crate) trait MdOption {
    /// Return the MD text for the option.
    fn get_md_text(&self) -> Option<String>;
}

/// Trait for anything that can be converted to RST directive content.
///
/// This is implemented for all ``IntoIterator<Item = String>``, effectively
/// allowing ``Vec<String>`` to be converted to RST content lines.
pub(crate) trait RstContent {
    fn get_rst_text(self, indent: &str) -> Vec<String>;
}

impl<T> RstContent for T
where
    T: IntoIterator<Item = String>,
{
    fn get_rst_text(self, indent: &str) -> Vec<String> {
        self.into_iter().map(|s| format!("{indent}{s}")).collect()
    }
}

/// Trait for anything that can be converted to MD directive content.
///
/// This is implemented for all ``IntoIterator<Item = String>``, effectively
/// allowing ``Vec<String>`` to be converted to MD content lines.
pub(crate) trait MdContent {
    fn get_md_text(self) -> Vec<String>;
}

impl<T> MdContent for T
where
    T: IntoIterator<Item = String>,
{
    fn get_md_text(self) -> Vec<String> {
        let mut text = vec![String::from("  :::")];
        text.extend(self.into_iter().map(|s| format!("  {s}")));
        text.push(String::from("  :::"));
        text
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_decoration() {
        assert_eq!(generate_decoration('=', 0), "");
        assert_eq!(generate_decoration('=', 1), "=");
        assert_eq!(generate_decoration('=', 5), "=====");
    }

    #[test]
    fn test_format() {
        let rst = Format::Rst;
        assert_eq!(rst.extension(), "rst");
        assert_eq!(rst.make_title("foo"), vec!["===", "foo", "===", ""]);
        assert_eq!(
            rst.make_title(&rst.make_inline_code("foo")),
            vec!["=======", "``foo``", "=======", ""]
        );
        assert_eq!(Format::from_str("rst").unwrap(), rst);

        let md = Format::Md;
        assert_eq!(md.extension(), "md");
        assert_eq!(md.make_title("foo"), vec!["# foo", ""]);
        assert_eq!(
            md.make_title(&md.make_inline_code("foo")),
            vec!["# `foo`", ""]
        );
        assert_eq!(Format::from_str("md").unwrap(), md);

        assert!(Format::from_str("foo").is_err());
    }

    #[test]
    fn test_content_traits() {
        let text: Vec<String> = ["line 1", "line 2", "line 3"]
            .iter()
            .map(|&s| s.to_string())
            .collect();
        let expected = vec!["  :::", "  line 1", "  line 2", "  line 3", "  :::"];
        assert_eq!(text.clone().get_rst_text("  "), &expected[1..4]);
        assert_eq!(text.clone().get_md_text(), expected);
    }
}
