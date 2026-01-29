use std::fmt::{Display, Formatter};
use std::str::FromStr;

use serde::Deserialize;
use syn::Visibility;

use crate::formats::{MdOption, RstOption};
use crate::nodes::Node;

/// Enum for the values of the :rust:struct:`DirectiveOption::Vis` option
///
/// The enum is ordered ``Pub < Crate < Pvt``, so it can be efficiently
/// compared for filtering. Note that ordering here is opposite to that of the
/// visibility itself.
#[derive(Clone, Copy, Debug, Default, Deserialize, Ord, PartialOrd, Eq, PartialEq)]
#[serde(rename_all = "lowercase")]
pub(crate) enum DirectiveVisibility {
    /// Public visibility
    #[default]
    Pub = 0,
    /// Crate visibility
    Crate = 1,
    /// Private visibility
    Pvt = 2,
}

impl DirectiveVisibility {
    /// Determine the effective visibility for an item based on its visibility
    /// or its parent's visibility.
    ///
    /// Args:
    ///     :visibility: The item's visibility.
    ///     :inherited_visibility: The visibility of the item's parent.
    ///
    /// Returns:
    ///     The directive visibility applicable to the item.
    pub(crate) fn effective_visibility(
        visibility: &Visibility,
        inherited_visibility: &Option<&Visibility>,
    ) -> Self {
        match visibility {
            Visibility::Public(_) => DirectiveVisibility::Pub,
            Visibility::Restricted(v) => {
                let path = &v.path;
                if path.segments.len() == 1 && path.segments.first().unwrap().ident == "crate" {
                    DirectiveVisibility::Crate
                }
                else {
                    DirectiveVisibility::Pvt
                }
            }
            Visibility::Inherited => match inherited_visibility {
                None => DirectiveVisibility::Pvt,
                Some(v) => Self::effective_visibility(v, &None),
            },
        }
    }
}

impl Display for DirectiveVisibility {
    fn fmt(&self, f: &mut Formatter<'_>) -> std::fmt::Result {
        f.write_str(match self {
            DirectiveVisibility::Pub => "pub",
            DirectiveVisibility::Crate => "crate",
            DirectiveVisibility::Pvt => "pvt",
        })
    }
}

impl From<&Visibility> for DirectiveVisibility {
    fn from(value: &Visibility) -> Self {
        Self::effective_visibility(value, &None)
    }
}

impl FromStr for DirectiveVisibility {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let s = s.to_lowercase();
        if s == "pub" {
            Ok(DirectiveVisibility::Pub)
        }
        else if s == "crate" {
            Ok(DirectiveVisibility::Crate)
        }
        else if s == "pvt" {
            Ok(DirectiveVisibility::Pvt)
        }
        else {
            Err(format!("Invalid value for visibility: {s}"))
        }
    }
}

/// The different index entry types.
///
/// This corresponds to the Python enum
/// :py:class:`sphinxcontrib_rust.items.SphinxIndexEntryType`.
#[derive(Copy, Clone, Debug)]
#[repr(i8)]
pub(crate) enum IndexEntryType {
    None = -1,
    Normal = 0,
    WithSubEntries = 1,
    SubEntry = 2,
}

/// Enum to represent the various options for the directives.
///
/// The enum implements the :rust:trait:`RstOption` and :rust:trait:`MdOption`
/// traits for easily converting the options to required text.
#[derive(Clone, Debug)]
pub(crate) enum DirectiveOption {
    /// The ``:index:`` option
    Index(IndexEntryType),
    /// The ``:vis:`` option.
    Vis(DirectiveVisibility),
    /// The ``:layout:`` option.
    Layout(Vec<Node>),
    /// The ``:toc:`` option.
    Toc(String),
}

impl RstOption for DirectiveOption {
    fn get_rst_text(&self, indent: &str) -> Option<String> {
        Some(match self {
            DirectiveOption::Index(i) => {
                format!("{indent}:index: {}", *i as i8)
            }
            DirectiveOption::Vis(v) => {
                format!("{indent}:vis: {v}")
            }
            DirectiveOption::Toc(t) => {
                format!("{indent}:toc: {t}")
            }
            DirectiveOption::Layout(lines) => {
                format!("{indent}:layout: {}", serde_json::to_string(lines).unwrap())
            }
        })
    }
}

impl MdOption for DirectiveOption {
    fn get_md_text(&self) -> Option<String> {
        Some(match self {
            DirectiveOption::Index(i) => {
                format!(":index: {}", *i as i8)
            }
            DirectiveOption::Vis(v) => {
                format!(":vis: {v}")
            }
            DirectiveOption::Toc(t) => {
                format!(":toc: {t}")
            }
            DirectiveOption::Layout(lines) => {
                format!(":layout: {}", serde_json::to_string(lines).unwrap())
            }
        })
    }
}
