# docs/conf.py -- robust Sphinx config for PepKit
from __future__ import annotations

import os
import warnings
from datetime import datetime
from typing import List

# ---------------------------------------------------------------------------
# Project info
# ---------------------------------------------------------------------------
project = "pepkit"
author = "Vivi-Tran"
copyright = f"{datetime.now().year}, {author}"

# ---------------------------------------------------------------------------
# Base extensions (always present)
# ---------------------------------------------------------------------------
extensions: List[str] = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

# ---------------------------------------------------------------------------
# Optional extensions (enable only if importable)
# ---------------------------------------------------------------------------
# For each optional extension we attempt an import; if it succeeds we add the
# extension name and set minimal required configuration for it.
_optional_exts = [
    ("sphinxcontrib.bibtex", "sphinxcontrib.bibtex"),
    ("sphinx_copybutton", "sphinx_copybutton"),
]

for import_name, ext_name in _optional_exts:
    try:
        __import__(import_name)  # type: ignore
    except Exception:
        # missing optional extension -> skip quietly
        pass
    else:
        extensions.append(ext_name)

# ---------------------------------------------------------------------------
# Required settings for optional extensions (avoid ExtensionError)
# ---------------------------------------------------------------------------
# If bibtex extension enabled, ensure bibtex_bibfiles is defined.
if "sphinxcontrib.bibtex" in extensions:
    # Default file(s) used by the docs build. Change this if you use a different path.
    bibtex_bibfiles = ["refs.bib"]

    # Warn (but don't raise) if the file(s) do not exist so the user can fix it.
    missing = [
        p
        for p in bibtex_bibfiles
        if not os.path.exists(os.path.join(os.path.dirname(__file__), p))
    ]
    if missing:
        warnings.warn(
            "sphinxcontrib.bibtex is enabled but the bib file(s) were not found: "
            f"{missing!r}. Create the file(s) or update `bibtex_bibfiles` in conf.py."
        )

# ---------------------------------------------------------------------------
# Templates / general Sphinx settings
# ---------------------------------------------------------------------------
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
autosectionlabel_prefix_document = True
default_role = "literal"

# ---------------------------------------------------------------------------
# Autodoc / Napoleon settings
# ---------------------------------------------------------------------------
autosummary_generate = True
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "private-members": False,
    "show-inheritance": True,
}
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_use_param = True
napoleon_use_rtype = True

# ---------------------------------------------------------------------------
# Intersphinx (normalized / safe default)
# ---------------------------------------------------------------------------
# Provide a valid default mapping. You can edit this block to add more.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    # "numpy": ("https://numpy.org/doc/stable", None),
    # "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
}

# ---------------------------------------------------------------------------
# HTML output options
# ---------------------------------------------------------------------------
try:
    import sphinx_rtd_theme  # noqa: F401
except Exception:
    html_theme = "alabaster"
    html_theme_options = {}
else:
    html_theme = "sphinx_rtd_theme"
    html_theme_options = {
        "collapse_navigation": False,
        "navigation_depth": 3,
        "sticky_navigation": True,
        "includehidden": True,
        "titles_only": False,
    }

html_static_path = ["_static"]
html_title = "PepKit Documentation"
html_show_sourcelink = True
html_css_files = ["custom.css"]

# ---------------------------------------------------------------------------
# Final niceties
# ---------------------------------------------------------------------------
nitpicky = False
