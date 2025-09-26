#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from pathlib import Path
from bs4 import BeautifulSoup

def examine_folder_structure(file_path):
    """Examine the folder structure in detail."""
    print(f"=== Examining folder structure in: {file_path} ===")
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    main_dl = soup.find('dl')
    
    # Find the first P element and its DT child
    p_element = main_dl.find('p')
    if p_element:
        dt_element = p_element.find('dt')
        if dt_element:
            print(f"Found DT element in P:")
            h3 = dt_element.find('h3')
            if h3:
                folder_name = h3.get_text(strip=True)
                print(f"  Folder name: '{folder_name}'")
                
                # Now let's see what comes after this DT
                print(f"\n  Looking for DL siblings...")
                
                # Method 1: Next sibling of the DT
                next_sibling = dt_element.find_next_sibling()
                if next_sibling:
                    print(f"  DT's next sibling: {next_sibling.name}")
                    if next_sibling.name == 'dl':
                        dl_children = next_sibling.find_all('dt', recursive=False)
                        print(f"    This DL has {len(dl_children)} direct DT children")
                        
                        # Look inside its P elements too
                        p_children = next_sibling.find_all('p', recursive=False)
                        total_dt_in_p = 0
                        for p_child in p_children:
                            dt_in_p = p_child.find_all('dt', recursive=False)
                            total_dt_in_p += len(dt_in_p)
                        print(f"    This DL has {len(p_children)} P children with {total_dt_in_p} total DT elements")
                else:
                    print(f"  No next sibling found for DT")
                
                # Method 2: Look for DL inside the DT itself
                inner_dl = dt_element.find('dl')
                if inner_dl:
                    print(f"\n  Found DL inside DT:")
                    inner_dt_direct = inner_dl.find_all('dt', recursive=False)
                    print(f"    Inner DL has {len(inner_dt_direct)} direct DT children")
                    
                    inner_p_children = inner_dl.find_all('p', recursive=False)
                    total_inner_dt_in_p = 0
                    for p_child in inner_p_children:
                        dt_in_p = p_child.find_all('dt', recursive=False)
                        total_inner_dt_in_p += len(dt_in_p)
                    print(f"    Inner DL has {len(inner_p_children)} P children with {total_inner_dt_in_p} total DT elements")
                
                # Method 3: Look at all DL elements in the entire document
                print(f"\n  All DL elements in document:")
                all_dls = soup.find_all('dl')
                for i, dl in enumerate(all_dls):
                    direct_dt = dl.find_all('dt', recursive=False)
                    p_elements = dl.find_all('p', recursive=False)
                    dt_in_ps = 0
                    for p in p_elements:
                        dt_in_ps += len(p.find_all('dt', recursive=False))
                    
                    print(f"    DL {i+1}: {len(direct_dt)} direct DT, {len(p_elements)} P elements, {dt_in_ps} DT in Ps")
                    
                    if i == 0:  # Show structure of first DL
                        print(f"      First DL immediate children: {[child.name for child in dl.children if child.name]}")

if __name__ == "__main__":
    test_file = Path("data/ingest/bookmarks_9_27_25.html")
    if test_file.exists():
        examine_folder_structure(test_file)
    else:
        print(f"Test file not found: {test_file}")