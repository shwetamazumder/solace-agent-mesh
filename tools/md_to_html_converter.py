import os
import sys
import re
import markdown
from bs4 import BeautifulSoup
import uuid
import yaml


def process_callouts(content):
    """Convert callout directives to HTML"""
    pattern = r'{{<\s*callout\s+type="([^"]+)"\s*>}}(.*?){{<\s*/callout\s*>}}'
    
    def replace_callout(match):
        callout_type = match.group(1)
        callout_content = match.group(2).strip()
        # Convert markdown within the callout content
        html_content = markdown.markdown(callout_content, extensions=["extra"])
        return f'<div class="callout callout-{callout_type}">{html_content}</div>'
    
    return re.sub(pattern, replace_callout, content, flags=re.DOTALL)

def process_mermaid_blocks(content):
    """Convert mermaid code blocks to embedded mermaid diagrams"""
    pattern = r'```mermaid\n(.*?)\n```'
    
    def replace_mermaid(match):
        mermaid_code = match.group(1)
        try:
            # Return the mermaid div that will be rendered by mermaid.js
            return f'<div class="mermaid">\n{mermaid_code}\n</div>'
        except Exception as e:
            print(f"Error generating mermaid diagram: {e}")
            return f'<pre class="mermaid-error">Error generating diagram:\n{mermaid_code}</pre>'
    
    return re.sub(pattern, replace_mermaid, content, flags=re.DOTALL)

def process_params(content, params=None):
    """Process {{< param name >}} shortcodes"""
    if params is None:
        params = {}
    
    pattern = r'{{<\s*param\s+([^>]+)\s*>}}'
    
    def replace_param(match):
        param_name = match.group(1).strip()
        return params.get(param_name, f"[Parameter '{param_name}' not found]")
    
    return re.sub(pattern, replace_param, content)

def extract_front_matter(content):
    """Extract YAML front matter from markdown content"""
    front_matter_pattern = r'^---\n(.*?)\n---\n'
    match = re.match(front_matter_pattern, content, re.DOTALL)
    
    if match:
        try:
            front_matter = yaml.safe_load(match.group(1))
            remaining_content = content[match.end():]
            return front_matter, remaining_content
        except yaml.YAMLError as e:
            print(f"Warning: Failed to parse front matter: {e}")
            return None, content
    return None, content

def convert_md_to_html(md_content, params=None):
    # Extract front matter if present
    front_matter, content = extract_front_matter(md_content)
    
    # Process params, callouts and mermaid blocks before markdown conversion
    content = process_params(content, params)
    content = process_callouts(content)
    content = process_mermaid_blocks(content)
    
    # Convert markdown to HTML
    html_content = markdown.markdown(content, extensions=["extra"])
    
    # If front matter exists, add title as heading
    if front_matter and 'title' in front_matter:
        title = front_matter['title']
        title_html = f"<h1>{title}</h1>"
        html_content = title_html + html_content
    
    return html_content


def find_index_file(directory):
    """Look for index.md or _index.md in the given directory"""
    for index_name in ['index.md', '_index.md']:
        index_path = os.path.join(directory, index_name)
        if os.path.exists(index_path):
            return index_path
    return None

def process_cards_directives(content, base_dir, processed_files, root_dir):
    """Process {{< cards >}} directives in the content"""
    embedded_content = []
    
    # Find all {{< cards >}}...{{< /cards >}} blocks
    pattern = r'{{<\s*cards\s*>}}(.*?){{<\s*/cards\s*>}}'
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        cards_block = match.group(1)
        cards_html = '<div class="cards-grid">'
        
        # Find individual card definitions
        card_pattern = r'{{<\s*card\s+link="([^"]+)"\s+title="([^"]+)"\s+icon="([^"]+)"\s*>}}'
        card_matches = re.finditer(card_pattern, cards_block)
        
        for card in card_matches:
            link, title, icon = card.groups()
            # Handle absolute vs relative paths
            if link.startswith('/'):
                # Absolute path - use root_dir
                linked_path = os.path.join(root_dir, link.lstrip('/'))
            else:
                # Relative path - use base_dir
                linked_path = os.path.join(base_dir, link)
            
            # Handle directory case
            if os.path.isdir(linked_path):
                index_file = find_index_file(linked_path)
                if index_file:
                    linked_path = index_file
                else:
                    print(f"Warning: No index file found in directory: {linked_path}")
                    continue
            elif not os.path.exists(linked_path):
                # Try with .md extension if file doesn't exist
                md_path = f"{linked_path}.md"
                if os.path.exists(md_path):
                    linked_path = md_path
                
            file_id = str(uuid.uuid4())
            anchor_id = f"file-{file_id}"
            
            if os.path.exists(linked_path):
                if linked_path not in processed_files:
                    linked_content, nested_content = process_markdown_file(
                        linked_path, base_dir, processed_files, root_dir
                    )
                    processed_files.add(linked_path)
                    embedded_content.append((anchor_id, linked_content))
                    embedded_content.extend(nested_content)
                
                cards_html += f'''
                    <a href="#{anchor_id}" class="card">
                        <div class="card-icon"><i class="icon-{icon}"></i></div>
                        <div class="card-title">{title}</div>
                    </a>
                '''
            else:
                print(f"Warning: Card link not found: {linked_path}")
        
        cards_html += '</div>'
        # Replace the entire cards block with the HTML
        content = content.replace(match.group(0), cards_html)
        
    return content, embedded_content

def process_markdown_file(file_path, base_url, processed_files, root_dir, params=None):
    if file_path in processed_files:
        return "", []

    try:
        with open(file_path, "r") as file:
            content = file.read()
            
        # If front matter contains params, add them to the params dict
        front_matter, _ = extract_front_matter(content)
        if front_matter and 'params' in front_matter:
            if params is None:
                params = {}
            params.update(front_matter['params'])
    except IOError as e:
        print(f"Error opening file {file_path}: {e}")
        sys.exit(1)

    # Process cards directives first
    content, cards_embedded = process_cards_directives(
        content, 
        os.path.dirname(file_path), 
        processed_files,
        root_dir
    )

    html_content = convert_md_to_html(content, params)
    soup = BeautifulSoup(html_content, "html.parser")
    embedded_content = list(cards_embedded)  # Start with cards content

    for link in soup.find_all("a"):
        href = link.get("href")
        if not href:
            continue
            
        linked_path = os.path.join(os.path.dirname(file_path), href)
        
        # Handle directory case
        if os.path.isdir(linked_path):
            index_file = find_index_file(linked_path)
            if index_file:
                linked_path = index_file
                
        if linked_path.endswith(".md") and os.path.exists(linked_path):
            file_id = str(uuid.uuid4())
            anchor_id = f"file-{file_id}"
            link["href"] = f"#{anchor_id}"
            if linked_path not in processed_files:
                linked_content, nested_content = process_markdown_file(
                    linked_path, base_url, processed_files, root_dir, params
                )
                processed_files.add(linked_path)
                embedded_content.append((anchor_id, linked_content))
                embedded_content.extend(nested_content)
        elif href.endswith(".md"):
            print(f"Warning: Linked file not found: {linked_path}")

    return str(soup), embedded_content


def create_html_page(main_content, embedded_content):
    embedded_html = ""
    for anchor_id, content in embedded_content:
        embedded_html += f'<div id="{anchor_id}">{content}</div>'

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Markdown Documentation</title>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{ startOnLoad: true }});
        </script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 4px;
                border-radius: 4px;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
            }}
            img {{
                max-width: 1000px;
                height: auto;
            }}
            .mermaid-diagram {{
                display: block;
                margin: 20px auto;
            }}
            .mermaid-error {{
                color: red;
                background-color: #ffebee;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
            }}
            .cards-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1rem;
                margin: 1rem 0;
            }}
            .card {{
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 1.5rem;
                border: 1px solid #e2e8f0;
                border-radius: 0.5rem;
                text-decoration: none;
                color: inherit;
                transition: transform 0.2s;
            }}
            .card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }}
            .card-icon {{
                font-size: 1.5rem;
                margin-bottom: 0.5rem;
            }}
            .card-title {{
                font-weight: 600;
                text-align: center;
            }}
            /* Callouts */
            .callout {{
                padding: 1rem;
                margin: 1rem 0;
                border-left: 4px solid;
                border-radius: 4px;
            }}
            .callout-warning {{
                background-color: #fff3e0;
                border-color: #ff9800;
            }}
            .callout-info {{
                background-color: #e3f2fd;
                border-color: #2196f3;
            }}
            .callout-tip {{
                background-color: #e8f5e9;
                border-color: #4caf50;
            }}
            .callout-danger {{
                background-color: #ffebee;
                border-color: #f44336;
            }}
            /* Basic icon font classes */
            .icon-template::before {{ content: "📐"; }}
            .icon-code::before {{ content: "💻"; }}
            .icon-server::before {{ content: "🖥️"; }}
            .icon-user::before {{ content: "👤"; }}
            .icon-pencil::before {{ content: "✏️"; }}
        </style>
    </head>
    <body>
        <div id="main-content">
            {main_content}
        </div>
        <hr>
        <div id="embedded-content">
            {embedded_html}
        </div>
    </body>
    </html>
    """


def main(index_file):
    if not os.path.exists(index_file):
        print(f"Error: File not found: {index_file}")
        sys.exit(1)

    # Determine root directory (parent of the directory containing index_file)
    base_url = os.path.dirname(os.path.abspath(index_file))
    root_dir = os.path.dirname(base_url)
    
    processed_files = set()
    main_content, embedded_content = process_markdown_file(
        index_file, base_url, processed_files, root_dir
    )
    html_page = create_html_page(main_content, embedded_content)

    output_file = os.path.splitext(index_file)[0] + ".html"
    with open(output_file, "w") as file:
        file.write(html_page)

    print(f"HTML file created: {output_file}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Convert markdown to HTML')
    parser.add_argument('index_file', help='Path to the index markdown file')
    args = parser.parse_args()

    main(args.index_file)
