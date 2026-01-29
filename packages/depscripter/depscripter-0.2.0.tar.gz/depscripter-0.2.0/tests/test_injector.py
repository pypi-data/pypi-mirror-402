from depscripter.injector import generate_script_metadata, inject_metadata
import re

def test_generate_metadata():
    deps = {"requests": "2.31.0", "numpy": None}
    metadata = generate_script_metadata(deps, python_requires=">=3.9")
    
    assert "# /// script" in metadata
    assert '# requires-python = ">=3.9"' in metadata
    assert "# dependencies = [" in metadata
    assert '#     "requests==2.31.0",' in metadata
    assert '#     "numpy",' in metadata
    assert "# ///" in metadata

def test_generate_metadata_overrides():
    deps = {"requests": "2.31.0"}
    overrides = {"requests": ">=2.30.0", "extra": ""}
    
    metadata = generate_script_metadata(deps, overrides=overrides)
    
    assert '"requests>=2.30.0"' in metadata
    assert '"requests==2.31.0"' not in metadata
    
    # Extra package added
    assert '"extra"' in metadata

def test_generate_metadata_python_uv_normalization():
    deps = {}
    # Bare version -> >=
    metadata = generate_script_metadata(deps, python_requires="3.8")
    assert 'requires-python = ">=3.8"' in metadata
    
    # Explicit == -> preserved
    metadata = generate_script_metadata(deps, python_requires="==3.12")
    assert 'requires-python = "==3.12"' in metadata
    
    # Explicit >= -> preserved
    metadata = generate_script_metadata(deps, python_requires=">=3.9")
    assert 'requires-python = ">=3.9"' in metadata

def test_inject_replace_existing():
    old_metadata = "# /// script\n# requires-python = \">=3.8\"\n# dependencies = [\n#     \"requests==2.31.0\",\n# ]\n# ///"
    new_metadata = "# /// script\n# requires-python = \">=3.8\"\n# dependencies = [\n#     \"requests==2.32.0\",\n# ]\n# ///"
    code = f"{old_metadata}\nimport requests\nprint('hello')"
    
    result = inject_metadata(code, new_metadata)
    
    assert new_metadata in result
    assert old_metadata not in result
    assert "import requests" in result
    # Ensure it didn't add extra separation newlines if just replacing
    assert result.count("# /// script") == 1

def test_inject_replace_with_shebang():
    shebang = "#!/usr/bin/env python3\n"
    old_metadata = "# /// script\n# requires-python = \">=3.8\"\n# dependencies = [\n#     \"requests==2.31.0\",\n# ]\n# ///\n"
    new_metadata = "# /// script\n# requires-python = \">=3.8\"\n# dependencies = [\n#     \"requests==2.32.0\",\n# ]\n# ///"
    code = f"{shebang}{old_metadata}import requests"
    
    result = inject_metadata(code, new_metadata)
    
    assert result.startswith(shebang)
    assert new_metadata in result
    assert old_metadata not in result
    assert result.count("# /// script") == 1

def test_inject_simple():
    code = "import requests\nprint('hello')"
    metadata = "# /// script\n# ///"
    
    injected = inject_metadata(code, metadata)
    assert injected.startswith("# /// script")
    assert "import requests" in injected
    
def test_inject_preserve_shebang():
    code = "#!/usr/bin/env python3\nimport requests"
    metadata = "# /// script\n# ///"
    
    injected = inject_metadata(code, metadata)
    lines = injected.splitlines()
    assert lines[0] == "#!/usr/bin/env python3"
    assert lines[1] == "# /// script"

def test_inject_preserve_encoding():
    code = "# -*- coding: utf-8 -*-\nimport requests"
    metadata = "# /// script\n# ///"
    
    injected = inject_metadata(code, metadata)
    lines = injected.splitlines()
    assert lines[0].startswith("# -*- coding")
    assert lines[1] == "# /// script"

def test_inject_preserve_shebang_and_encoding():
    code = "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nimport requests"
    metadata = "# /// script\n# ///"
    
    injected = inject_metadata(code, metadata)
    lines = injected.splitlines()
    assert lines[0] == "#!/usr/bin/env python3"
    assert lines[1].startswith("# -*- coding")
    assert lines[2] == "# /// script"
