import sys
import subprocess
import pytest
from pathlib import Path

def run_depscripter(args, cwd=None):
    """Result of running depscripter with given args."""
    cmd = [sys.executable, "-m", "depscripter"] + args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)

def test_integration_pytest(tmp_path):
    """
    Test checking a script that imports pytest (which is definitely installed).
    """
    script = tmp_path / "test_script.py"
    script.write_text("import pytest\nprint(pytest.__version__)", encoding="utf-8")
    
    result = run_depscripter([str(script)])
    
    assert result.returncode == 0
    output = result.stdout
    
    # Check for metadata block
    assert "# /// script" in output
    assert "pytest" in output
    # Since we are in an environment with pytest installed, it should pin it.
    # We can't know exact version easily without checking, but it should be pinned.
    assert "pytest==" in output

def test_integration_stdlib_only(tmp_path):
    """
    Test a script with only stdlib imports. Should have empty dependencies.
    """
    script = tmp_path / "stdlib_script.py"
    script.write_text("import os\nimport sys\nimport re", encoding="utf-8")
    
    result = run_depscripter([str(script)])
    
    assert result.returncode == 0
    output = result.stdout
    
    assert "# /// script" in output
    assert "# dependencies = [" in output
    # Should be empty list or just close bracket
    # The current implementation iterates over dependencies. If empty, it just ensures the block exists?
    # Actually my injector implementation wraps dependency generation. 
    # generate_script_metadata iterates `dependencies`. If empty, it just prints `# ]`.
    assert "# ]" in output
    # verify no external packages listed
    # How to check that?
    # "os" and "sys" should not appear in dependencies list
    assert '"os"' not in output
    assert '"sys"' not in output

def test_integration_in_place(tmp_path):
    """
    Test --in-place modification.
    """
    script = tmp_path / "modify_me.py"
    script.write_text("import pytest", encoding="utf-8")
    
    result = run_depscripter([str(script), "--in-place"])
    assert result.returncode == 0
    
    content = script.read_text(encoding="utf-8")
    assert "# /// script" in content
    assert "pytest==" in content

def test_integration_no_pin(tmp_path):
    """
    Test --no-pin option.
    """
    script = tmp_path / "no_pin.py"
    script.write_text("import pytest", encoding="utf-8")
    
    result = run_depscripter([str(script), "--no-pin"])
    assert result.returncode == 0
    
    output = result.stdout
    assert '"pytest",' in output  # format is "pkg",
    assert "pytest==" not in output

def test_integration_output_option(tmp_path):
    """
    Test --output option.
    """
    script = tmp_path / "output_test_in.py"
    script.write_text("import pytest", encoding="utf-8")
    outfile = tmp_path / "output_test_out.py"
    
    result = run_depscripter([str(script), "-o", str(outfile)])
    assert result.returncode == 0
    
    assert outfile.exists()
    content = outfile.read_text(encoding="utf-8")
    assert "# /// script" in content
    assert "pytest==" in content
    # check original unchaged
    assert script.read_text(encoding="utf-8") == "import pytest"
