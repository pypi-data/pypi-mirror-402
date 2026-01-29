#!/usr/bin/env python3
"""
Refined CSS usage analysis for Gatekit TUI.
Identifies unused CSS classes with better detection patterns.
"""

import re
from pathlib import Path
from typing import Set


def find_all_class_usage_patterns(file_path: Path) -> Set[str]:
    """Find CSS class usage with comprehensive patterns."""
    used_classes = set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return used_classes

    # All possible patterns for CSS class usage
    patterns = [
        # Standard class assignment patterns
        r'classes\s*=\s*["\']([^"\']*)["\']',
        r"classes\s*=\s*\[([^\]]*)\]",
        # Dynamic class manipulation
        r'add_class\s*\(\s*["\']([^"\']+)["\']',
        r'remove_class\s*\(\s*["\']([^"\']+)["\']',
        r'set_class\s*\(\s*[^,]*,\s*["\']([^"\']+)["\']',
        # Textual CSS class patterns
        r"\.([a-zA-Z][a-zA-Z0-9_-]*)\s*{",  # CSS selectors in CSS blocks
        r"\.([a-zA-Z][a-zA-Z0-9_-]*)\s*:",  # CSS pseudo-selectors
        r"\.([a-zA-Z][a-zA-Z0-9_-]*)\s*>",  # CSS child selectors
        # Widget-specific patterns
        r"Input\.([a-zA-Z][a-zA-Z0-9_-]*)",  # Input.invalid
        r"Select\.([a-zA-Z][a-zA-Z0-9_-]*)",  # Select.invalid
        r"Label\.([a-zA-Z][a-zA-Z0-9_-]*)",  # Label.required
        # Dynamic class names in CSS
        r">\s*\.([a-zA-Z][a-zA-Z0-9_-]*)",
        r"\.([a-zA-Z][a-zA-Z0-9_-]*)\s*\.",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            # Handle both single matches and comma-separated class lists
            if isinstance(match, str):
                # Split on spaces and commas for multiple classes
                classes = re.split(r"[,\s]+", match.strip())
                for cls in classes:
                    cls = cls.strip().strip("\"'")
                    if (
                        cls
                        and not cls.startswith("-")
                        and cls.replace("-", "").replace("_", "").isalnum()
                    ):
                        used_classes.add(cls)

    return used_classes


def extract_all_css_classes() -> Set[str]:
    """Extract all CSS classes from all sources."""
    all_classes = set()
    tui_path = Path("gatekit/tui")

    # Extract from Python files with CSS
    css_files = [
        "utils/array_editor.py",
        "utils/object_item_modal.py",
        "screens/simple_modals.py",
        "screens/config_selector.py",
        "screens/directory_browser_modal.py",
        "screens/plugin_config/modal.py",
        "screens/config_error_modal.py",
        "screens/config_editor/base.py",
        "app.py",
        "widgets/plugin_table.py",
        "widgets/ascii_checkbox.py",
        "widgets/global_plugins.py",
        "widgets/selectable_static.py",
    ]

    for css_file in css_files:
        file_path = tui_path / css_file
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                # Find CSS blocks
                css_pattern = r'(?:DEFAULT_)?CSS\s*=\s*"""(.*?)"""'
                css_matches = re.findall(css_pattern, content, re.DOTALL)
                for css_content in css_matches:
                    # Extract class names
                    class_matches = re.findall(
                        r"\.([a-zA-Z][a-zA-Z0-9_-]*)", css_content
                    )
                    all_classes.update(class_matches)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    # External CSS file
    external_css = tui_path / "styles/validation.css"
    if external_css.exists():
        try:
            with open(external_css, "r") as f:
                content = f.read()
            class_matches = re.findall(r"\.([a-zA-Z][a-zA-Z0-9_-]*)", content)
            all_classes.update(class_matches)
        except Exception as e:
            print(f"Error reading {external_css}: {e}")

    return all_classes


def analyze_usage():
    """Perform comprehensive CSS usage analysis."""
    print("=== Comprehensive CSS Usage Analysis ===")

    tui_path = Path("gatekit/tui")

    # Get all defined CSS classes
    all_classes = extract_all_css_classes()
    print(f"Total CSS classes defined: {len(all_classes)}")

    # Find usage across all Python files
    used_classes = set()

    for py_file in tui_path.rglob("*.py"):
        if py_file.name.startswith("__"):
            continue
        file_used = find_all_class_usage_patterns(py_file)
        used_classes.update(file_used)

    # Calculate unused
    unused_classes = all_classes - used_classes

    # Special validation for classes that might be used dynamically
    potentially_used = set()
    for cls in unused_classes.copy():
        # Check for partial matches or dynamic usage
        for py_file in tui_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            try:
                with open(py_file, "r") as f:
                    content = f.read()
                # Look for string literals containing the class name
                if f'"{cls}"' in content or f"'{cls}'" in content:
                    potentially_used.add(cls)
                    break
                # Look for class name in comments or docstrings (might indicate usage)
                if cls in content and ('"""' in content or "'''" in content):
                    potentially_used.add(cls)
                    break
            except Exception:
                continue

    # Final unused list
    definitely_unused = unused_classes - potentially_used

    print(f"Used CSS classes: {len(used_classes)}")
    print(f"Potentially used (found in strings): {len(potentially_used)}")
    print(f"Definitely unused: {len(definitely_unused)}")

    print("\n=== DEFINITELY UNUSED CSS CLASSES ===")
    for cls in sorted(definitely_unused):
        print(f"  .{cls}")

    if potentially_used:
        print("\n=== POTENTIALLY USED (need manual review) ===")
        for cls in sorted(potentially_used):
            print(f"  .{cls}")


if __name__ == "__main__":
    analyze_usage()
