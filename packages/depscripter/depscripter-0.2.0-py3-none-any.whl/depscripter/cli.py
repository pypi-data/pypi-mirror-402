import argparse
import sys
from pathlib import Path

from depscripter.scanner import scan_imports
from depscripter.resolver import resolve_packages
from depscripter.injector import generate_script_metadata, inject_metadata

def main():
    parser = argparse.ArgumentParser(description="Add PEP 723 metadata to Python scripts.")
    parser.add_argument("file", type=Path, help="Path to the Python script")
    parser.add_argument("--no-pin", action="store_true", help="Do not pin package versions")
    parser.add_argument("-p", "--python", help="Specify strict python version requirement (e.g. '>=3.9')")
    parser.add_argument("-m", "--manual", action="append", help="Manually specify dependency (e.g. 'numpy>=2.0')")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--in-place", action="store_true", help="Modify the file in-place")
    group.add_argument("-o", "--output", type=Path, help="Write output to a specific file")
    
    args = parser.parse_args()
    
    if not args.file.exists():
        sys.exit(f"Error: File {args.file} not found.")
        
    source_code = args.file.read_text(encoding="utf-8")
    
    # Parse manual overrides
    overrides = {}
    if args.manual:
        import re
        # Regex to capture package name (alphanumeric, -, _, .) at start
        # Everything else is the specifier
        pkg_re = re.compile(r"^([A-Za-z0-9_.-]+)(.*)$")
        for manual_dep in args.manual:
            match = pkg_re.match(manual_dep)
            if match:
                pkg_name = match.group(1)
                specifier = match.group(2)
                overrides[pkg_name] = specifier
            else:
                # If regex mismatch (weird inputs), just assume whole string is name?
                # or warn? Let's just key it by whole string and empty spec
                overrides[manual_dep] = ""
    
    # Scan
    modules = scan_imports(source_code)
    
    # Resolve
    dependencies = resolve_packages(modules, pin_versions=not args.no_pin)
    
    # Generate metadata
    metadata = generate_script_metadata(dependencies, python_requires=args.python, overrides=overrides)
    
    # Inject
    new_source = inject_metadata(source_code, metadata)
    
    if args.in_place:
        args.file.write_text(new_source, encoding="utf-8")
        print(f"Updated {args.file}")
    elif args.output:
        args.output.write_text(new_source, encoding="utf-8")
        print(f"Saved to {args.output}")
    else:
        print(new_source, end="")

if __name__ == "__main__":
    main()
