# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import subprocess
import sys
from datetime import date
from subprocess import PIPE
from typing import Optional

from packaging import version as version_module

# Correct the path to the avatars package
# The actual location is in the src directory
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)  # avatars package is in src directory

from avatars import __version__  # noqa: E402

TAG_PREFIX = "avatars-python-v"

# -- Project information -----------------------------------------------------

project = "avatars"
copyright = f"{date.today().year}, Octopize"
author = "Octopize"
version = __version__  # Sphinx requires 'version' to be a string
release = __version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_multiversion",
    "sphinx.ext.autosummary",
    "sphinxcontrib.autodoc_pydantic",
    "sphinx.ext.viewcode",
]

autodoc_default_options = {
    "exclude-members": "login, get_job, to_common_type",
    # weird, have to add this so that the avatars.client module is documented
    "undoc-members": True,
}
autodoc_typehints_format = "short"
autodoc_member_order = "bysource"

# autodoc_typehints_format is not applied to attributes:
# See https://github.com/sphinx-doc/sphinx/issues/10290
python_use_unqualified_type_names = True

# -- Sphinx Multi-version -------------------------------------------------
# https://autodoc-pydantic.readthedocs.io/en/stable/users/configuration.html
autodoc_pydantic_model_show_json = False
autodoc_pydantic_model_show_config = False
autodoc_pydantic_model_signature_prefix = "class"
autodoc_pydantic_field_doc_policy = "description"
autodoc_pydantic_field_signature_prefix = " "
autodoc_pydantic_model_show_field_summary = False

# -------------------------------------------------------------------------

templates_path = ["_templates"]

# -- Sphinx Multi-version -------------------------------------------------
# https://holzhaus.github.io/sphinx-multiversion/master/configuration.html

# create a version for main and current branch to be able to see layout during development
proc = subprocess.Popen(args=("git", "branch", "--show-current"), stdout=PIPE, text=True)
current_branch, _ = proc.communicate()
smv_branch_whitelist = f"^(main|{current_branch.strip()})$"
# Tags define a release, which are the ones that show up on the sidebar.
# Add the pattern for which you want the releases to appear.
smv_released_pattern = rf"^refs/tags/{TAG_PREFIX}.*$"
smv_tag_whitelist = rf"^{TAG_PREFIX}.*$"
# -------------------------------------------------------------------------

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    # Exclude legacy / merged documentation pages and generated autosummary stubs
    "avatar_yaml.rst",
    "client_and_api.rst",
    "general_approach.rst",
    "_autosummary/*",
]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "furo"
html_static_path = ["_static"]


def modify_class_signature(app, what, name, obj, options, signature, return_annotation):
    """Remove attribute 'client: ApiClient' from modified classnames.

    Using bin/modify_class_names.py, and this method here, we modify
    'avatars.api.Health(client: ApiClient)' into 'avatars.ApiClient.health' to
    be in line with the designed use of the API.
    """

    if signature and "client: ApiClient" in signature:
        signature = "()"

    return (signature, return_annotation)


def autodoc_skip_member(app, what, name, obj, skip, options) -> Optional[bool]:
    # Skip avatars.api.Auth
    if what == "module" and name == "Auth":
        return True
    return None


def sort_versions_semantic(versions_list):
    """Sort version tags semantically using packaging.version.

    This ensures proper ordering like 0.11.0, 0.10.0, 0.9.2, 0.9.1, 0.9.0
    instead of alphabetical ordering like 0.10.0, 0.11.0, 0.7.2, 0.7.3, etc.

    Args:
        versions_list: List of version objects with 'name' and 'url' attributes.
                      The 'name' attribute should contain the full tag name
                      (e.g., 'avatars-python-v1.0.0').

    Returns:
        List sorted by semantic version in descending order (newest first)
    """
    def extract_version(item):
        # Remove the TAG_PREFIX from the version name
        # TAG_PREFIX is defined at module level in this config file
        version_str = item.name.replace(TAG_PREFIX, "")
        try:
            return version_module.parse(version_str)
        except version_module.InvalidVersion:
            # If parsing fails (e.g., invalid version format),
            # return a minimal version so it sorts last
            return version_module.parse("0.0.0")

    return sorted(versions_list, key=extract_version, reverse=True)
def setup(app):
    app.connect("autodoc-process-signature", modify_class_signature)
    app.connect("autodoc-skip-member", autodoc_skip_member)

    # Register custom Jinja2 filter for semantic version sorting
    def add_custom_filters(app):
        app.builder.templates.environment.filters["sort_versions_semantic"] = sort_versions_semantic

    app.connect("builder-inited", add_custom_filters)
