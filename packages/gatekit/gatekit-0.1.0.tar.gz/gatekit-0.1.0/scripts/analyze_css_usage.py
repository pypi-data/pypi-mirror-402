#!/usr/bin/env python3
"""
Analyze CSS usage in Gatekit TUI.
Identifies unused CSS classes and rules.
"""

import re
from pathlib import Path
from typing import Set, Dict


def extract_css_from_file(file_path: Path) -> Dict[str, Set[str]]:
    """Extract CSS classes and rules from a Python file."""
    css_rules = set()
    css_classes = set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {"rules": css_rules, "classes": css_classes}

    # Find CSS blocks (DEFAULT_CSS = """ or CSS = """)
    css_pattern = r'(?:DEFAULT_)?CSS\s*=\s*"""(.*?)"""'
    css_matches = re.findall(css_pattern, content, re.DOTALL)

    for css_content in css_matches:
        # Extract CSS selectors and class names
        # Match class selectors like .class-name
        class_matches = re.findall(r"\.([a-zA-Z][a-zA-Z0-9_-]*)", css_content)
        css_classes.update(class_matches)

        # Extract all CSS rules (simplified - just the selectors)
        # This regex captures CSS selectors (including element selectors, class selectors, etc.)
        rule_pattern = r"^([^{]+){"
        for line in css_content.split("\n"):
            match = re.match(rule_pattern, line.strip())
            if match:
                selector = match.group(1).strip()
                css_rules.add(selector)

    return {"rules": css_rules, "classes": css_classes}


def extract_css_from_external_file(file_path: Path) -> Dict[str, Set[str]]:
    """Extract CSS classes and rules from external CSS file."""
    css_rules = set()
    css_classes = set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {"rules": css_rules, "classes": css_classes}

    # Extract class selectors like .class-name
    class_matches = re.findall(r"\.([a-zA-Z][a-zA-Z0-9_-]*)", content)
    css_classes.update(class_matches)

    # Extract all CSS rules
    rule_pattern = r"^([^{]+){"
    for line in content.split("\n"):
        match = re.match(rule_pattern, line.strip())
        if match:
            selector = match.group(1).strip()
            css_rules.add(selector)

    return {"rules": css_rules, "classes": css_classes}


def find_class_usage_in_file(file_path: Path, css_classes: Set[str]) -> Set[str]:
    """Find which CSS classes are used in a Python file."""
    used_classes = set()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return used_classes

    for css_class in css_classes:
        # Look for class usage patterns:
        # classes="class-name"
        # classes='class-name'
        # classes=["class-name"]
        # classes=['class-name']
        # add_class("class-name")
        # remove_class("class-name")
        patterns = [
            rf'classes\s*=\s*["\']([^"\']*{re.escape(css_class)}[^"\']*)["\']',
            rf'classes\s*=\s*\[["\'][^"\']*{re.escape(css_class)}[^"\']*["\']',
            rf'add_class\s*\(\s*["\']({re.escape(css_class)})["\']',
            rf'remove_class\s*\(\s*["\']({re.escape(css_class)})["\']',
        ]

        for pattern in patterns:
            if re.search(pattern, content):
                used_classes.add(css_class)
                break

    return used_classes


def main():
    """Main analysis function."""
    tui_path = Path("gatekit/tui")

    if not tui_path.exists():
        print("TUI path not found. Make sure you're in the project root.")
        return

    # Collect all CSS definitions
    all_css_classes = set()
    all_css_rules = set()
    css_sources = {}  # Map class -> source file

    print("=== Scanning for CSS definitions ===")

    # Scan Python files for CSS definitions
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
            result = extract_css_from_file(file_path)
            all_css_classes.update(result["classes"])
            all_css_rules.update(result["rules"])

            # Map classes to source files
            for css_class in result["classes"]:
                if css_class not in css_sources:
                    css_sources[css_class] = []
                css_sources[css_class].append(str(file_path))

            print(
                f"  {file_path}: {len(result['classes'])} classes, {len(result['rules'])} rules"
            )

    # Check external CSS file
    external_css = tui_path / "styles/validation.css"
    if external_css.exists():
        result = extract_css_from_external_file(external_css)
        all_css_classes.update(result["classes"])
        all_css_rules.update(result["rules"])

        for css_class in result["classes"]:
            if css_class not in css_sources:
                css_sources[css_class] = []
            css_sources[css_class].append(str(external_css))

        print(
            f"  {external_css}: {len(result['classes'])} classes, {len(result['rules'])} rules"
        )

    print(f"\nTotal CSS classes found: {len(all_css_classes)}")
    print(f"Total CSS rules found: {len(all_css_rules)}")

    # Now scan for class usage
    print("\n=== Scanning for CSS class usage ===")
    used_classes = set()

    # Scan all Python files in TUI
    for py_file in tui_path.rglob("*.py"):
        if py_file.name.startswith("__"):
            continue

        file_used_classes = find_class_usage_in_file(py_file, all_css_classes)
        used_classes.update(file_used_classes)

        if file_used_classes:
            print(
                f"  {py_file}: uses {len(file_used_classes)} classes: {sorted(file_used_classes)}"
            )

    # Find unused classes
    unused_classes = all_css_classes - used_classes

    print("\n=== Results ===")
    print(f"Used CSS classes: {len(used_classes)}")
    print(f"Unused CSS classes: {len(unused_classes)}")

    if unused_classes:
        print("\n=== UNUSED CSS CLASSES ===")
        for css_class in sorted(unused_classes):
            sources = css_sources.get(css_class, ["Unknown"])
            print(f"  .{css_class} (defined in: {', '.join(sources)})")

    if used_classes:
        print("\n=== USED CSS CLASSES ===")
        for css_class in sorted(used_classes):
            sources = css_sources.get(css_class, ["Unknown"])
            print(f"  .{css_class} (defined in: {', '.join(sources)})")


if __name__ == "__main__":
    main()
