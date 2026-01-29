from depscripter.scanner import scan_imports

def test_scan_simple_import():
    code = "import os\nimport requests"
    assert scan_imports(code) == {"os", "requests"}

def test_scan_from_import():
    code = "from collections import defaultdict\nfrom numpy import array"
    assert scan_imports(code) == {"collections", "numpy"}

def test_scan_import_as_alias():
    code = "import pandas as pd"
    assert scan_imports(code) == {"pandas"}

def test_scan_dotted_import():
    code = "import google.auth"
    assert scan_imports(code) == {"google"}

def test_scan_from_dotted_import():
    code = "from google.cloud import storage"
    assert scan_imports(code) == {"google"}

def test_ignore_relative_import():
    code = "from . import module"
    assert scan_imports(code) == set()

def test_ignore_deep_relative_import():
    code = "from ..sub import module"
    assert scan_imports(code) == set()
