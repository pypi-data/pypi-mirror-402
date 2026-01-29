import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest
from depscripter.cli import main

def test_cli_file_not_found(tmp_path):
    with patch("sys.argv", ["depscripter", str(tmp_path / "missing.py")]):
        with pytest.raises(SystemExit):
            main()

def test_cli_successful_run(tmp_path, capsys):
    f = tmp_path / "script.py"
    f.write_text("import requests", encoding="utf-8")
    
    with patch("sys.argv", ["depscripter", str(f), "--no-pin"]):
        with patch("depscripter.cli.scan_imports", return_value={"requests"}), \
             patch("depscripter.cli.resolve_packages", return_value={"requests": None}), \
             patch("depscripter.cli.generate_script_metadata", return_value="# /// metadata"), \
             patch("depscripter.cli.inject_metadata", return_value="# /// metadata\nimport requests"):
             
             main()
             
    captured = capsys.readouterr()
    assert "# /// metadata" in captured.out

def test_cli_in_place(tmp_path):
    f = tmp_path / "script.py"
    f.write_text("import requests", encoding="utf-8")
    
    with patch("sys.argv", ["depscripter", str(f), "--in-place", "--no-pin"]):
        with patch("depscripter.cli.scan_imports", return_value={"requests"}), \
             patch("depscripter.cli.resolve_packages", return_value={"requests": None}), \
             patch("depscripter.cli.generate_script_metadata", return_value="# /// metadata"), \
             patch("depscripter.cli.inject_metadata", return_value="# /// metadata\nimport requests"):
             
             main()
    
    assert f.read_text(encoding="utf-8") == "# /// metadata\nimport requests"

def test_cli_output_option(tmp_path):
    f = tmp_path / "script.py"
    f.write_text("import requests", encoding="utf-8")
    out = tmp_path / "output.py"
    
    with patch("sys.argv", ["depscripter", str(f), "-o", str(out), "--no-pin"]):
        with patch("depscripter.cli.scan_imports", return_value={"requests"}), \
             patch("depscripter.cli.resolve_packages", return_value={"requests": None}), \
             patch("depscripter.cli.generate_script_metadata", return_value="# /// metadata"), \
             patch("depscripter.cli.inject_metadata", return_value="# /// metadata\nimport requests"):
             
             main()
    
    assert out.read_text(encoding="utf-8") == "# /// metadata\nimport requests"
    assert f.read_text(encoding="utf-8") == "import requests" # original unchanged

def test_cli_python_version_option(tmp_path):
    f = tmp_path / "script.py"
    f.write_text("import requests", encoding="utf-8")
    
    with patch("sys.argv", ["depscripter", str(f), "--python", ">=3.11"]):
        with patch("depscripter.cli.scan_imports", return_value={"requests"}), \
             patch("depscripter.cli.resolve_packages", return_value={"requests": None}), \
             patch("depscripter.cli.generate_script_metadata", return_value="metadata") as mock_gen, \
             patch("depscripter.cli.inject_metadata", return_value="output"):
             
             main()
             
             main()
             
             mock_gen.assert_called_with({"requests": None}, python_requires=">=3.11", overrides={})

def test_cli_python_version_exact(tmp_path):
    f = tmp_path / "script.py"
    f.write_text("import requests", encoding="utf-8")
    
    with patch("sys.argv", ["depscripter", str(f), "--python", "3.10"]):
        with patch("depscripter.cli.scan_imports", return_value={"requests"}), \
             patch("depscripter.cli.resolve_packages", return_value={"requests": None}), \
             patch("depscripter.cli.generate_script_metadata") as mock_gen, \
             patch("depscripter.cli.inject_metadata"):
             
             main()
             
             mock_gen.assert_called_with({"requests": None}, python_requires="3.10", overrides={})

def test_cli_manual_option(tmp_path):
    f = tmp_path / "script.py"
    f.write_text("import requests", encoding="utf-8")
    
    with patch("sys.argv", ["depscripter", str(f), "--manual", "requests>=2.0", "--manual", "pandas"]):
        with patch("depscripter.cli.scan_imports", return_value={"requests"}), \
             patch("depscripter.cli.resolve_packages", return_value={"requests": "2.31.0"}), \
             patch("depscripter.cli.generate_script_metadata") as mock_gen, \
             patch("depscripter.cli.inject_metadata"):
             
             main()
             
             call_kwargs = mock_gen.call_args.kwargs
             overrides = call_kwargs['overrides']
             assert overrides["requests"] == ">=2.0"
             assert overrides["pandas"] == "" # no specifier
