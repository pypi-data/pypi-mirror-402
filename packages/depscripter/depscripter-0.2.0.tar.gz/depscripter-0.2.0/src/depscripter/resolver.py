import sys
from typing import Dict, List, Optional, Set
import importlib.metadata

def _get_packages_distributions_fallback() -> Dict[str, List[str]]:
    """
    Fallback for importlib.metadata.packages_distributions() for generic Python < 3.10.
    Builds a mapping of top-level module names to distribution names.
    """
    pkg_to_dist = {}
    for dist in importlib.metadata.distributions():
        # Try to get top-level modules
        try:
            # .read_text('top_level.txt') might return None if file missing
            top_level = dist.read_text('top_level.txt')
            if top_level:
                for module in top_level.splitlines():
                    module = module.strip()
                    if module:
                        pkg_to_dist.setdefault(module, []).append(dist.metadata['Name'])
                continue
        except Exception:
            pass

        # If top_level.txt is missing (e.g. some wheels), inspect files?
        # This is expensive and complex to do perfectly correctly without external libs.
        # For now, rely on top_level.txt which covers most cases.
        # Alternatively, name matching? e.g. dist "requests" provides "requests"
        
        # Simple heuristic: normalized name matches?
        # This is risky. Let's just stick to top_level.txt for now as per stdlib implementation inspiration.
        # Actually stdlib implementation also checks for extension modules, but that's hard.
        pass
    
    return pkg_to_dist

def get_packages_distributions() -> Dict[str, List[str]]:
    if hasattr(importlib.metadata, 'packages_distributions'):
        return importlib.metadata.packages_distributions()
    return _get_packages_distributions_fallback()

def resolve_packages(module_names: Set[str], pin_versions: bool = True) -> Dict[str, Optional[str]]:
    """
    Resolves module names to PyPI package names and optional versions.
    
    Returns a dict: {package_name: version_string_or_None}
    """
    mapping = get_packages_distributions()
    resolved = {}
    
    for module in module_names:
        # Skip private modules or special keys
        if module.startswith('_'):
            continue
            
        dists = mapping.get(module)
        if not dists:
            # Perhaps it's a standard library module or local file.
            # We skip it.
            continue
        
        # If multiple distributions provide the same module, pick the first one?
        # Or maybe warn? For now, pick first.
        dist_name = dists[0]
        
        if dist_name in resolved:
            continue
            
        version = None
        if pin_versions:
            try:
                version = importlib.metadata.version(dist_name)
            except importlib.metadata.PackageNotFoundError:
                pass
        
        resolved[dist_name] = version
        
    return resolved
