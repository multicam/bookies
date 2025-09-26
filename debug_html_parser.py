#!/usr/bin/env python3

import sys
sys.path.insert(0, 'scripts')

from pathlib import Path
from bs4 import BeautifulSoup
from models.database import DatabaseManager
from parsers.html_parser import HTMLBookmarkParser

# Test with the specific file we examined
test_file = Path("data/ingest/bookmarks_9_27_25.html")

print(f"Testing HTML parser with: {test_file}")
print(f"File exists: {test_file.exists()}")

if test_file.exists():
    # Read and parse the file manually first
    with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    print(f"File size: {len(content)} characters")
    
    soup = BeautifulSoup(content, 'html.parser')
    main_dl = soup.find('dl')
    print(f"Found main DL element: {main_dl is not None}")
    
    if main_dl:
        # Test the extraction manually
        print(f"Main DL has {len(main_dl.find_all('dt', recursive=False))} direct DT children")
        
        # Check what the main DL actually contains
        print("\nInvestigating main DL structure:")
        direct_children = [child for child in main_dl.children if child.name]
        print(f"Direct named children: {[child.name for child in direct_children]}")
        
        # Check all DT elements recursively
        all_dts = main_dl.find_all('dt')
        print(f"All DT elements (recursive): {len(all_dts)}")
        
        # Investigate the P element
        p_element = main_dl.find('p')
        if p_element:
            print(f"\nFound P element with {len(p_element.find_all('dt'))} DT children")
            print(f"P element next siblings: {[sibling.name for sibling in p_element.next_siblings if sibling.name]}")
            
            # Check what comes after the P
            next_sibling = p_element.find_next_sibling()
            if next_sibling:
                print(f"Next sibling after P: {next_sibling.name}")
                if next_sibling.name == 'dt':
                    print("Found DT sibling after P!")
                    
        # Let's try a different approach - find all DT elements that are direct children of any DL
        print("\nTrying alternative approach...")
        all_dls = soup.find_all('dl')
        print(f"Total DL elements: {len(all_dls)}")
        
        # Check the structure of nested DLs
        for i, dl in enumerate(all_dls[:3]):
            direct_dts = dl.find_all('dt', recursive=False)
            print(f"DL {i+1}: {len(direct_dts)} direct DT children")
        
        # Look for actual bookmarks
        all_links = soup.find_all('a')
        print(f"Total A tags found: {len(all_links)}")
        
        valid_links = []
        for link in all_links[:5]:  # Check first 5
            href = link.get('href', '')
            if href and not href.startswith('javascript:') and not href.startswith('data:'):
                valid_links.append({
                    'href': href[:50] + '...' if len(href) > 50 else href,
                    'title': link.get_text(strip=True)[:50]
                })
        
        print("Sample valid links found:")
        for i, link in enumerate(valid_links):
            print(f"  {i+1}. {link['title']} -> {link['href']}")
        
        # Test the actual parser
        db = DatabaseManager('database/bookmarks.db')
        parser = HTMLBookmarkParser(db)
        
        print("\nTesting extract_folder_hierarchy method:")
        bookmarks = parser.extract_folder_hierarchy(main_dl)
        print(f"Parser extracted {len(bookmarks)} bookmarks")
        
        if len(bookmarks) > 0:
            print("Sample extracted bookmarks:")
            for i, bookmark in enumerate(bookmarks[:3]):
                print(f"  {i+1}. {bookmark['title'][:50]} -> {bookmark['url'][:50]}")
        else:
            print("No bookmarks extracted! Investigating...")
            
            # Debug the parsing logic step by step
            dt_children = main_dl.find_all(['dt'], recursive=False)
            print(f"Direct DT children: {len(dt_children)}")
            
            for i, child in enumerate(dt_children[:3]):
                print(f"\nDT child {i+1}:")
                h3 = child.find('h3')
                link = child.find('a')
                print(f"  Has H3: {h3 is not None}")
                print(f"  Has A: {link is not None}")
                
                if h3:
                    folder_name = h3.get_text(strip=True)
                    print(f"  H3 text: '{folder_name}'")
                    print(f"  Skipping folder? {folder_name.lower() in ['bookmarks', 'bookmarks bar']}")
                    
                    # Test sibling search
                    dl_sibling = child.find_next_sibling('dl')
                    dl_within = child.find('dl')
                    print(f"  Next DL sibling: {dl_sibling is not None}")
                    print(f"  DL within: {dl_within is not None}")
                    
                if link:
                    href = link.get('href', '')
                    title = link.get_text(strip=True)
                    print(f"  Link URL: {href[:50]}")
                    print(f"  Link title: {title[:50]}")
                    print(f"  Valid URL? {bool(href and not href.startswith('javascript:') and not href.startswith('data:'))}")

else:
    print("Test file not found!")