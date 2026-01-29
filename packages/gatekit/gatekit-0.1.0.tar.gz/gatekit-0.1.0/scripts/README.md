# Development Scripts

This directory contains utility scripts for development and maintenance tasks.

## CSS Analysis Scripts

### `analyze_css_usage.py`
Basic CSS usage analysis script that identifies potentially unused CSS classes in the TUI.

**Usage:**
```bash
cd /path/to/gatekit
python scripts/analyze_css_usage.py
```

**Output:**
- Lists all CSS classes found in the codebase
- Shows which files use which CSS classes  
- Identifies potentially unused CSS classes

### `refined_css_analysis.py`  
More sophisticated CSS usage analysis with better detection patterns and fewer false positives.

**Usage:**
```bash
cd /path/to/gatekit
python scripts/refined_css_analysis.py
```

**Output:**
- Total CSS classes defined vs used
- Definitely unused CSS classes (safe to remove)
- Potentially used classes that need manual review

**Note:** The "potentially used" classes are often Python attribute names that happen to match CSS class names, not actual CSS usage.

## Guidelines

- Scripts in this directory are for development use only
- They should not be shipped with the production package
- Add documentation here when adding new development utilities
- Test scripts before committing to ensure they work correctly
