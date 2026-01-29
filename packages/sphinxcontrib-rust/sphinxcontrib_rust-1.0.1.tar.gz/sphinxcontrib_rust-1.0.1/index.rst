==================
Sphinxcontrib-rust
==================

This is a `Sphinx`_ extension for integrating Rust programming language projects in Sphinx builds. It will work with
existing Rust docstrings with some minor tweaks. See :doc:`docs/compatibility` for writing docstrings compatible with
both rustdoc and this extension. See :doc:`docs/limitations` for known limitations compared to rustdoc.

You can also read this documentation on `Gitlab Pages`_ or `readthedocs`_.

.. _`Gitlab Pages`: https://munir0b0t.gitlab.io/sphinxcontrib-rust
.. _`readthedocs`: https://sphinxcontrib-rust.readthedocs.io/en/latest/

.. contents::
   :backlinks: none
   :local:

Motivation
----------

This is primarily meant for teams and projects that are already using Sphinx as a documentation build tool, and would
like to include documentation for Rust projects in it along with Python, C, and other languages.

Using the extension adds the following functionality:

1. Rust specific :doc:`directives <docs/directives>` and :doc:`roles <docs/roles>` that can be used to define and
   link to Rust items.
2. rustdoc comments may be written in reStructuredText.
3. Various Sphinx features and extensions can be used to generate and publish the docs.

This is not a replacement for `rustdoc`_, and since rustdoc is a part of the Rust language itself, it will not have all
the same features as `rustdoc`_.

The goal is to provide a way for teams and projects using multiple languages to publish a single, consolidated
documentation and use this, along with rustdoc, as part of the documentation workflow.

See :doc:`docs/limitations` for some cases where the tool will not work the same as rustdoc and
:doc:`docs/compatibility` for any tweaks required to make the tool work with existing docstrings.

.. _`usage`:

Installation
------------

There are two components that are required for this to work

1. The ``sphinx-rustdocgen`` Rust crate for extracting the docs.
2. The ``sphinxcontrib_rust`` Python package, which is a Sphinx extension.

Both components are installed when installing the Python package with

.. code-block::

   pip install sphinxcontrib-rust

The installation will check for ``cargo`` in the ``$PATH`` environment variable and will use that to build and install
the Rust executable.

The executable is built with the Rust code shipped with the Python package to ensure that the Rust executable and
Python package are always compatible with each other.

Make sure that the directory where ``cargo`` installs the executable is in ``$PATH`` as well. If the default
installation directory is not part of the ``$PATH`` environment, the installed executable may be specified in the
Sphinx configuration with ``rust_rustdocgen`` option.

If for any reason the crate does not get installed with Python package, it can be installed directly from crates.io
with ``cargo install sphinx-rustdocgen``. Make sure to install the same version of the create as the Python package.

Configuration
-------------

.. _`md usage`:

rustdoc compatible Markdown docstrings
++++++++++++++++++++++++++++++++++++++

This is most probably what you want to do and allows generating Sphinx documentation separately from rustdoc output.

To use the extension along with rustdoc, add the extension to Sphinx's ``conf.py`` file and also add the
`myst-parser`_ extension. Sphinx also needs to be `configured for Markdown builds`_. Use the code snippet below with
your crates specified in ``rust_crates`` to enable all if this.

Using various extensions for myst-parser, existing docstrings can be rendered with Sphinx with minimal changes.
See :doc:`docs/compatibility` for details on how to write docstrings that can work with both rustdoc and Sphinx.

.. code-block:: python

   extensions = ["sphinxcontrib_rust", "myst_parser"]
   source_suffix = {
       ".rst": "restructuredtext",
       ".md": "markdown",
       ".txt": "markdown", # Optional
   }
   # See docs/compatibility for details on these extensions.
   myst_enable_extensions = {
       "attrs_block",
       "colon_fence",
       "html_admonition",
       "replacements",
       "smartquotes",
       "strikethrough",
       "tasklist",
   }
   rust_crates = {
       "my_crate": ".",
       "my_crate_derive": "my-crate-derive",
   }
   rust_doc_dir = "docs/crates/"
   rust_rustdoc_fmt = "md"

This will generate the documentation from your Rust crates and put them in the ``docs/crates/<crate_name>`` directories.
:doc:`docs/including` describes the various ways to integrate the documentation in the Sphinx build. The Rust items
can then be referenced using :doc:`docs/roles` from other docs in the Sphinx build.

See the `configuration options for MyST`_  for other options that are supported by myst-parser. They can be changed
as required to customize the generated docs.

reStructuredText docstrings
+++++++++++++++++++++++++++

Using the extension, it is also possible to write the Rust docstrings in reStructuredText. Note that this makes the
docstrings unusable with Rustdoc and should only be considered when the rustdoc documentation will not be used.
Publishing a crate with such docstrings is still possible, but the documentation on docs.rs for the crate will not be
rendered properly.

To enable RST docstrings, add the extension to the ``conf.py`` file and configure it appropriately.

.. code-block:: python

   extensions = ["sphinxcontrib_rust"]
   rust_crates = {
       "my_crate": ".",
       "my_crate_derive": "my-crate-derive",
   }
   rust_doc_dir = "docs/crates/"
   rust_rustdoc_fmt = "rst"

This will generate the documentation from your Rust crates and put them in the ``docs/crates/<crate_name>`` directories.
You can link against the documentation in your ``toctree`` by specifying the path to ``lib`` file and any executables.
See :doc:`docs/including` for more details. The Rust items can then be referenced using :doc:`docs/roles` from other
docs in the Sphinx build.

Recommendations
+++++++++++++++

* Use a HTML theme that allows expanding the TOC in the sidebar completely. For example, if using ``sphinx_rtd_theme``,
  set the ``navigation_depth`` in ``html_theme_options`` to -1 in the ``conf.py`` file
  (``html_theme_options = {"navigation_depth": -1}``). This makes the sidebar much better to use.
* It is possible to write docstrings in Markdown and other documentation in reStructuredText. The configuration should
  be the same as what is described in :ref:`md usage`. The roles and directives will work the same regardless of the
  choice of the docstrings syntax.

Options
-------

Options are simply Python variables set in the ``conf.py`` file. Most options can be provided as a global value or a
dict of values per crate, with the crate name as the key. The options that are global only are listed separately below.

:rust_crates: (Required) A dict of crate names and their source code directories.
              This must be a dict even for a single crate. It determines which
              crates are documented. The directory should be the one which contains
              the ``Cargo.toml`` file for the crate and each crate in the workspace
              must be listed explicitly.
:rust_doc_dir: (Required) A directory under which to write the docs for all crates,
               or a dict of directory for each crate name. The directories will be
               read by Sphinx during the build, so they must be part of the source
               tree and not under the build directory. The build process will create
               a directory with the crate name under this, even when specified per
               crate.
:rust_rustdoc_fmt: Either ``rst`` or ``md``. (Default: ``rst``)
:rust_visibility: Only includes documentation and indexes for items with visibility greater than or equal to the
                  setting. The value can be ``pub``, ``crate`` or ``pvt``. Visibility restrictions like ``super`` and
                  ``in <path>`` are not supported currently and are treated as private. (Default: ``pub``).
:rust_strip_src: Whether to remove the ``src/`` directory when creating output files or not.
                 The default is ``True``, since that was the initial behavior. So,
                 instead of creating output files as ``<crate_name>/src/<mod_name>.rst``,
                 the output files are created as ``<crate_name>/<mod_name>.rst``, effectively
                 removing ``src/`` from the paths. Set to ``False`` for crates that use a
                 different path. (Default: True)

The below options are global options, and cannot be specified per crate.

:rust_generate_mode: One of ``always``, ``skip`` or ``changed``. If set to
                     ``always``, all documents are regenerated. If set to ``skip``,
                     the docs are not regenerated at all. If set to ``changed``,
                     only docs whose source files have been modified since they
                     were last modified are regenerated. (Default: ``changed``)
:rust_rustdocgen: The path to the ``sphinx-rustdocgen`` executable to use.
                  The path must be an absolute path or relative to Sphinx's
                  working directory. (Default: Obtained from the ``$PATH``
                  environment variable.)

.. _`Sphinx`: https://www.sphinx-doc.org/en/master/index.html
.. _`myst-parser`: https://myst-parser.readthedocs.io/en/latest/index.html
.. _`configured for Markdown builds`: https://www.sphinx-doc.org/en/master/usage/markdown.html
.. _`configuration options for MyST`: https://myst-parser.readthedocs.io/en/latest/configuration.html
.. _`myst-parser syntax`:
   https://myst-parser.readthedocs.io/en/latest/syntax/roles-and-directives.html#roles-an-in-line-extension-point
.. _rustdoc: https://doc.rust-lang.org/rustdoc/index.html

.. _details:

.. toctree::
   :caption: Detailed docs
   :maxdepth: 2
   :glob:

   docs/including
   docs/roles
   docs/directives
   docs/indices
   docs/limitations
   docs/compatibility
   docs/developing
   docs/sphinx-rustdocgen
   docs/sphinx-extension
   CONTRIBUTING
