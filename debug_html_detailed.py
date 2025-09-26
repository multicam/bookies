#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from pathlib import Path
from bs4 import BeautifulSoup
from scripts.parsers.html_parser import HTMLBookmarkParser
from scripts.models.database import DatabaseManager

def debug_extract_method(file_path):
    """Debug the extract_folder_hierarchy method step by step."""
    print(f"=== Debugging extract_folder_hierarchy for: {file_path} ===")
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    main_dl = soup.find('dl')
    
    print(f"Found main DL: {main_dl is not None}")
    
    if not main_dl:
        return
    
    # Simulate the extract_folder_hierarchy logic step by step
    path = []
    bookmarks = []
    
    print(f"\n1. Looking for direct DT children of main DL...")
    dt_children = main_dl.find_all(['dt'], recursive=False)
    print(f"   Direct DT children found: {len(dt_children)}")
    
    if not dt_children:
        print(f"\n2. No direct DT children, looking inside P elements...")
        p_elements = main_dl.find_all('p', recursive=False)
        print(f"   P elements found: {len(p_elements)}")
        
        for i, p in enumerate(p_elements):
            dt_in_p = p.find_all('dt', recursive=False)
            print(f"   P element {i+1}: {len(dt_in_p)} DT children")
            dt_children.extend(dt_in_p)
        
        print(f"   Total DT children after P search: {len(dt_children)}")
    
    # Count bookmarks vs folders
    bookmark_count = 0
    folder_count = 0
    
    print(f"\n3. Processing {len(dt_children)} DT elements...")
    
    for i, child in enumerate(dt_children[:10]):  # Look at first 10 for debugging
        h3 = child.find('h3')
        link = child.find('a')
        
        if h3:
            folder_name = h3.get_text(strip=True)
            print(f"   DT {i+1}: FOLDER '{folder_name}'")
            folder_count += 1
        elif link:
            title = link.get_text(strip=True)[:50]
            url = link.get('href', '')[:50]
            print(f"   DT {i+1}: BOOKMARK '{title}' -> {url}")
            bookmark_count += 1
        else:
            print(f"   DT {i+1}: UNKNOWN (no H3 or A element)")
    
    if len(dt_children) > 10:
        print(f"   ... and {len(dt_children) - 10} more DT elements")
    
    print(f"\n4. Summary from first 10 DT elements:")
    print(f"   Folders: {folder_count}")
    print(f"   Bookmarks: {bookmark_count}")
    
    # Now test the actual parser
    print(f"\n5. Testing actual parser...")
    db = DatabaseManager()
    parser = HTMLBookmarkParser(db)
    
    # Extract using the actual method
    actual_bookmarks = parser.extract_folder_hierarchy(main_dl)
    print(f"   Parser extracted: {len(actual_bookmarks)} bookmarks")
    
    # Show some sample bookmarks
    if actual_bookmarks:
        print(f"\n6. Sample extracted bookmarks:")
        for i, bookmark in enumerate(actual_bookmarks[:5]):
            print(f"   {i+1}. {bookmark['title'][:50]} -> {bookmark['url'][:50]}")
    
    return len(actual_bookmarks)

if __name__ == "__main__":
    test_file = Path("data/ingest/bookmarks_9_27_25.html")
    if test_file.exists():
        result = debug_extract_method(test_file)
        print(f"\n=== Final Result: {result} bookmarks extracted ===")
    else:
        print(f"Test file not found: {test_file}")