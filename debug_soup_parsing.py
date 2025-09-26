#!/usr/bin/env python3

from pathlib import Path
from bs4 import BeautifulSoup

def debug_soup_parsing(file_path):
    """Debug how BeautifulSoup is parsing the HTML."""
    print(f"=== Debugging BeautifulSoup parsing of: {file_path} ===")
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Show raw HTML around the problematic area
    lines = content.split('\n')
    print("Raw HTML lines 8-20:")
    for i, line in enumerate(lines[7:20]):
        print(f"{i+8:2}: {line}")
    
    print("\n" + "="*60 + "\n")
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    main_dl = soup.find('dl')
    
    print("BeautifulSoup parsed structure:")
    print(f"Main DL found: {main_dl is not None}")
    
    if main_dl:
        # Print the parsed structure
        print(f"Main DL tag: {main_dl.name}")
        print(f"Main DL attributes: {main_dl.attrs}")
        
        children = list(main_dl.children)
        named_children = [child for child in children if child.name]
        text_children = [child.strip() for child in children if isinstance(child, str) and child.strip()]
        
        print(f"Total children: {len(children)}")
        print(f"Named children: {len(named_children)}")
        print(f"Text children: {len(text_children)}")
        
        print("\nFirst few children (showing type and content):")
        for i, child in enumerate(children[:10]):
            if hasattr(child, 'name'):  # Tag
                if child.name == 'p':
                    dt_count = len(child.find_all('dt', recursive=False))
                    print(f"  {i+1}. TAG: {child.name} (contains {dt_count} DT elements)")
                elif child.name == 'dl':
                    dt_count = len(child.find_all('dt'))  # recursive for debugging
                    print(f"  {i+1}. TAG: {child.name} (contains {dt_count} total DT elements)")
                else:
                    print(f"  {i+1}. TAG: {child.name}")
            else:  # String/text
                text = str(child).strip()[:50]
                if text:
                    print(f"  {i+1}. TEXT: '{text}'")
                else:
                    print(f"  {i+1}. WHITESPACE")
        
        if len(children) > 10:
            print(f"  ... and {len(children) - 10} more children")
    
    # Let's also try to find all DT elements in the document
    all_dt_elements = soup.find_all('dt')
    print(f"\n=== TOTAL DT ELEMENTS IN ENTIRE DOCUMENT: {len(all_dt_elements)} ===")
    
    # Show first 10 DT elements
    print("\nFirst 10 DT elements in document:")
    for i, dt in enumerate(all_dt_elements[:10]):
        h3 = dt.find('h3')
        link = dt.find('a')
        parent_tag = dt.parent.name if dt.parent else "None"
        
        if h3:
            folder_name = h3.get_text(strip=True)
            print(f"  {i+1}. FOLDER '{folder_name}' (parent: {parent_tag})")
        elif link:
            title = link.get_text(strip=True)[:50]
            url = link.get('href', '')[:40]
            print(f"  {i+1}. BOOKMARK '{title}' -> {url} (parent: {parent_tag})")
        else:
            print(f"  {i+1}. UNKNOWN DT (parent: {parent_tag})")
    
    # Check if the DT elements are where we expect them
    main_dl_descendants = main_dl.find_all('dt') if main_dl else []
    print(f"\n=== DT ELEMENTS WITHIN MAIN DL (recursive): {len(main_dl_descendants)} ===")

if __name__ == "__main__":
    test_file = Path("data/ingest/bookmarks_9_27_25.html")
    if test_file.exists():
        debug_soup_parsing(test_file)
    else:
        print(f"Test file not found: {test_file}")