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

//! Module for generating a semi-structured representation of Rust signatures.
//!
//! The module helps with mapping the content of Rust signatures to the
//! appropriate docutils node type.

use std::fmt::Debug;

use quote::ToTokens;
use serde::ser::SerializeMap;
use serde::{Serialize, Serializer};
use syn::punctuated::Punctuated;
use syn::{
    Abi,
    AngleBracketedGenericArguments,
    BoundLifetimes,
    Expr,
    ExprLit,
    GenericArgument,
    GenericParam,
    Generics,
    LifetimeParam,
    ParenthesizedGenericArguments,
    Pat,
    PatType,
    Path,
    PathArguments,
    PathSegment,
    ReturnType,
    Token,
    TraitBoundModifier,
    Type,
    TypeBareFn,
    TypeParam,
    TypeParamBound,
    TypePath,
    WhereClause,
    WherePredicate,
};

/// Enum representing various docutils nodes for item signatures
#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) enum Node {
    /// The node for a name in the signature.
    Name(String),
    /// A node for link to another item in the signature.
    Link { value: String, target: String },
    /// A node for a keyword in the signature.
    Keyword(&'static str),
    /// A node for a punctuation in the signature.
    Punctuation(&'static str),
    /// A node for a single space in the signature.
    Space,
    /// A node for a newline in the signature.
    Newline,
    /// A node for adding an indentation before the line.
    Indent,
    /// A node for an operator in the signature.
    Operator(&'static str),
    /// A node for the returns symbol.
    Returns,
    /// A literal string to include in the signature.
    Literal(String),
    /// A node for a lifetime name. This is not a docutils node, but kept
    /// separate for easier identification.
    Lifetime(String),
}

impl Serialize for Node {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        match self {
            Node::Name(n) => {
                let mut map = serializer.serialize_map(Some(2))?;
                map.serialize_entry("type", "name")?;
                map.serialize_entry("value", n)?;
                map.end()
            }
            Node::Link {
                value,
                target,
            } => {
                let mut map = serializer.serialize_map(Some(3))?;
                map.serialize_entry("type", "link")?;
                map.serialize_entry("value", value)?;
                map.serialize_entry("target", target)?;
                map.end()
            }
            Node::Keyword(k) => {
                let mut map = serializer.serialize_map(Some(2))?;
                map.serialize_entry("type", "keyword")?;
                map.serialize_entry("value", k)?;
                map.end()
            }
            Node::Punctuation(p) => {
                let mut map = serializer.serialize_map(Some(2))?;
                map.serialize_entry("type", "punctuation")?;
                map.serialize_entry("value", p)?;
                map.end()
            }
            Node::Space => {
                let mut map = serializer.serialize_map(Some(1))?;
                map.serialize_entry("type", "space")?;
                map.end()
            }
            Node::Newline => {
                let mut map = serializer.serialize_map(Some(1))?;
                map.serialize_entry("type", "newline")?;
                map.end()
            }
            Node::Indent => {
                let mut map = serializer.serialize_map(Some(1))?;
                map.serialize_entry("type", "indent")?;
                map.end()
            }
            Node::Operator(o) => {
                let mut map = serializer.serialize_map(Some(2))?;
                map.serialize_entry("type", "operator")?;
                map.serialize_entry("value", o)?;
                map.end()
            }
            Node::Returns => {
                let mut map = serializer.serialize_map(Some(1))?;
                map.serialize_entry("type", "returns")?;
                map.end()
            }
            Node::Literal(l) => {
                let mut map = serializer.serialize_map(Some(2))?;
                map.serialize_entry("type", "literal")?;
                map.serialize_entry("value", l)?;
                map.end()
            }
            Node::Lifetime(lt) => {
                let mut map = serializer.serialize_map(Some(2))?;
                map.serialize_entry("type", "lifetime")?;
                map.serialize_entry("value", lt)?;
                map.end()
            }
        }
    }
}

/// Get simple name for a type parameter bound.
///
/// The simple name is the name without any generic arguments.
fn type_param_bound_name(type_param_bound: &TypeParamBound) -> String {
    match type_param_bound {
        TypeParamBound::Trait(t) => t.path.segments.last().map(|s| s.ident.to_string()).unwrap(),
        TypeParamBound::Lifetime(l) => l.to_string(),
        TypeParamBound::Verbatim(_) => panic!("Cannot determine name for verbatim type"),
        x => {
            panic!("Unsupported bound type {:?}", x)
        }
    }
}

/// Get simple name for a type path.
///
/// The simple name is essentially the path created from the identifiers of
/// each segment of the type path.
fn type_path_name(type_path: &TypePath) -> String {
    type_path
        .path
        .segments
        .iter()
        .map(|s| s.ident.to_string())
        .collect::<Vec<String>>()
        .join("::")
}

/// Get simple name for a type.
///
/// The simple name is the name without any generic arguments.
pub(crate) fn type_name(ty: &Type) -> String {
    match ty {
        Type::Array(a) => format!("[{}; ?]", type_name(&a.elem)),
        Type::BareFn(f) => format!(
            "fn ({}){}",
            f.inputs
                .iter()
                .map(|i| type_name(&i.ty))
                .collect::<Vec<String>>()
                .join(", "),
            match &f.output {
                ReturnType::Type(_, r_ty) => {
                    format!(" -> {}", type_name(r_ty))
                }
                _ => String::new(),
            }
        ),
        Type::Group(g) => type_name(&g.elem),
        Type::ImplTrait(t) => format!(
            "impl {}",
            t.bounds
                .iter()
                .map(type_param_bound_name)
                .collect::<Vec<String>>()
                .join(" + ")
        ),
        Type::Infer(_) | Type::Macro(_) => "_".into(),
        Type::Never(_) => "!".into(),
        Type::Paren(p) => format!("({})", type_name(&p.elem)),
        Type::Path(p) => type_path_name(p),
        Type::Ptr(p) => format!("*{}", type_name(&p.elem)),
        Type::Reference(r) => format!("&{}", type_name(&r.elem)),
        Type::Slice(s) => format!("[{}]", type_name(&s.elem)),
        Type::TraitObject(t) => format!(
            "dyn {}",
            t.bounds
                .iter()
                .map(type_param_bound_name)
                .collect::<Vec<String>>()
                .join(" + ")
        ),
        Type::Tuple(t) => format!(
            "({})",
            t.elems
                .iter()
                .map(type_name)
                .collect::<Vec<String>>()
                .join(", ")
        ),
        Type::Verbatim(_) => panic!("Cannot determine name for verbatim type"),
        x => panic!("Unsupported type category {:?}", x),
    }
}

/// Create nodes for a literal expression.
fn nodes_for_expr_lit(expr_lit: &ExprLit) -> Vec<Node> {
    // TODO: Better handling for expressions. Not sure if required.
    // If this implemented for all expr variants, update the Const and
    // AssocConst branches below.
    vec![Node::Literal(expr_lit.lit.to_token_stream().to_string())]
}

/// Create nodes for a generic argument.
fn nodes_for_generic_argument(generic_arg: &GenericArgument) -> Vec<Node> {
    let mut nodes = vec![];
    match generic_arg {
        GenericArgument::Lifetime(lt) => nodes.push(Node::Lifetime(lt.to_string())),
        GenericArgument::Type(t) => nodes.extend(nodes_for_type(t)),
        GenericArgument::Const(_) => {
            // XXX: Can't really do much here since the expr would have to be evaluated
            // with compiler context, and that is way beyond the scope of the project.
            nodes.push(Node::Keyword("<const arg>"));
        }
        GenericArgument::AssocType(at) => {
            nodes.push(Node::Name(at.ident.to_string()));
            if let Some(ab) = &at.generics {
                nodes.extend(nodes_for_angle_bracket_generic_args(ab));
            }
            nodes.push(Node::Punctuation(" = "));
            nodes.extend(nodes_for_type(&at.ty));
        }
        GenericArgument::AssocConst(ac) => {
            nodes.push(Node::Name(ac.ident.to_string()));
            if let Some(ab) = &ac.generics {
                nodes.extend(nodes_for_angle_bracket_generic_args(ab));
            }
            // Same issue as with const. The expr has to be evaluated to get the actual type
            nodes.push(Node::Punctuation(" = "));
            nodes.push(Node::Keyword("<default>"));
        }
        GenericArgument::Constraint(c) => {
            nodes.push(Node::Name(c.ident.to_string()));
            if let Some(ab) = &c.generics {
                nodes.extend(nodes_for_angle_bracket_generic_args(ab));
            }
            nodes.push(Node::Punctuation(": "));
            nodes.extend(nodes_for_type_param_bounds(&c.bounds));
        }
        x => panic!("Unknown generic argument type {:?}", x),
    }
    nodes
}

/// Create nodes for angle bracket generic arguments in paths.
fn nodes_for_angle_bracket_generic_args(angled_args: &AngleBracketedGenericArguments) -> Vec<Node> {
    let mut nodes = vec![];
    if angled_args.colon2_token.is_some() {
        nodes.push(Node::Punctuation("::"));
    }
    nodes.push(Node::Punctuation("<"));
    for arg in &angled_args.args {
        nodes.extend(nodes_for_generic_argument(arg));
        nodes.push(Node::Punctuation(", "));
    }

    nodes.pop();
    nodes.push(Node::Punctuation(">"));
    nodes
}

/// Create nodes for parenthesized generic arguments in paths.
fn nodes_for_parenthesized_generic_args(paren_args: &ParenthesizedGenericArguments) -> Vec<Node> {
    let mut nodes = vec![Node::Punctuation("(")];
    for ty in &paren_args.inputs {
        nodes.extend(nodes_for_type(ty));
        nodes.push(Node::Punctuation(", "));
    }
    nodes.pop();
    nodes.push(Node::Punctuation(")"));
    nodes.extend(nodes_for_return_type(&paren_args.output));
    nodes
}

/// Create nodes for a path segment.
fn nodes_for_path_segment(segment: &PathSegment, make_link: bool) -> Vec<Node> {
    let mut nodes = if make_link {
        vec![Node::Link {
            value: segment.ident.to_string(),
            target: segment.ident.to_string(),
        }]
    }
    else {
        vec![Node::Name(segment.ident.to_string())]
    };
    match &segment.arguments {
        PathArguments::None => {}
        PathArguments::AngleBracketed(ab) => {
            nodes.extend(nodes_for_angle_bracket_generic_args(ab));
        }
        PathArguments::Parenthesized(p) => {
            nodes.extend(nodes_for_parenthesized_generic_args(p));
        }
    }
    nodes
}

/// Create nodes for a path.
pub(crate) fn nodes_for_path(path: &Path) -> Vec<Node> {
    let mut nodes = vec![];
    if path.leading_colon.is_some() {
        nodes.push(Node::Punctuation("::"));
    }
    for (idx, segment) in path.segments.iter().enumerate() {
        nodes.extend(nodes_for_path_segment(segment, idx == 0));
        nodes.push(Node::Punctuation("::"));
    }
    nodes.pop();
    nodes
}

/// Create nodes for an optional ABI specification.
pub(crate) fn nodes_for_abi_opt(abi: &Option<Abi>) -> Vec<Node> {
    abi.as_ref()
        .map(|abi| {
            let mut nodes = vec![Node::Keyword("extern"), Node::Space];
            if let Some(s) = &abi.name {
                nodes.extend_from_slice(&[Node::Literal(s.value()), Node::Space]);
            }
            nodes
        })
        .unwrap_or_default()
}

/// Create nodes for a type specification.
pub(crate) fn nodes_for_type(ty: &Type) -> Vec<Node> {
    let mut nodes = vec![];
    match ty {
        Type::Array(a) => {
            nodes.push(Node::Punctuation("["));
            nodes.extend(nodes_for_type(&a.elem));
            nodes.push(Node::Punctuation("; "));

            // XXX: Array len is an expression that has to be evaluated.
            // In some cases, it may be a simple constant, but it can also be a variable,
            // and its value can't be determined simply from the AST.
            if let Expr::Lit(l) = &a.len {
                nodes.extend(nodes_for_expr_lit(l));
            }
            else {
                nodes.push(Node::Punctuation("?"))
            }

            nodes.push(Node::Punctuation("]"));
        }
        Type::BareFn(bf) => {
            nodes.extend(nodes_for_bare_fn(bf));
        }
        Type::Group(_) => {} // Unsure if this needs to be supported
        Type::ImplTrait(i) => {
            nodes.push(Node::Keyword("impl"));
            nodes.push(Node::Space);
            nodes.extend(nodes_for_type_param_bounds(&i.bounds));
        }
        Type::Infer(_) => {
            nodes.push(Node::Punctuation("_"));
        }
        Type::Macro(_) => {
            nodes.push(Node::Punctuation("?"));
        }
        Type::Never(_) => {
            nodes.push(Node::Punctuation("!"));
        }
        Type::Paren(p) => {
            nodes.push(Node::Punctuation("("));
            nodes.extend(nodes_for_type(&p.elem));
            nodes.push(Node::Punctuation(")"));
        }
        Type::Path(p) => {
            // TODO: Figure out whether supporting QSelf if necessary or not
            // TODO: Check whether path needs to be link or not based on its name.
            nodes.extend(nodes_for_path(&p.path));
        }
        Type::Ptr(p) => {
            nodes.push(Node::Operator("*"));
            if p.const_token.is_some() {
                nodes.push(Node::Keyword("const"));
                nodes.push(Node::Space);
            }
            if p.mutability.is_some() {
                nodes.push(Node::Keyword("mut"));
                nodes.push(Node::Space);
            }
            nodes.extend(nodes_for_type(&p.elem));
        }
        Type::Reference(r) => {
            nodes.push(Node::Punctuation("&"));
            if let Some(lt) = &r.lifetime {
                nodes.push(Node::Lifetime(lt.to_string()));
                nodes.push(Node::Space);
            }
            if r.mutability.is_some() {
                nodes.push(Node::Keyword("mut"));
                nodes.push(Node::Space);
            }
            nodes.extend(nodes_for_type(&r.elem));
        }
        Type::Slice(s) => {
            nodes.push(Node::Punctuation("["));
            nodes.extend(nodes_for_type(&s.elem));
            nodes.push(Node::Punctuation("]"));
        }
        Type::TraitObject(t) => {
            nodes.push(Node::Keyword("dyn"));
            nodes.push(Node::Space);
            nodes.extend(nodes_for_type_param_bounds(&t.bounds));
        }
        Type::Tuple(t) => {
            nodes.push(Node::Punctuation("("));
            for elem in &t.elems {
                nodes.extend(nodes_for_type(elem));
                nodes.push(Node::Punctuation(", "));
            }
            if !t.elems.is_empty() {
                nodes.pop();
            }
            nodes.push(Node::Punctuation(")"));
        }
        Type::Verbatim(_) => {}
        x => panic!("Unsupported type category {:?}", x),
    }

    nodes
}

/// Create nodes for a lifetime parameter.
fn nodes_for_lifetime_param(lifetime_param: &LifetimeParam) -> Vec<Node> {
    let mut nodes = vec![Node::Lifetime(lifetime_param.lifetime.to_string())];
    if lifetime_param.colon_token.is_some() {
        nodes.push(Node::Punctuation(": "));
        for bound in &lifetime_param.bounds {
            nodes.push(Node::Lifetime(bound.to_string()));
            nodes.push(Node::Punctuation(" + "));
        }
        nodes.pop();
    }

    nodes
}

/// Create nodes for bound lifetimes.
fn nodes_for_bound_lifetimes(bound_lts: &BoundLifetimes) -> Vec<Node> {
    let mut nodes = vec![];
    nodes.extend_from_slice(&[Node::Keyword("for"), Node::Punctuation("<")]);
    for lt in &bound_lts.lifetimes {
        nodes.extend(nodes_for_generic_param(lt));
        nodes.push(Node::Punctuation(", "));
    }
    nodes.pop();
    nodes.extend_from_slice(&[Node::Punctuation(">"), Node::Space]);
    nodes
}

/// Create nodes for a type parameter binding.
fn nodes_for_type_param_bound(type_param_bound: &TypeParamBound) -> Vec<Node> {
    let mut nodes = vec![];
    match type_param_bound {
        TypeParamBound::Trait(t) => {
            if t.paren_token.is_some() {
                nodes.push(Node::Punctuation("("));
            }
            if matches!(t.modifier, TraitBoundModifier::Maybe(_)) {
                nodes.push(Node::Punctuation("?"));
            }
            if let Some(blt) = &t.lifetimes {
                nodes.extend(nodes_for_bound_lifetimes(blt));
            }
            nodes.extend(nodes_for_path(&t.path));
            if t.paren_token.is_some() {
                nodes.push(Node::Punctuation(")"));
            }
        }
        TypeParamBound::Lifetime(lt) => {
            nodes.push(Node::Lifetime(lt.to_string()));
        }
        TypeParamBound::Verbatim(_) => {}
        x => {
            panic!("Unsupported bound type {:?}", x)
        }
    }

    nodes
}

/// Create nodes for all type parameters in a binding.
fn nodes_for_type_param_bounds(
    type_param_bounds: &Punctuated<TypeParamBound, Token![+]>,
) -> Vec<Node> {
    let mut nodes = vec![];
    for bound in type_param_bounds {
        nodes.extend(nodes_for_type_param_bound(bound));
        nodes.push(Node::Punctuation(" + "))
    }
    nodes.pop();
    nodes
}

/// Create nodes for a type parameter, along with its bounds.
fn nodes_for_type_param(type_param: &TypeParam) -> Vec<Node> {
    let mut nodes = vec![Node::Name(type_param.ident.to_string())];
    if type_param.colon_token.is_some() {
        nodes.push(Node::Punctuation(": "));
        nodes.extend(nodes_for_type_param_bounds(&type_param.bounds));
    }

    nodes
}

/// Create nodes for a generic parameter, along with its bounds.
fn nodes_for_generic_param(generic_param: &GenericParam) -> Vec<Node> {
    match generic_param {
        GenericParam::Lifetime(lt) => nodes_for_lifetime_param(lt),
        GenericParam::Type(ty) => nodes_for_type_param(ty),
        GenericParam::Const(c) => {
            let mut nodes = vec![
                Node::Keyword("const"),
                Node::Space,
                Node::Name(c.ident.to_string()),
                Node::Punctuation(": "),
            ];
            nodes.extend(nodes_for_type(&c.ty));

            nodes
        }
    }
}

/// Create nodes for generics declared for an item.
///
/// The function does not create nodes for the where clause of the generics.
/// Use :rust:fn:`nodes_for_where_clause` to generate nodes for it.
pub(crate) fn nodes_for_generics(generics: &Generics) -> Vec<Node> {
    if generics.params.is_empty() {
        return vec![];
    }

    let mut nodes = vec![Node::Punctuation("<")];

    for generic in &generics.params {
        nodes.extend(nodes_for_generic_param(generic));
        nodes.push(Node::Punctuation(", "));
    }

    // Remove last ", " and add the closing >
    nodes.pop();
    nodes.push(Node::Punctuation(">"));

    nodes
}

/// Create nodes for the where clause of generics for an item.
///
/// The created nodes will insert a newline node as the first node, and
/// between each predicate.
pub(crate) fn nodes_for_where_clause(where_clause: &WhereClause) -> Vec<Node> {
    let mut nodes = vec![Node::Newline, Node::Keyword("where")];
    for predicate in &where_clause.predicates {
        nodes.extend_from_slice(&[Node::Newline, Node::Indent]);
        match predicate {
            WherePredicate::Lifetime(lt) => {
                nodes.extend_from_slice(&[
                    Node::Lifetime(lt.lifetime.to_string()),
                    Node::Punctuation(": "),
                ]);
                for bound in &lt.bounds {
                    nodes.extend_from_slice(&[
                        Node::Lifetime(bound.to_string()),
                        Node::Punctuation(" + "),
                    ]);
                }
                nodes.pop();
            }
            WherePredicate::Type(ty) => {
                if let Some(blt) = &ty.lifetimes {
                    nodes.extend(nodes_for_bound_lifetimes(blt));
                }
                nodes.extend(nodes_for_type(&ty.bounded_ty));
                nodes.push(Node::Punctuation(": "));
                nodes.extend(nodes_for_type_param_bounds(&ty.bounds));
            }
            x => {
                panic!("Unknown where predicate type {:?}", x)
            }
        }
        nodes.push(Node::Punctuation(","))
    }
    nodes.pop();

    nodes
}

/// Create nodes for a type pattern binding.
pub(crate) fn nodes_for_pat_type(pat_type: &PatType) -> Vec<Node> {
    let mut nodes = vec![];
    nodes.extend(nodes_for_pat(&pat_type.pat));
    nodes.push(Node::Punctuation(": "));
    nodes.extend(nodes_for_type(&pat_type.ty));
    nodes
}

/// Create nodes for a pattern binding.
fn nodes_for_pat(pat: &Pat) -> Vec<Node> {
    let mut nodes = vec![];
    match pat {
        Pat::Const(_) => {
            nodes.push(Node::Keyword("<const block>"));
        }
        Pat::Ident(i) => {
            if i.by_ref.is_some() {
                nodes.push(Node::Keyword("ref"));
                nodes.push(Node::Space);
            }
            if i.mutability.is_some() {
                nodes.push(Node::Keyword("mut"));
                nodes.push(Node::Space);
            }
            nodes.push(Node::Name(i.ident.to_string()));
        }
        Pat::Lit(l) => nodes.extend(nodes_for_expr_lit(l)),
        Pat::Macro(_) => nodes.push(Node::Literal("macro".into())),
        Pat::Or(o) => {
            if o.leading_vert.is_some() {
                nodes.push(Node::Operator("| "));
            }
            for case in &o.cases {
                nodes.extend(nodes_for_pat(case));
                nodes.push(Node::Operator(" | "));
            }
            nodes.pop();
        }
        Pat::Paren(p) => {
            nodes.push(Node::Punctuation("("));
            nodes.extend(nodes_for_pat(&p.pat));
            nodes.push(Node::Punctuation(")"));
        }
        Pat::Path(p) => {
            // TODO: Figure out whether supporting QSelf if necessary or not
            nodes.extend(nodes_for_path(&p.path))
        }
        Pat::Range(_) => {
            nodes.push(Node::Literal("range".into()));
        }
        Pat::Reference(r) => {
            nodes.push(Node::Punctuation("&"));
            if r.mutability.is_some() {
                nodes.push(Node::Keyword("mut"));
            }
            nodes.push(Node::Space);
            nodes.extend(nodes_for_pat(&r.pat))
        }
        Pat::Rest(_) => {
            nodes.push(Node::Operator(".."));
        }
        Pat::Slice(s) => {
            nodes.push(Node::Punctuation("["));
            for pat in &s.elems {
                nodes.extend(nodes_for_pat(pat));
                nodes.push(Node::Punctuation(", "));
            }
            nodes.pop();
            nodes.push(Node::Punctuation("]"));
        }
        Pat::Struct(s) => {
            // TODO: Figure out whether supporting QSelf if necessary or not
            // TODO: Figure out whether listing fields is necessary or not
            nodes.extend(nodes_for_path(&s.path));
            nodes.push(Node::Space);
            nodes.push(Node::Punctuation("{..}"));
        }
        Pat::Tuple(t) => {
            nodes.push(Node::Punctuation("("));
            for pat in &t.elems {
                nodes.extend(nodes_for_pat(pat));
                nodes.push(Node::Punctuation(", "));
            }
            nodes.pop();
            nodes.push(Node::Punctuation(")"));
        }
        Pat::TupleStruct(ts) => {
            // TODO: Figure out whether supporting QSelf if necessary or not
            nodes.extend(nodes_for_path(&ts.path));
            nodes.push(Node::Punctuation("("));
            for pat in &ts.elems {
                nodes.extend(nodes_for_pat(pat));
                nodes.push(Node::Punctuation(", "));
            }
            nodes.pop();
            nodes.push(Node::Punctuation(")"));
        }
        Pat::Type(t) => {
            nodes.extend(nodes_for_pat_type(t));
        }
        Pat::Verbatim(_) => {}
        Pat::Wild(_) => {
            nodes.push(Node::Punctuation("_"));
        }
        x => panic!("Unsupported pattern type {:?} in fn inputs", x),
    }
    nodes
}

/// Create nodes for the return type of function.
pub(crate) fn nodes_for_return_type(return_type: &ReturnType) -> Vec<Node> {
    let mut nodes = vec![];
    if let ReturnType::Type(_, ty) = return_type {
        nodes.extend_from_slice(&[Node::Space, Node::Returns, Node::Space]);
        nodes.extend(nodes_for_type(ty));
    }

    nodes
}

/// Create nodes for a bare fn type.
pub(crate) fn nodes_for_bare_fn(bare_fn: &TypeBareFn) -> Vec<Node> {
    let mut nodes = Vec::new();
    if bare_fn.unsafety.is_some() {
        nodes.push(Node::Keyword("unsafe"));
        nodes.push(Node::Space);
    }
    nodes.extend(nodes_for_abi_opt(&bare_fn.abi));
    nodes.push(Node::Keyword("fn"));
    nodes.push(Node::Space);

    // Nodes for arguments
    nodes.push(Node::Punctuation("("));
    for arg in &bare_fn.inputs {
        nodes.extend(nodes_for_type(&arg.ty));
        nodes.push(Node::Punctuation(", "));
    }

    // If variadic, add the "..." otherwise remove the last ", ".
    if bare_fn.variadic.is_some() {
        nodes.push(Node::Punctuation("..."));
    }
    else if !bare_fn.inputs.is_empty() {
        nodes.pop();
    }
    // Closing parenthesis
    nodes.push(Node::Punctuation(")"));

    // Return type
    nodes.extend(nodes_for_return_type(&bare_fn.output));

    nodes
}
