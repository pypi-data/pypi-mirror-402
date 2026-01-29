import sys
from unittest.mock import patch, MagicMock
from depscripter.resolver import resolve_packages

def test_resolve_packages_simple():
    module_names = {"requests", "yaml"}
    
    with patch("depscripter.resolver.get_packages_distributions") as mock_dist:
        mock_dist.return_value = {
            "requests": ["requests"],
            "yaml": ["PyYAML"],
        }
        
        with patch("importlib.metadata.version") as mock_ver:
            mock_ver.side_effect = lambda x: "2.31.0" if x == "requests" else "6.0"
            
            resolved = resolve_packages(module_names, pin_versions=True)
            
            assert resolved["requests"] == "2.31.0"
            assert resolved["PyYAML"] == "6.0"

def test_resolve_packages_no_pin():
    module_names = {"requests"}
    
    with patch("depscripter.resolver.get_packages_distributions") as mock_dist:
        mock_dist.return_value = {"requests": ["requests"]}
        
        resolved = resolve_packages(module_names, pin_versions=False)
        assert resolved["requests"] is None

def test_resolve_missing_distribution():
    # e.g. stdlib "sys"
    module_names = {"sys"}
    
    with patch("depscripter.resolver.get_packages_distributions") as mock_dist:
        mock_dist.return_value = {} # sys not in external dists
        
        resolved = resolve_packages(module_names)
        assert resolved == {}

def test_resolve_package_not_found_version():
    # package exists in map but not installed? (shouldn't happen technically if map comes from installed)
    # But just in case
    module_names = {"foo"}
    
    with patch("depscripter.resolver.get_packages_distributions") as mock_dist:
        mock_dist.return_value = {"foo": ["foo-pkg"]}
        
        with patch("importlib.metadata.version") as mock_ver:
            from importlib.metadata import PackageNotFoundError
            mock_ver.side_effect = PackageNotFoundError
            
            resolved = resolve_packages(module_names, pin_versions=True)
            assert resolved["foo-pkg"] is None
