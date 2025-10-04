#!/usr/bin/env python3
"""
GitHub Pages Documentation Generator
Reads all crawl_inventory.csv and crawl_summary.json files from docs/
and generates an interactive HTML site with collapsible sections
"""

import os
import json
import csv
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse

# Base path to docs directory
DOCS_BASE = Path(__file__).parent.parent / 'docs'
OUTPUT_DIR = Path(__file__).parent

def read_crawl_data():
    """Read all crawl inventory and summary files"""
    sites = {}

    # Find all subdirectories in docs/
    for site_dir in DOCS_BASE.iterdir():
        if not site_dir.is_dir():
            continue

        site_name = site_dir.name
        crawl_data = {
            'name': site_name,
            'pages': [],
            'summary': {},
            'crawl_date': None
        }

        # Read crawl_inventory.csv if it exists
        csv_file = site_dir / 'crawl_inventory.csv'
        if csv_file.exists():
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    crawl_data['pages'].append(row)

        # Read crawl_summary.json if it exists
        json_file = site_dir / 'crawl_summary.json'
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)
                crawl_data['summary'] = summary
                crawl_data['crawl_date'] = summary.get('crawl_date')

                # If no CSV, build pages list from summary files
                if not crawl_data['pages'] and 'files' in summary:
                    for file_path in summary.get('files', []):
                        file_name = Path(file_path).name
                        # Infer URL from filename
                        url = f"{summary.get('base_url', '')}/{file_name.replace('.md', '')}"
                        crawl_data['pages'].append({
                            'URL': url,
                            'Title': file_name.replace('.md', '').replace('-', ' ').title(),
                            'Local File': file_path,
                            'Source': 'file',
                            'Depth': '0'
                        })

        # Only add sites that have data
        if crawl_data['pages'] or crawl_data['summary']:
            sites[site_name] = crawl_data

    return sites

def build_hierarchy(pages):
    """Build hierarchical structure from flat page list"""
    hierarchy = defaultdict(lambda: {'children': defaultdict(dict), 'pages': []})

    for page in pages:
        url = page.get('URL', '')
        if not url:
            continue

        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]

        # Build nested structure
        current = hierarchy[parsed.netloc]
        for i, part in enumerate(path_parts[:-1]):
            if part not in current['children']:
                current['children'][part] = {'children': defaultdict(dict), 'pages': []}
            current = current['children'][part]

        # Add page to appropriate level
        current['pages'].append(page)

    return hierarchy

def format_site_name(name):
    """Convert directory name to human-readable site name"""
    name_map = {
        'abo-site': 'Administrative Business Office (ABO)',
        'intranet': 'CAES Intranet',
        'caes-main-site': 'CAES Main Website',
        'extension-site': 'UGA Extension',
        'oit-site': 'Office of Information Technology (OIT)',
        'olod-site': 'Office of Learning & Organizational Development (OLOD)',
        'omc-site': 'Office of Marketing & Communications (OMC)',
        'brand-site': 'CAES Brand Guidelines',
        'teamdynamix': 'TeamDynamix',
        'dropbox': 'Dropbox Documents',
        'gacounts-site': 'GA Counts'
    }
    return name_map.get(name, name.replace('-', ' ').title())

def generate_html(sites):
    """Generate interactive HTML documentation"""

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CAES Chatbot - Crawled Content Documentation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }

        header {
            background: linear-gradient(135deg, #ba0c2f 0%, #8b0000 100%);
            color: white;
            padding: 2rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
        }

        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }

        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }

        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            color: #ba0c2f;
        }

        .stat-label {
            font-size: 0.9rem;
            color: #666;
            margin-top: 0.5rem;
        }

        .site-section {
            background: white;
            margin: 2rem 0;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .site-header {
            background: #333;
            color: white;
            padding: 1.5rem;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.3s;
        }

        .site-header:hover {
            background: #444;
        }

        .site-header h2 {
            font-size: 1.5rem;
            font-weight: 600;
        }

        .site-meta {
            font-size: 0.9rem;
            opacity: 0.8;
        }

        .toggle-icon {
            font-size: 1.5rem;
            transition: transform 0.3s;
        }

        .toggle-icon.expanded {
            transform: rotate(180deg);
        }

        .site-content {
            display: none;
            padding: 1.5rem;
        }

        .site-content.expanded {
            display: block;
        }

        .subsection {
            margin: 1rem 0;
            border-left: 3px solid #ba0c2f;
            padding-left: 1rem;
        }

        .subsection-header {
            font-weight: 600;
            color: #ba0c2f;
            cursor: pointer;
            padding: 0.5rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .subsection-header:hover {
            color: #8b0000;
        }

        .subsection-content {
            display: none;
            margin-top: 0.5rem;
        }

        .subsection-content.expanded {
            display: block;
        }

        .page-list {
            list-style: none;
            margin: 0.5rem 0;
        }

        .page-item {
            padding: 0.75rem;
            margin: 0.5rem 0;
            background: #f9f9f9;
            border-radius: 4px;
            transition: background 0.2s;
        }

        .page-item:hover {
            background: #f0f0f0;
        }

        .page-title {
            font-weight: 600;
            color: #333;
            margin-bottom: 0.25rem;
        }

        .page-url {
            font-size: 0.85rem;
            color: #0066cc;
            word-break: break-all;
            text-decoration: none;
        }

        .page-url:hover {
            text-decoration: underline;
        }

        .page-meta {
            font-size: 0.8rem;
            color: #666;
            margin-top: 0.25rem;
        }

        .search-box {
            margin: 2rem 0;
            padding: 1rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .search-box input {
            width: 100%;
            padding: 1rem;
            font-size: 1rem;
            border: 2px solid #ddd;
            border-radius: 4px;
            transition: border-color 0.3s;
        }

        .search-box input:focus {
            outline: none;
            border-color: #ba0c2f;
        }

        footer {
            text-align: center;
            padding: 2rem;
            color: #666;
            margin-top: 3rem;
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: #ba0c2f;
            color: white;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 0.5rem;
        }

        .expand-all {
            background: #ba0c2f;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1rem;
            margin: 1rem 0;
            transition: background 0.3s;
        }

        .expand-all:hover {
            background: #8b0000;
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>CAES Chatbot Documentation</h1>
            <p class="subtitle">Comprehensive index of all crawled content sources</p>
        </div>
    </header>

    <div class="container">
        <div class="stats">
"""

    # Calculate statistics
    total_sites = len(sites)
    total_pages = sum(len(site['pages']) for site in sites.values())

    html += f"""
            <div class="stat-card">
                <div class="stat-number">{total_sites}</div>
                <div class="stat-label">Total Sites Crawled</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_pages:,}</div>
                <div class="stat-label">Total Pages Indexed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{datetime.now().strftime('%Y-%m-%d')}</div>
                <div class="stat-label">Last Updated</div>
            </div>
        </div>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Search pages by title or URL...">
        </div>

        <button class="expand-all" onclick="toggleAll()">Expand All Sites</button>

        <div id="sitesContainer">
"""

    # Generate content for each site
    for site_name, site_data in sorted(sites.items()):
        display_name = format_site_name(site_name)
        page_count = len(site_data['pages'])
        base_url = site_data['summary'].get('base_url', 'N/A')
        crawl_date = site_data.get('crawl_date', 'Unknown')

        if crawl_date != 'Unknown':
            try:
                crawl_date = datetime.fromisoformat(crawl_date.replace('Z', '+00:00')).strftime('%Y-%m-%d')
            except:
                pass

        html += f"""
            <div class="site-section" data-site="{site_name}">
                <div class="site-header" onclick="toggleSite('{site_name}')">
                    <div>
                        <h2>{display_name}<span class="badge">{page_count} pages</span></h2>
                        <div class="site-meta">
                            Base URL: {base_url} | Crawled: {crawl_date}
                        </div>
                    </div>
                    <span class="toggle-icon">▼</span>
                </div>
                <div class="site-content" id="content-{site_name}">
"""

        # Group pages by path hierarchy for better organization
        if site_name == 'dropbox':
            # Special handling for dropbox - just list all files
            html += '<ul class="page-list">\n'
            for page in sorted(site_data['pages'], key=lambda x: x.get('Title', '')):
                title = page.get('Title', 'Untitled')
                url = page.get('URL', '#')
                local_file = page.get('Local File', '')

                html += f"""
                    <li class="page-item">
                        <div class="page-title">{title}</div>
                        <a href="{url}" class="page-url" target="_blank">{url}</a>
                        <div class="page-meta">Local: {Path(local_file).name if local_file else 'N/A'}</div>
                    </li>
"""
            html += '</ul>\n'
        else:
            # Hierarchical display for websites
            hierarchy = build_hierarchy(site_data['pages'])
            html += render_hierarchy(hierarchy, site_name)

        html += """
                </div>
            </div>
"""

    html += """
        </div>
    </div>

    <footer>
        <p>Generated by CAES Chatbot Documentation Generator</p>
        <p>University of Georgia - College of Agricultural & Environmental Sciences</p>
    </footer>

    <script>
        let allExpanded = false;

        function toggleSite(siteName) {
            const content = document.getElementById('content-' + siteName);
            const icon = event.currentTarget.querySelector('.toggle-icon');

            content.classList.toggle('expanded');
            icon.classList.toggle('expanded');
        }

        function toggleSubsection(sectionId) {
            const content = document.getElementById(sectionId);
            content.classList.toggle('expanded');
            event.target.querySelector('span').textContent =
                content.classList.contains('expanded') ? '▼' : '▶';
        }

        function toggleAll() {
            allExpanded = !allExpanded;
            const sections = document.querySelectorAll('.site-content');
            const icons = document.querySelectorAll('.toggle-icon');

            sections.forEach(section => {
                if (allExpanded) {
                    section.classList.add('expanded');
                } else {
                    section.classList.remove('expanded');
                }
            });

            icons.forEach(icon => {
                if (allExpanded) {
                    icon.classList.add('expanded');
                } else {
                    icon.classList.remove('expanded');
                }
            });

            event.target.textContent = allExpanded ? 'Collapse All Sites' : 'Expand All Sites';
        }

        // Search functionality
        document.getElementById('searchInput').addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const pageItems = document.querySelectorAll('.page-item');

            pageItems.forEach(item => {
                const title = item.querySelector('.page-title').textContent.toLowerCase();
                const url = item.querySelector('.page-url').textContent.toLowerCase();

                if (title.includes(searchTerm) || url.includes(searchTerm)) {
                    item.style.display = 'block';
                    // Expand parent site if match found
                    const site = item.closest('.site-section');
                    const content = site.querySelector('.site-content');
                    if (searchTerm.length > 2) {
                        content.classList.add('expanded');
                        site.querySelector('.toggle-icon').classList.add('expanded');
                    }
                } else {
                    item.style.display = 'none';
                }
            });
        });
    </script>
</body>
</html>
"""

    return html

def render_hierarchy(hierarchy, site_name, level=0):
    """Recursively render hierarchical page structure"""
    html = ''

    for domain, data in hierarchy.items():
        if data['pages']:
            html += '<ul class="page-list">\n'
            for page in sorted(data['pages'], key=lambda x: x.get('Title', '')):
                title = page.get('Title', 'Untitled')
                url = page.get('URL', '#')
                depth = page.get('Depth', 'N/A')
                local_file = page.get('Local File', '')

                html += f"""
                <li class="page-item">
                    <div class="page-title">{title}</div>
                    <a href="{url}" class="page-url" target="_blank">{url}</a>
                    <div class="page-meta">Depth: {depth} | Local: {Path(local_file).name if local_file else 'N/A'}</div>
                </li>
"""
            html += '</ul>\n'

        # Render children
        if data['children']:
            for child_name, child_data in sorted(data['children'].items()):
                subsection_id = f"subsection-{site_name}-{child_name}-{level}"
                html += f"""
                <div class="subsection">
                    <div class="subsection-header" onclick="toggleSubsection('{subsection_id}')">
                        <span>▶</span> {child_name.replace('-', ' ').title()}
                    </div>
                    <div class="subsection-content" id="{subsection_id}">
"""
                html += render_hierarchy({child_name: child_data}, site_name, level + 1)
                html += """
                    </div>
                </div>
"""

    return html

def main():
    print("CAES Chatbot - Documentation Site Generator")
    print("=" * 60)

    print(f"\nReading crawl data from: {DOCS_BASE}")
    sites = read_crawl_data()

    print(f"\nFound {len(sites)} sites:")
    for name, data in sites.items():
        print(f"  - {format_site_name(name)}: {len(data['pages'])} pages")

    print("\nGenerating HTML documentation...")
    html = generate_html(sites)

    output_file = OUTPUT_DIR / 'index.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n[OK] Documentation generated: {output_file}")
    print(f"     Total pages indexed: {sum(len(s['pages']) for s in sites.values()):,}")
    print("\nTo view locally: Open index.html in a web browser")
    print("For GitHub Pages: Commit and push the GITPAGES directory")

if __name__ == '__main__':
    main()
