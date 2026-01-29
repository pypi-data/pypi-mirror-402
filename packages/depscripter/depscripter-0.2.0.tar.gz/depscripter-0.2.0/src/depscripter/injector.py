import re
import sys
from typing import Dict, Optional


def generate_script_metadata(dependencies: Dict[str, Optional[str]], python_requires: Optional[str] = None, overrides: Optional[Dict[str, str]] = None) -> str:
    """
    Generates the PEP 723 metadata block.
    
    overrides: Dictionary of package name -> version specifier (e.g. ">=2.0")
    """
    if python_requires is None:
        # Default to current running python version major.minor
        v = sys.version_info
        python_requires = f">={v.major}.{v.minor}"
    elif python_requires and python_requires[0].isdigit():
        # Prepend >= if it's just a version number (uv convention)
        python_requires = f">={python_requires}"
    
    if overrides is None:
        overrides = {}

    lines = []
    lines.append("# /// script")
    lines.append(f'# requires-python = "{python_requires}"')
    lines.append("# dependencies = [")
    
    # Merge keys from dependencies and overrides
    all_packages = set(dependencies.keys()) | set(overrides.keys())
    sorted_deps = sorted(all_packages)
    
    for pkg in sorted_deps:
        if pkg in overrides:
            # Use manual override specifier
            spec = overrides[pkg]
            lines.append(f'#     "{pkg}{spec}",')
        else:
            version = dependencies[pkg]
            if version:
                lines.append(f'#     "{pkg}=={version}",')
            else:
                lines.append(f'#     "{pkg}",')
            
    lines.append("# ]")
    lines.append("# ///")
    
    return "\n".join(lines)

def inject_metadata(source_code: str, metadata_block: str) -> str:
    """
    Inserts the metadata block into the source code, replacing an existing one if present,
    or preserving shebang and encoding lines if inserting for the first time.
    """
    lines = source_code.splitlines(keepends=True)
    
    # Check for existing block
    start_idx = -1
    end_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == "# /// script":
            start_idx = i
        elif start_idx != -1 and line.strip() == "# ///":
            end_idx = i
            break
            
    # Prepare the new block as a list of lines with newlines
    formatted_block = [line + "\n" for line in metadata_block.splitlines()]
    
    if start_idx != -1 and end_idx != -1:
        # Replace existing block
        lines[start_idx : end_idx + 1] = formatted_block
    else:
        # Insert for the first time
        insert_idx = 0
        # Logic to skip shebang/encoding
        if lines:
            # Shebang
            if lines[0].startswith("#!"):
                insert_idx += 1
                
                # Encoding cookie (must be line 1 or 2)
                coding_re = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)")
                if len(lines) > 1 and coding_re.match(lines[1]):
                    insert_idx += 1
            else:
                # Check line 1 for encoding
                coding_re = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)")
                if coding_re.match(lines[0]):
                    insert_idx += 1
        
        # Add an extra newline for separation from code/docstrings
        formatted_block.append("\n")
        lines[insert_idx:insert_idx] = formatted_block
    
    return "".join(lines)
