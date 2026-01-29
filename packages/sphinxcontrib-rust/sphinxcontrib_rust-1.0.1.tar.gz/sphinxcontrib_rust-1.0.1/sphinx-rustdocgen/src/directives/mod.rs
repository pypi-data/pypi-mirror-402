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

//! Module for the various Sphinx directives for the Rust domain.
//!
//! The module primarily provides the :rust:enum:`Directive`, which implements
//! the various directives using directive specific structs. The enum and all
//! directive specific structs implement both
//! :rust:trait:`~sphinx_rustdocgen::formats::RstContent` and
//! :rust:trait:`~sphinx_rustdocgen::formats::MdContent` traits.
//! It also provides the :rust:enum:`DirectiveOption` enum, which
//! implements the various options of the directive.
//!
//! The output of the directives is parsed by the
//! :py:class:`sphinxcontrib_rust.directives.RustDirective` within the Python
//! extension.

mod crate_directive;
mod directive_options;
mod enum_directive;
mod executable_directive;
mod function_directive;
mod impl_directive;
mod macro_directive;
mod module_directive;
mod struct_directive;
mod trait_directive;
mod type_directive;
mod use_directive;
mod variable_directive;

use syn::{Attribute, Expr, ForeignItem, ImplItem, Item, Lit, TraitItem, Visibility};

// Re-exports are mainly for testing
pub use crate::directives::crate_directive::CrateDirective;
pub(crate) use crate::directives::directive_options::DirectiveVisibility;
pub use crate::directives::enum_directive::EnumDirective;
pub use crate::directives::executable_directive::ExecutableDirective;
pub use crate::directives::function_directive::FunctionDirective;
pub use crate::directives::impl_directive::ImplDirective;
pub use crate::directives::macro_directive::MacroDirective;
pub use crate::directives::module_directive::ModuleDirective;
pub use crate::directives::struct_directive::StructDirective;
pub use crate::directives::trait_directive::TraitDirective;
pub use crate::directives::type_directive::TypeDirective;
pub use crate::directives::use_directive::UseDirective;
pub use crate::directives::variable_directive::VariableDirective;
use crate::formats::{MdDirective, RstDirective};
use crate::utils::SourceCodeFile;

/// The Sphinx directives that are implemented by the Rust domain.
#[derive(Clone, Debug)]
pub(crate) enum Directive {
    Crate(CrateDirective),
    Enum(EnumDirective),
    Executable(ExecutableDirective),
    Function(FunctionDirective),
    Impl(ImplDirective),
    Macro(MacroDirective),
    Module(ModuleDirective),
    Struct(StructDirective),
    Trait(TraitDirective),
    Type(TypeDirective),
    Use(UseDirective),
    Variable(VariableDirective),
}

impl Directive {
    fn name(&self) -> &str {
        match self {
            Directive::Crate(c) => &c.name,
            Directive::Enum(e) => &e.name,
            Directive::Executable(e) => &e.0.name,
            Directive::Function(f) => &f.name,
            Directive::Impl(i) => &i.name,
            Directive::Macro(m) => &m.name,
            Directive::Module(m) => &m.name,
            Directive::Struct(s) => &s.name,
            Directive::Trait(t) => &t.name,
            Directive::Type(t) => &t.name,
            Directive::Use(_) => {
                unreachable!("name is used for sorting, which is not done for UseDirective")
            }
            Directive::Variable(v) => &v.name,
        }
    }

    /// Change the parent of the directive.
    fn change_parent(&mut self, new_parent: &str) {
        match self {
            Directive::Crate(_) => {
                unreachable!("Crate directive shouldn't have parent")
            }
            Directive::Enum(e) => e.change_parent(new_parent),
            Directive::Executable(_) => {
                unreachable!("Executable directive shouldn't have parent")
            }
            Directive::Function(f) => f.change_parent(new_parent),
            Directive::Impl(i) => i.change_parent(new_parent),
            Directive::Macro(m) => m.change_parent(new_parent),
            Directive::Module(m) => m.change_parent(new_parent),
            Directive::Struct(s) => s.change_parent(new_parent),
            Directive::Trait(t) => t.change_parent(new_parent),
            Directive::Type(t) => t.change_parent(new_parent),
            Directive::Use(_) => {}
            Directive::Variable(v) => v.change_parent(new_parent),
        }
    }

    /// Get the visibility of the directive.
    fn directive_visibility(&self) -> &DirectiveVisibility {
        match self {
            Directive::Crate(_) => &DirectiveVisibility::Pub,
            Directive::Enum(e) => e.directive_visibility(),
            Directive::Executable(_) => &DirectiveVisibility::Pub,
            Directive::Function(f) => f.directive_visibility(),
            Directive::Impl(i) => i.directive_visibility(),
            Directive::Macro(m) => m.directive_visibility(),
            Directive::Module(m) => m.directive_visibility(),
            Directive::Struct(s) => s.directive_visibility(),
            Directive::Trait(t) => t.directive_visibility(),
            Directive::Type(t) => t.directive_visibility(),
            Directive::Use(u) => u.directive_visibility(),
            Directive::Variable(v) => v.directive_visibility(),
        }
    }

    /// Add the content to the directive.
    ///
    /// The content is appended to any existing content.
    fn add_content<I: IntoIterator<Item = String>>(&mut self, content: I) {
        match self {
            Directive::Crate(d) => {
                d.content.push(String::new());
                d.content.extend(content);
                d.content.push(String::new())
            }
            Directive::Enum(d) => {
                d.content.push(String::new());
                d.content.extend(content);
                d.content.push(String::new())
            }
            Directive::Executable(d) => {
                d.0.content.push(String::new());
                d.0.content.extend(content);
                d.0.content.push(String::new())
            }
            Directive::Function(d) => {
                d.content.push(String::new());
                d.content.extend(content);
                d.content.push(String::new())
            }
            Directive::Impl(d) => {
                d.content.push(String::new());
                d.content.extend(content);
                d.content.push(String::new())
            }
            Directive::Macro(d) => {
                d.content.push(String::new());
                d.content.extend(content);
                d.content.push(String::new())
            }
            Directive::Module(d) => {
                d.content.push(String::new());
                d.content.extend(content);
                d.content.push(String::new())
            }
            Directive::Struct(d) => {
                d.content.push(String::new());
                d.content.extend(content);
                d.content.push(String::new())
            }
            Directive::Trait(d) => {
                d.content.push(String::new());
                d.content.extend(content);
                d.content.push(String::new())
            }
            Directive::Type(d) => {
                d.content.push(String::new());
                d.content.extend(content);
                d.content.push(String::new())
            }
            Directive::Use(d) => {
                d.content.push(String::new());
                d.content.extend(content);
                d.content.push(String::new())
            }
            Directive::Variable(d) => {
                d.content.push(String::new());
                d.content.extend(content);
                d.content.push(String::new())
            }
        }
    }

    /// Create the appropriate directive from the provided ``syn::Item``
    ///
    /// Args:
    ///     :parent_path: The parent path of the item.
    ///     :item: The item to parse into a directive.
    ///
    /// Returns:
    ///     An option a :rust:enum:`Directive` variant.
    fn from_item(
        parent_path: &str,
        item: &Item,
        inherited_visibility: &Option<&Visibility>,
    ) -> Option<Directive> {
        match item {
            Item::Const(c) => Some(VariableDirective::from_const(parent_path, c)),
            Item::Enum(e) => Some(EnumDirective::from_item(parent_path, e)),
            Item::ExternCrate(_) => None,
            Item::Fn(f) => Some(FunctionDirective::from_item(parent_path, f)),
            Item::ForeignMod(_) => panic!("ForeignMod items cannot be converted to a single item"),
            Item::Impl(i) => Some(Directive::Impl(ImplDirective::from_item(
                parent_path,
                i,
                inherited_visibility,
            ))),
            Item::Macro(m) => MacroDirective::from_item(parent_path, m),
            Item::Mod(_) => panic!("Module directives must be created with a source code file"),
            Item::Static(s) => Some(VariableDirective::from_static(parent_path, s)),
            Item::Struct(s) => Some(StructDirective::from_item(parent_path, s)),
            Item::Trait(t) => Some(TraitDirective::from_item(parent_path, t)),
            Item::TraitAlias(t) => Some(TraitDirective::from_alias(parent_path, t)),
            Item::Type(t) => Some(TypeDirective::from_item(parent_path, t)),
            Item::Union(u) => Some(StructDirective::from_union(parent_path, u)),
            Item::Use(u) => Some(UseDirective::from_item_as_directive(parent_path, u)),
            Item::Verbatim(_) => None,
            i => panic!("Unexpected item: {:?}", i),
        }
    }

    /// Create the appropriate directive from the provided ``syn::ImplItem``
    ///
    /// Args:
    ///     :parent_path: The path of the impl block which defines the item.
    ///     :item: The impl item to parse into a directive.
    ///
    /// Returns:
    ///     An option a :rust:enum:`Directive` variant.
    fn from_impl_item(
        parent_path: &str,
        item: &ImplItem,
        inherited_visibility: &Option<&Visibility>,
    ) -> Option<Directive> {
        match item {
            ImplItem::Const(c) => Some(VariableDirective::from_impl_const(
                parent_path,
                c,
                inherited_visibility,
            )),
            ImplItem::Fn(f) => Some(FunctionDirective::from_impl_item(
                parent_path,
                f,
                inherited_visibility,
            )),
            ImplItem::Type(t) => Some(TypeDirective::from_impl_item(
                parent_path,
                t,
                inherited_visibility,
            )),
            ImplItem::Macro(_) | ImplItem::Verbatim(_) => None,
            i => panic!("Unexpected impl item: {:?}", i),
        }
    }

    /// Create the appropriate directives from the provided ``syn::ImplItem``
    /// iterator.
    ///
    /// Args:
    ///     :parent_path: The path of the impl block which defines the items.
    ///     :items: The impl items to parse into a directive.
    ///
    /// Returns:
    ///     An vec of :rust:enum:`Directive` variants.
    fn from_impl_items<'a, T: Iterator<Item = &'a ImplItem>>(
        parent_path: &str,
        items: T,
        inherited_visibility: &Option<&Visibility>,
    ) -> Vec<Directive> {
        items
            .filter_map(|i| Self::from_impl_item(parent_path, i, inherited_visibility))
            .collect()
    }

    /// Create the appropriate directive from the provided ``syn::TraitItem``
    ///
    /// Args:
    ///     :parent_path: The path of the trait which defines the items.
    ///     :item: The trait item to parse into a directive.
    ///
    /// Returns:
    ///     An option a :rust:enum:`Directive` variant.
    fn from_trait_item(
        parent_path: &str,
        item: &TraitItem,
        inherited_visibility: &Option<&Visibility>,
    ) -> Option<Directive> {
        match item {
            TraitItem::Const(c) => Some(VariableDirective::from_trait_const(
                parent_path,
                c,
                inherited_visibility,
            )),
            TraitItem::Fn(f) => Some(FunctionDirective::from_trait_item(
                parent_path,
                f,
                inherited_visibility,
            )),
            TraitItem::Type(t) => Some(TypeDirective::from_trait_item(
                parent_path,
                t,
                inherited_visibility,
            )),
            TraitItem::Macro(_) | TraitItem::Verbatim(_) => None,
            i => panic!("Unexpected trait item: {:?}", i),
        }
    }

    /// Create the appropriate directives from the provided ``syn::TraitItem``
    /// iterator.
    ///
    /// Args:
    ///     :parent_path: The path of the module which defines the items.
    ///     :items: The trait items to parse into a directive.
    ///
    /// Returns:
    ///     An vec of :rust:enum:`Directive` variants.
    fn from_trait_items<'a, T: Iterator<Item = &'a TraitItem>>(
        parent_path: &str,
        items: T,
        inherited_visibility: &Option<&Visibility>,
    ) -> Vec<Directive> {
        items
            .filter_map(|i| Self::from_trait_item(parent_path, i, inherited_visibility))
            .collect()
    }

    /// Create the appropriate directive from the provided ``syn::ForeignItem``
    ///
    /// Args:
    ///     :parent_path: The path of the module which defines the items.
    ///     :item: The foreign item to parse into a directive.
    ///
    /// Returns:
    ///     An option a :rust:enum:`Directive` variant.
    fn from_extern_item(parent_path: &str, item: &ForeignItem) -> Option<Directive> {
        match item {
            ForeignItem::Fn(f) => Some(FunctionDirective::from_extern(parent_path, f)),
            ForeignItem::Static(s) => Some(VariableDirective::from_extern_static(parent_path, s)),
            ForeignItem::Type(t) => Some(TypeDirective::from_extern(parent_path, t)),
            _ => None,
        }
    }

    /// Create the appropriate directives from the provided ``syn::ForeignItem``
    /// iterator.
    ///
    /// Args:
    ///     :parent_path: The path of the trait which defines the items.
    ///     :items: The foreign items to parse into a directive.
    ///
    /// Returns:
    ///     An vec of :rust:enum:`Directive` variants.
    fn from_extern_items<'a, T: Iterator<Item = &'a ForeignItem>>(
        parent_path: &str,
        items: T,
    ) -> Vec<Directive> {
        items
            .filter_map(|i| Self::from_extern_item(parent_path, i))
            .collect()
    }
}

impl RstDirective for Directive {
    fn get_rst_text(self, level: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        match self {
            Directive::Crate(c) => c.get_rst_text(level, max_visibility),
            Directive::Enum(e) => e.get_rst_text(level, max_visibility),
            Directive::Executable(e) => e.get_rst_text(level, max_visibility),
            Directive::Function(f) => f.get_rst_text(level, max_visibility),
            Directive::Impl(i) => i.get_rst_text(level, max_visibility),
            Directive::Macro(m) => m.get_rst_text(level, max_visibility),
            Directive::Module(m) => m.get_rst_text(level, max_visibility),
            Directive::Struct(s) => s.get_rst_text(level, max_visibility),
            Directive::Trait(t) => t.get_rst_text(level, max_visibility),
            Directive::Type(t) => t.get_rst_text(level, max_visibility),
            Directive::Use(u) => u.get_rst_text(level, max_visibility),
            Directive::Variable(v) => v.get_rst_text(level, max_visibility),
        }
    }
}

impl MdDirective for Directive {
    fn get_md_text(self, fence_size: usize, max_visibility: &DirectiveVisibility) -> Vec<String> {
        match self {
            Directive::Crate(c) => c.get_md_text(fence_size, max_visibility),
            Directive::Enum(e) => e.get_md_text(fence_size, max_visibility),
            Directive::Executable(e) => e.get_md_text(fence_size, max_visibility),
            Directive::Function(f) => f.get_md_text(fence_size, max_visibility),
            Directive::Impl(i) => i.get_md_text(fence_size, max_visibility),
            Directive::Macro(m) => m.get_md_text(fence_size, max_visibility),
            Directive::Module(m) => m.get_md_text(fence_size, max_visibility),
            Directive::Struct(s) => s.get_md_text(fence_size, max_visibility),
            Directive::Trait(t) => t.get_md_text(fence_size, max_visibility),
            Directive::Type(t) => t.get_md_text(fence_size, max_visibility),
            Directive::Use(u) => u.get_md_text(fence_size, max_visibility),
            Directive::Variable(v) => v.get_md_text(fence_size, max_visibility),
        }
    }

    fn fence_size(&self) -> usize {
        match self {
            Directive::Crate(c) => c.fence_size(),
            Directive::Enum(e) => e.fence_size(),
            Directive::Executable(e) => e.fence_size(),
            Directive::Function(f) => f.fence_size(),
            Directive::Impl(i) => i.fence_size(),
            Directive::Macro(m) => m.fence_size(),
            Directive::Module(m) => m.fence_size(),
            Directive::Struct(s) => s.fence_size(),
            Directive::Trait(t) => t.fence_size(),
            Directive::Type(t) => t.fence_size(),
            Directive::Use(u) => u.fence_size(),
            Directive::Variable(v) => v.fence_size(),
        }
    }
}

/// Extract the docstring from the attrs of an item.
///
/// Args:
///     :attrs: ``syn::attr::Attribute`` vec.
///
/// Returns:
///     A vec of strings, where each string is a line of a documentation
///     comment. If there are no documentation comments, an empty vec is
///     returned.
pub(crate) fn extract_doc_from_attrs(attrs: &Vec<Attribute>) -> Vec<String> {
    let mut content = Vec::new();
    for attr in attrs {
        if attr.path().segments.is_empty() || attr.path().segments[0].ident != "doc" {
            continue;
        }

        if let Expr::Lit(e) = &attr.meta.require_name_value().unwrap().value {
            if let Lit::Str(d) = &e.lit {
                let line = d.value();
                content.push(line.strip_prefix(' ').unwrap_or(&line).to_string());
            }
        }
    }
    content
}

/// Macro to sort and push items within a vec.
macro_rules! push_sorted {
    ($sorted:expr, $items:expr, $name:expr) => {{
        if !$items.is_empty() {
            $items.sort_by(|a, b| a.name().cmp(b.name()));
            $sorted.push(($name, $items));
        }
    }};
}

/// Named type for the output of :rust:fn:`order_items`.
type ItemSections = Vec<(&'static str, Vec<Directive>)>;

/// Order the items for documentation
///
/// The items are ordered using the following rules:
///
/// 1. If the item is a module without content, it is removed and a link to the
///    module is added to the ``toctree``. If there are no such module, the
///    ``toctree`` isn't added.
/// 2. Each directive is then separated by type and ordered alphabetically
///    except for ``impl`` directives.
/// 3. All ``impl`` blocks associated with a struct or enum are ordered after
///    it, starting with the associated ``impl`` block, followed by trait
///    ``impl`` blocks in alphabetical order.
///
/// It uses the :rust:any:`push_sorted!()` macro.
///
/// Returns:
///    A vec of section names with their directives.
fn order_items(items: Vec<Directive>) -> ItemSections {
    let mut enums = vec![];
    let mut fns = vec![];
    let mut impls = vec![];
    let mut macros = vec![];
    let mut structs = vec![];
    let mut traits = vec![];
    let mut types = vec![];
    let mut vars = vec![];

    for item in items {
        match item {
            Directive::Crate(_) => {
                unreachable!("Unexpected crate directive as an item")
            }
            Directive::Enum(e) => enums.push(Directive::Enum(e)),
            Directive::Executable(_) => {
                unreachable!("Unexpected executable directive as an item")
            }
            Directive::Function(f) => fns.push(Directive::Function(f)),
            Directive::Impl(i) => impls.push(Directive::Impl(i)),
            Directive::Macro(m) => macros.push(Directive::Macro(m)),
            Directive::Module(_) => unreachable!("Unexpected module directive as item"),
            Directive::Struct(s) => structs.push(Directive::Struct(s)),
            Directive::Trait(t) => traits.push(Directive::Trait(t)),
            Directive::Type(t) => types.push(Directive::Type(t)),
            Directive::Use(_) => unreachable!("Unexpected use directive as item"),
            Directive::Variable(v) => vars.push(Directive::Variable(v)),
        }
    }

    impls.sort_by(|a, b| a.name().cmp(b.name()));

    let mut sorted = Vec::new();
    push_sorted!(sorted, types, "Types");
    push_sorted!(sorted, vars, "Variables");
    push_sorted!(sorted, macros, "Macros");
    push_sorted!(sorted, fns, "Functions");

    push_sorted!(sorted, traits, "Traits");
    push_sorted!(sorted, enums, "Enums");
    push_sorted!(sorted, structs, "Structs and Unions");
    push_sorted!(sorted, impls, "Impls");

    sorted
}

#[derive(Clone, Debug)]
pub(crate) struct FileDirectives {
    /// The directives for the modules defined in the file.
    pub(crate) modules: Vec<ModuleDirective>,
    /// The directives for the impls defined in the file.
    pub(crate) impls: Vec<ImplDirective>,
    /// The directives for the use statements in the file.
    pub(crate) uses: Vec<UseDirective>,
    /// The directives for all other items in the file.
    /// This will never contain a module, impl or use directive.
    pub(crate) items: Vec<Directive>,
}

impl FileDirectives {
    /// Create new file directives from the AST of a file.
    ///
    /// Args:
    ///     :ast_items: A list of items parsed by syn.
    ///     :module_parent: The parent source code file to find
    ///        modules under.
    fn from_ast_items(ast_items: &Vec<Item>, module_parent: &SourceCodeFile) -> Self {
        let mut modules = vec![];
        let mut impls = vec![];
        let mut uses = vec![
            UseDirective::for_path(&module_parent.item, "self"),
            UseDirective::for_path(module_parent.crate_name(), "crate"),
        ];
        let mut items = vec![];

        for item in ast_items {
            match item {
                Item::Mod(m) => {
                    if let Some(md) = ModuleDirective::from_item(module_parent, m) {
                        modules.push(md);
                    }
                }
                Item::Use(u) => {
                    uses.push(UseDirective::from_item(&module_parent.item, u));
                }
                Item::Impl(i) => {
                    impls.push(ImplDirective::from_item(&module_parent.item, i, &None));
                }
                Item::ForeignMod(f) => {
                    items.extend(Directive::from_extern_items(
                        &module_parent.item,
                        f.items.iter(),
                    ));
                }
                _ => {
                    if let Some(i) = Directive::from_item(&module_parent.item, item, &None) {
                        items.push(i);
                    }
                }
            }
        }

        // Resolve any use paths that are relative to the file.
        for use_ in &mut uses {
            use_.resolve_relative_paths(&modules);
        }

        // Resolve the self_ty and trait_ for the impls.
        // If either self_ty or trait_ is defined in the module itself,
        // they will not resolve. Also, items from the preamble will not
        // resolve. In this case, the resolved names are left as is. It
        // doesn't really matter here since the check for which item owns the
        // impl will only resolve when the name matches entirely.
        for impl_ in &mut impls {
            for use_ in &uses {
                if let Some(path) = use_.find(&impl_.self_ty) {
                    impl_.resolved_self_ty = path.clone();
                }
                else if let Some(trait_) = &impl_.trait_ {
                    if let Some(path) =
                        use_.find(trait_.strip_prefix('!').unwrap_or_else(|| trait_))
                    {
                        impl_.resolved_trait = Some(path.clone());
                    }
                }
            }
        }

        FileDirectives {
            modules,
            impls,
            uses,
            items,
        }
    }

    fn claim_impls(&mut self, parent_name: &str, impls: Vec<ImplDirective>) -> Vec<ImplDirective> {
        let mut remaining = vec![];

        'impl_loop: for impl_ in impls {
            // Check for enums and structs first
            for item in &mut self.items {
                match item {
                    Directive::Enum(e) if impl_.for_item(&e.name) => {
                        e.add_impl(impl_);
                        continue 'impl_loop;
                    }
                    Directive::Struct(s) if impl_.for_item(&s.name) => {
                        s.add_impl(impl_);
                        continue 'impl_loop;
                    }
                    _ => {}
                }
            }
            // Check for trait impls where self_ty is not in crate or a generic.
            for item in &mut self.items {
                match item {
                    Directive::Trait(t) if impl_.for_trait(&t.name, parent_name) => {
                        t.add_impl(impl_);
                        continue 'impl_loop;
                    }
                    _ => {}
                }
            }
            remaining.push(impl_)
        }

        // Recurse into submodules
        for module in &mut self.modules {
            remaining = module.claim_impls(remaining);
        }
        remaining
    }
}
