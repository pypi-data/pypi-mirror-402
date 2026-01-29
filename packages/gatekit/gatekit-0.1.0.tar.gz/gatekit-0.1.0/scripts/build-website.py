#!/usr/bin/env python3
"""
Build the Gatekit website from markdown documentation.

Usage:
    python scripts/build-website.py

Requires: pip install mistune pygments

This script:
1. Reads markdown files from docs/
2. Converts them to HTML with syntax highlighting
3. Wraps them in a consistent template
4. Writes to website/docs/

The script is excluded from the public repo (scripts/ is in sync exclusions).
"""

import re
import shutil
from pathlib import Path

try:
    import mistune
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import HtmlFormatter
    from pygments.util import ClassNotFound
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install mistune pygments")
    raise SystemExit(1)


# Paths
ROOT = Path(__file__).parent.parent
DOCS_DIR = ROOT / "docs"
WEBSITE_DIR = ROOT / "website"
TEMPLATE_DIR = WEBSITE_DIR / "_templates"

# Directories to skip
SKIP_DIRS = {"testing", "images"}


class HighlightRenderer(mistune.HTMLRenderer):
    """Custom renderer with syntax highlighting for code blocks."""

    def block_code(self, code, info=None):
        if info:
            info = info.strip()
            try:
                lexer = get_lexer_by_name(info, stripall=True)
            except ClassNotFound:
                lexer = guess_lexer(code)
        else:
            try:
                lexer = guess_lexer(code)
            except ClassNotFound:
                return f'<pre><code>{mistune.escape(code)}</code></pre>\n'

        formatter = HtmlFormatter(nowrap=True)
        highlighted = highlight(code, lexer, formatter)
        return f'<pre><code class="language-{info or "text"}">{highlighted}</code></pre>\n'

    def heading(self, text, level, **attrs):
        # Generate an ID from the heading text for anchor links
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        return f'<h{level} id="{slug}">{text}</h{level}>\n'

    def link(self, text, url, title=None):
        # Convert .md links to .html for internal docs
        if url and not url.startswith(('http://', 'https://', '#', 'mailto:')):
            if url.endswith('.md'):
                url = url[:-3] + '.html'
        title_attr = f' title="{mistune.escape(title)}"' if title else ''
        return f'<a href="{url}"{title_attr}>{text}</a>'


def create_markdown_parser():
    """Create a mistune parser with our custom renderer."""
    renderer = HighlightRenderer()
    return mistune.create_markdown(renderer=renderer, plugins=['table', 'strikethrough'])


def get_template(name: str) -> str:
    """Load an HTML template."""
    template_path = TEMPLATE_DIR / f"{name}.html"
    if template_path.exists():
        return template_path.read_text()
    raise FileNotFoundError(f"Template not found: {template_path}")


def extract_title(content: str, filename: str) -> str:
    """Extract title from markdown content (first h1) or filename."""
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    # Fallback to filename
    return filename.replace('-', ' ').replace('_', ' ').title()


def extract_description(content: str) -> str:
    """Extract first paragraph as description for meta tags."""
    # Skip the title and find first paragraph
    lines = content.split('\n')
    in_paragraph = False
    paragraph_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_paragraph:
                break
            continue
        if stripped.startswith('#'):
            continue
        if stripped.startswith(('```', '|', '-', '*', '>')):
            if in_paragraph:
                break
            continue
        in_paragraph = True
        paragraph_lines.append(stripped)

    desc = ' '.join(paragraph_lines)[:160]
    if len(desc) == 160:
        desc = desc[:157] + '...'
    return desc


def build_nav_tree():
    """Build navigation structure from docs directory."""
    nav = {
        "Getting Started": [
            ("Quick Start", "/docs/getting-started.html"),
        ],
        "Guides": [
            ("Managing Tools", "/docs/guides/managing-tools.html"),
        ],
        "Concepts": [
            ("Configuration", "/docs/concepts/configuration.html"),
            ("Routing Model", "/docs/concepts/routing.html"),
            ("Security Model", "/docs/concepts/security.html"),
        ],
        "Plugin Development": [
            ("Plugin Guide", "/docs/plugins/development-guide.html"),
        ],
        "Reference": [
            ("Built-in Plugins", "/docs/reference/plugins/"),
            ("Known Issues", "/docs/reference/known-issues.html"),
        ],
        "Decisions": [
            ("Architecture Decision Records", "/decisions/"),
        ],
    }
    return nav


def render_nav(nav: dict, current_path: str = "") -> str:
    """Render navigation HTML."""
    html_parts = ['<nav class="docs-nav">']

    for section, items in nav.items():
        html_parts.append(f'<div class="nav-section">')
        html_parts.append(f'<h3>{section}</h3>')
        html_parts.append('<ul>')
        for title, path in items:
            active = ' class="active"' if path == current_path else ''
            html_parts.append(f'<li><a href="{path}"{active}>{title}</a></li>')
        html_parts.append('</ul>')
        html_parts.append('</div>')

    html_parts.append('</nav>')
    return '\n'.join(html_parts)


def process_markdown_file(md_path: Path, output_path: Path, template: str, nav: dict):
    """Convert a markdown file to HTML."""
    content = md_path.read_text()
    title = extract_title(content, md_path.stem)
    description = extract_description(content)

    parser = create_markdown_parser()
    html_content = parser(content)

    # Calculate relative path for nav highlighting
    rel_path = "/" + str(output_path.relative_to(WEBSITE_DIR))
    nav_html = render_nav(nav, rel_path)

    # Calculate depth for relative paths in template
    depth = len(output_path.relative_to(WEBSITE_DIR).parts) - 1
    base_path = "../" * depth if depth > 0 else "./"

    # Fill template
    html = template.replace("{{title}}", title)
    html = html.replace("{{description}}", description)
    html = html.replace("{{nav}}", nav_html)
    html = html.replace("{{content}}", html_content)
    html = html.replace("{{base}}", base_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
    print(f"  {md_path.name} -> {output_path.relative_to(WEBSITE_DIR)}")


def build_docs_index(template: str, nav: dict):
    """Build the docs index page."""
    content = """
<h1>Gatekit Documentation</h1>

<p>Gatekit is a Model Context Protocol (MCP) gateway that lets you control communication between your LLM and MCP tools using a plugin architecture.</p>

<h2>Getting Started</h2>
<p>New to Gatekit? Start here:</p>
<ul>
  <li><a href="/docs/getting-started.html">Quick Start Guide</a> - Installation and basic setup</li>
</ul>

<h2>Guides</h2>
<p>Step-by-step guides for common tasks:</p>
<ul>
  <li><a href="/docs/guides/managing-tools.html">Managing Tools</a> - Filter, rename, and customize MCP tools</li>
</ul>

<h2>Concepts</h2>
<p>Understand how Gatekit works:</p>
<ul>
  <li><a href="/docs/concepts/configuration.html">Configuration</a> - Complete configuration reference</li>
  <li><a href="/docs/concepts/routing.html">Routing Model</a> - How requests are routed to servers</li>
  <li><a href="/docs/concepts/security.html">Security Model</a> - Security architecture and plugin behavior</li>
</ul>

<h2>Plugin Development</h2>
<p>Extend Gatekit with custom plugins:</p>
<ul>
  <li><a href="/docs/plugins/development-guide.html">Plugin Development Guide</a> - Write your own plugins</li>
</ul>

<h2>Reference</h2>
<ul>
  <li><a href="/docs/reference/plugins/">Built-in Plugins</a> - Documentation for all included plugins</li>
  <li><a href="/docs/reference/known-issues.html">Known Issues</a> - Current limitations and workarounds</li>
  <li><a href="/decisions/">Architecture Decision Records</a> - Design decisions and rationale</li>
</ul>
"""

    nav_html = render_nav(nav, "/docs/")
    html = template.replace("{{title}}", "Documentation")
    html = html.replace("{{description}}", "Gatekit documentation - configuration, guides, and reference")
    html = html.replace("{{nav}}", nav_html)
    html = html.replace("{{content}}", content)
    html = html.replace("{{base}}", "../")

    output_path = WEBSITE_DIR / "docs" / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
    print(f"  Docs index -> docs/index.html")


def build_docs():
    """Build all documentation pages."""
    print("Building documentation...")

    template = get_template("docs")
    nav = build_nav_tree()

    # Build the docs index page
    build_docs_index(template, nav)

    # Map source files to output locations
    file_mapping = {
        # Getting Started
        "getting-started.md": "docs/getting-started.html",
        # Guides
        "tutorial-managing-tools.md": "docs/guides/managing-tools.html",
        # Concepts
        "configuration-specification.md": "docs/concepts/configuration.html",
        "routing-model.md": "docs/concepts/routing.html",
        "security-model.md": "docs/concepts/security.html",
        # Plugins
        "plugin-development-guide.md": "docs/plugins/development-guide.html",
        # Reference (builtin-plugins replaced by generated plugin docs)
        "known-issues.md": "docs/reference/known-issues.html",
    }

    for src_name, dest_path in file_mapping.items():
        src_path = DOCS_DIR / src_name
        if src_path.exists():
            output_path = WEBSITE_DIR / dest_path
            process_markdown_file(src_path, output_path, template, nav)
        else:
            print(f"  Warning: {src_name} not found, skipping")


def build_plugin_docs():
    """Build plugin reference documentation (auto-generated)."""
    print("Building plugin reference...")

    template = get_template("docs")
    nav = build_nav_tree()

    plugin_docs_dir = DOCS_DIR / "reference" / "plugins"
    output_dir = WEBSITE_DIR / "docs" / "reference" / "plugins"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not plugin_docs_dir.exists():
        print("  Warning: docs/reference/plugins/ not found, skipping")
        print("  Run: python scripts/generate-plugin-docs.py first")
        return

    # Process all markdown files in plugin docs directory
    for md_path in sorted(plugin_docs_dir.glob("*.md")):
        output_path = output_dir / (md_path.stem + ".html")
        process_markdown_file(md_path, output_path, template, nav)


def build_adrs():
    """Build Architecture Decision Records pages."""
    print("Building ADRs...")

    template = get_template("docs")
    nav = build_nav_tree()

    adr_dir = DOCS_DIR / "decision-records"
    output_dir = WEBSITE_DIR / "decisions"
    output_dir.mkdir(parents=True, exist_ok=True)

    adrs = []
    for md_path in sorted(adr_dir.glob("*.md")):
        content = md_path.read_text()
        title = extract_title(content, md_path.stem)
        output_path = output_dir / (md_path.stem + ".html")
        process_markdown_file(md_path, output_path, template, nav)
        adrs.append((md_path.stem, title, output_path.name))

    # Build ADR index
    build_adr_index(adrs, template, nav)


def build_adr_index(adrs: list, template: str, nav: dict):
    """Build the ADR index page."""
    html_parts = [
        '<h1>Architecture Decision Records</h1>',
        '<p>This section documents significant architectural decisions made during Gatekit development. '
        'Each ADR captures the context, decision, and consequences of a particular choice.</p>',
        '<table class="adr-table">',
        '<thead><tr><th>ID</th><th>Title</th></tr></thead>',
        '<tbody>',
    ]

    for stem, title, filename in adrs:
        # Extract ADR number from filename (e.g., "001" from "001-transport-layer-architecture")
        adr_num = stem.split('-')[0] if '-' in stem else stem
        html_parts.append(f'<tr><td>{adr_num}</td><td><a href="{filename}">{title}</a></td></tr>')

    html_parts.extend(['</tbody>', '</table>'])

    content = '\n'.join(html_parts)
    nav_html = render_nav(nav, "/decisions/")

    html = template.replace("{{title}}", "Architecture Decision Records")
    html = html.replace("{{description}}", "Architectural decisions made during Gatekit development")
    html = html.replace("{{nav}}", nav_html)
    html = html.replace("{{content}}", content)
    html = html.replace("{{base}}", "../")

    output_path = WEBSITE_DIR / "decisions" / "index.html"
    output_path.write_text(html)
    print(f"  ADR index -> decisions/index.html")


def copy_images():
    """Copy images to website."""
    print("Copying images...")
    src_dir = DOCS_DIR / "images"
    dest_dir = WEBSITE_DIR / "images"

    if dest_dir.exists():
        shutil.rmtree(dest_dir)

    if src_dir.exists():
        shutil.copytree(src_dir, dest_dir)
        print(f"  Copied {len(list(dest_dir.glob('*')))} images")


def main():
    """Build the complete website."""
    print("=" * 50)
    print("Building Gatekit Website")
    print("=" * 50)

    # Ensure output directories exist
    (WEBSITE_DIR / "docs").mkdir(parents=True, exist_ok=True)

    # Build components
    copy_images()
    build_docs()
    build_plugin_docs()
    build_adrs()

    print("=" * 50)
    print("Build complete!")
    print(f"Output: {WEBSITE_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    main()
