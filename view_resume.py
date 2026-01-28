#!/usr/bin/env python3
"""
Simple script to view a markdown file in your browser.
Usage: python view_resume.py [path/to/resume.md]
"""

import sys
import webbrowser
import tempfile
from pathlib import Path

def markdown_to_html(md_content):
    """Convert markdown to HTML with nice styling."""
    
    # Simple markdown to HTML conversion
    html = md_content
    
    # Headers
    html = html.replace('# ', '<h1>').replace('\n## ', '</h1>\n<h2>').replace('\n### ', '</h2>\n<h3>').replace('\n#### ', '</h3>\n<h4>')
    
    # Bold
    import re
    html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html)
    
    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Line breaks
    html = html.replace('\n\n', '</p><p>')
    html = html.replace('\n- ', '<li>').replace('\n  - ', '<li style="margin-left: 20px;">')
    
    # Wrap in paragraphs
    html = '<p>' + html + '</p>'
    
    # Close any open headers
    html = html.replace('<h1>', '<h1>').replace('\n<h2>', '</h1>\n<h2>')
    html = html.replace('<h2>', '<h2>').replace('\n<h3>', '</h2>\n<h3>')
    html = html.replace('<h3>', '<h3>').replace('\n<h4>', '</h3>\n<h4>')
    html = html.replace('<h4>', '<h4>').replace('\n<p>', '</h4>\n<p>')
    
    return html

def create_html_page(md_content):
    """Create a full HTML page with styling."""
    
    body_content = markdown_to_html(md_content)
    
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume - Rafael Valle</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            color: #333;
            background: #fff;
        }}
        h1 {{
            font-size: 2.5em;
            margin-bottom: 0.2em;
            color: #1a1a1a;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
        }}
        h2 {{
            font-size: 1.8em;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            color: #0066cc;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 5px;
        }}
        h3 {{
            font-size: 1.4em;
            margin-top: 1.2em;
            margin-bottom: 0.4em;
            color: #333;
        }}
        h4 {{
            font-size: 1.1em;
            margin-top: 1em;
            margin-bottom: 0.3em;
            color: #555;
            font-weight: 600;
        }}
        p {{
            margin: 0.8em 0;
        }}
        strong {{
            color: #1a1a1a;
            font-weight: 600;
        }}
        a {{
            color: #0066cc;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        li {{
            margin: 0.5em 0;
            list-style-type: none;
        }}
        li:before {{
            content: "• ";
            color: #0066cc;
            font-weight: bold;
            margin-right: 8px;
        }}
        hr {{
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 30px 0;
        }}
        @media print {{
            body {{
                max-width: 100%;
                margin: 0;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    {body_content}
</body>
</html>"""
    
    return html_template

def main():
    # Get the markdown file path
    if len(sys.argv) > 1:
        md_file = Path(sys.argv[1])
    else:
        # Default to resume_updated.md in current directory or outputs
        if Path('/mnt/user-data/outputs/resume_updated.md').exists():
            md_file = Path('/mnt/user-data/outputs/resume_updated.md')
        elif Path('resume_updated.md').exists():
            md_file = Path('resume_updated.md')
        elif Path('resume.md').exists():
            md_file = Path('resume.md')
        else:
            print("Error: No markdown file found.")
            print("Usage: python view_resume.py [path/to/resume.md]")
            sys.exit(1)
    
    if not md_file.exists():
        print(f"Error: File not found: {md_file}")
        sys.exit(1)
    
    # Read the markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Create HTML
    html_content = create_html_page(md_content)
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_path = f.name
    
    print(f"Opening {md_file.name} in your browser...")
    print(f"Temporary HTML file: {temp_path}")
    
    # Open in browser
    webbrowser.open(f'file://{temp_path}')

if __name__ == '__main__':
    main()
