#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from pathlib import Path
from bs4 import BeautifulSoup

def examine_html_structure(file_path):
    """Examine the exact HTML structure."""
    print(f"=== Examining HTML structure in: {file_path} ===")
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Show first 50 lines of HTML to understand structure
    lines = content.split('\n')
    print("First 50 lines of HTML:")
    for i, line in enumerate(lines[:50]):
        print(f"{i+1:2}: {line[:100]}")
    
    print("\n" + "="*80 + "\n")
    
    # Find and examine the main structure
    main_dl = soup.find('dl')
    if main_dl:
        print("Main DL structure:")
        
        # Get the immediate children of main DL
        immediate_children = [child for child in main_dl.children if child.name]
        print(f"Immediate children of main DL: {len(immediate_children)}")
        
        for i, child in enumerate(immediate_children[:5]):  # First 5 children
            print(f"  Child {i+1}: {child.name}")
            if child.name == 'p':
                # Look inside P
                dt = child.find('dt')
                if dt:
                    h3 = dt.find('h3')
                    link = dt.find('a')
                    if h3:
                        print(f"    Contains DT with H3: '{h3.get_text(strip=True)}'")
                    elif link:
                        print(f"    Contains DT with A: '{link.get_text(strip=True)[:50]}' -> {link.get('href', '')[:50]}")
            elif child.name == 'dl':
                # Another DL - look inside it
                inner_p = child.find('p')
                if inner_p:
                    inner_dt = inner_p.find('dt')
                    if inner_dt:
                        inner_h3 = inner_dt.find('h3')
                        inner_link = inner_dt.find('a')
                        if inner_h3:
                            print(f"    Contains DL->P->DT with H3: '{inner_h3.get_text(strip=True)}'")
                        elif inner_link:
                            print(f"    Contains DL->P->DT with A: '{inner_link.get_text(strip=True)[:50]}' -> {inner_link.get('href', '')[:50]}")
        
        if len(immediate_children) > 5:
            print(f"    ... and {len(immediate_children) - 5} more children")
    
    print("\n" + "="*80 + "\n")
    
    # Look at the relationship between the main folder and its contents
    print("Analyzing folder-content relationship:")
    
    p_element = main_dl.find('p')
    if p_element:
        dt_element = p_element.find('dt')
        if dt_element:
            h3 = dt_element.find('h3')
            if h3 and h3.get_text(strip=True) == 'Bookmarks':
                print("Found main 'Bookmarks' folder")
                
                # The rest of the DL children should be the folder contents
                all_children = [child for child in main_dl.children if child.name]
                if len(all_children) > 1:
                    print(f"Main DL has {len(all_children)} children total")
                    print("Children after the first P:")
                    for i, child in enumerate(all_children[1:6]):  # Next 5 children
                        if child.name == 'dl':
                            inner_p = child.find('p')
                            if inner_p:
                                inner_dt = inner_p.find('dt')
                                if inner_dt:
                                    inner_link = inner_dt.find('a')
                                    inner_h3 = inner_dt.find('h3')
                                    if inner_link:
                                        title = inner_link.get_text(strip=True)[:50]
                                        url = inner_link.get('href', '')[:50]
                                        print(f"  Child {i+2}: DL with bookmark '{title}' -> {url}")
                                    elif inner_h3:
                                        folder = inner_h3.get_text(strip=True)
                                        print(f"  Child {i+2}: DL with folder '{folder}'")

if __name__ == "__main__":
    test_file = Path("data/ingest/bookmarks_9_27_25.html")
    if test_file.exists():
        examine_html_structure(test_file)
    else:
        print(f"Test file not found: {test_file}")