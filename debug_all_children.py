#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from pathlib import Path
from bs4 import BeautifulSoup

def examine_all_dl_children(file_path):
    """Examine all children of the main DL."""
    print(f"=== Examining all children of main DL in: {file_path} ===")
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    main_dl = soup.find('dl')
    
    if not main_dl:
        print("No main DL found!")
        return
    
    # Get ALL children of the main DL
    all_children = list(main_dl.children)
    named_children = [child for child in all_children if child.name]
    
    print(f"Main DL has {len(named_children)} named children")
    
    total_dt_count = 0
    
    # Show first 10 children in detail
    for i, child in enumerate(named_children[:10]):
        print(f"\nChild {i+1}: {child.name}")
        
        if child.name == 'p':
            # Look for DT elements in this P
            dt_elements = child.find_all('dt', recursive=False)
            print(f"  Contains {len(dt_elements)} DT elements:")
            for j, dt in enumerate(dt_elements):
                h3 = dt.find('h3')
                link = dt.find('a')
                if h3:
                    folder_name = h3.get_text(strip=True)
                    print(f"    DT {j+1}: FOLDER '{folder_name}'")
                elif link:
                    title = link.get_text(strip=True)[:50]
                    url = link.get('href', '')[:50]
                    print(f"    DT {j+1}: BOOKMARK '{title}' -> {url}")
                else:
                    print(f"    DT {j+1}: UNKNOWN")
            total_dt_count += len(dt_elements)
        
        elif child.name == 'dl':
            # Look for DT elements in this DL
            dt_elements_direct = child.find_all('dt', recursive=False)
            p_elements = child.find_all('p', recursive=False)
            
            dt_in_p = 0
            for p in p_elements:
                dt_in_p += len(p.find_all('dt', recursive=False))
            
            print(f"  DL contains {len(dt_elements_direct)} direct DT, {len(p_elements)} P elements, {dt_in_p} DT in Ps")
            total_dt_count += len(dt_elements_direct) + dt_in_p
    
    if len(named_children) > 10:
        print(f"\n... and {len(named_children) - 10} more children")
        
        # Count DTs in remaining children
        for child in named_children[10:]:
            if child.name == 'p':
                dt_elements = child.find_all('dt', recursive=False)
                total_dt_count += len(dt_elements)
            elif child.name == 'dl':
                dt_elements_direct = child.find_all('dt', recursive=False)
                p_elements = child.find_all('p', recursive=False)
                dt_in_p = 0
                for p in p_elements:
                    dt_in_p += len(p.find_all('dt', recursive=False))
                total_dt_count += len(dt_elements_direct) + dt_in_p
    
    print(f"\n=== TOTAL DT ELEMENTS IN MAIN DL: {total_dt_count} ===")
    
    # Now test the parser with the improved logic
    from scripts.parsers.html_parser import HTMLBookmarkParser
    from scripts.models.database import DatabaseManager
    
    db = DatabaseManager()
    parser = HTMLBookmarkParser(db)
    
    # Get all DT elements using parser's improved logic
    dt_children = []
    dt_children.extend(main_dl.find_all(['dt'], recursive=False))
    for p in main_dl.find_all('p', recursive=False):
        dt_children.extend(p.find_all('dt', recursive=False))
    
    print(f"\n=== PARSER LOGIC FINDS: {len(dt_children)} DT ELEMENTS ===")
    
    # Test actual extraction
    bookmarks = parser.extract_folder_hierarchy(main_dl)
    print(f"\n=== PARSER EXTRACTS: {len(bookmarks)} BOOKMARKS ===")
    
    if bookmarks:
        print("\nSample extracted bookmarks:")
        for i, bookmark in enumerate(bookmarks[:10]):
            print(f"  {i+1}. {bookmark['title'][:60]} -> {bookmark['url'][:60]}")

if __name__ == "__main__":
    test_file = Path("data/ingest/bookmarks_9_27_25.html")
    if test_file.exists():
        examine_all_dl_children(test_file)
    else:
        print(f"Test file not found: {test_file}")