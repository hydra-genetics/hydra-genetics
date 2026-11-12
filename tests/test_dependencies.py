import ast
import os
import sys
import unittest

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

try:
    import tomllib
except ImportError:  # Python < 3.11, CI runs 3.11
    tomllib = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE = os.path.join(ROOT, "hydra_genetics")
# Jinja sources, not importable Python
TEMPLATES = {os.path.join(PACKAGE, "pipeline-template"), os.path.join(PACKAGE, "rule-template")}

# Import names that differ from the name of the distribution that provides them. pyaml is a wrapper
# that depends on PyYAML, which provides the yaml module.
IMPORT_TO_DISTRIBUTION = {"yaml": "pyaml", "git": "gitpython"}

# Imports that no distribution provides. add_contigs_to_header in utils/io/utils.py imports src.lib.data.files.reference,
# a module that is not in this repository (the function is unused). Remove this when that is cleaned up.
UNRESOLVABLE_IMPORTS = {"src"}


def python_files():
    for directory, subdirectories, files in os.walk(PACKAGE):
        subdirectories[:] = [d for d in subdirectories if os.path.join(directory, d) not in TEMPLATES]
        for file in files:
            if file.endswith(".py"):
                yield os.path.join(directory, file)


def imported_modules(path):
    """Return the top-level names of all modules imported in a file, including imports inside functions"""
    with open(path) as source:
        tree = ast.parse(source.read(), filename=path)
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            modules.add(node.module.split(".")[0])
    return modules


@unittest.skipIf(tomllib is None or not hasattr(sys, "stdlib_module_names"), "needs Python >= 3.11")
class TestDeclaredDependencies(unittest.TestCase):
    def declared_distributions(self):
        with open(os.path.join(ROOT, "pyproject.toml"), "rb") as pyproject:
            dependencies = tomllib.load(pyproject)["project"]["dependencies"]
        return {canonicalize_name(Requirement(dependency).name) for dependency in dependencies}

    def test_all_third_party_imports_are_declared(self):
        declared = self.declared_distributions()
        undeclared = {}
        for path in python_files():
            for module in imported_modules(path):
                if module in sys.stdlib_module_names or module == "hydra_genetics" or module in UNRESOLVABLE_IMPORTS:
                    continue
                distribution = canonicalize_name(IMPORT_TO_DISTRIBUTION.get(module, module))
                if distribution not in declared:
                    undeclared.setdefault(distribution, []).append(os.path.relpath(path, ROOT))
        self.assertEqual(
            undeclared, {},
            "Imported but not listed in [project] dependencies in pyproject.toml "
            "(if the import name differs from the distribution name, add it to IMPORT_TO_DISTRIBUTION)",
        )
