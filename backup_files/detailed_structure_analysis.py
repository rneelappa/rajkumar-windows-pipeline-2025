#!/usr/bin/env python3
"""
Detailed Structure Analysis for Tally XML
Provides a comprehensive analysis of the XML structure focusing on ledger and inventory entries.
"""

import re
from typing import Dict, List, Any
from collections import defaultdict


def analyze_tally_xml_structure(xml_file_path: str) -> Dict[str, Any]:
    """Analyze the structure of Tally XML file."""
    
    with open(xml_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Clean content
    content = re.sub(r'<\?xml[^>]*\?>', '', content)
    content = re.sub(r'<TALLYMESSAGE[^>]*>', '', content)
    content = re.sub(r'</TALLYMESSAGE>', '', content)
    content = re.sub(r'<ENVELOPE[^>]*>', '', content)
    content = re.sub(r'</ENVELOPE>', '', content)
    
    # Split into vouchers
    voucher_pattern = r'<VOUCHER_AMOUNT>'
    matches = list(re.finditer(voucher_pattern, content))
    
    vouchers = []
    for i, match in enumerate(matches):
        start_pos = match.start()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        voucher_content = content[start_pos:end_pos].strip()
        vouchers.append(voucher_content)
    
    # Analyze structure
    analysis = {
        'total_vouchers': len(vouchers),
        'voucher_structure': [],
        'ledger_entry_patterns': defaultdict(int),
        'inventory_entry_patterns': defaultdict(int),
        'vouchers_with_inventory': 0,
        'vouchers_without_inventory': 0,
        'sample_vouchers': []
    }
    
    for i, voucher_content in enumerate(vouchers[:10]):  # Analyze first 10 vouchers in detail
        voucher_analysis = analyze_single_voucher(voucher_content, i + 1)
        analysis['voucher_structure'].append(voucher_analysis)
        analysis['sample_vouchers'].append(voucher_analysis)
        
        # Count patterns
        if voucher_analysis['has_inventory_item']:
            analysis['vouchers_with_inventory'] += 1
        else:
            analysis['vouchers_without_inventory'] += 1
    
    # Count patterns across all vouchers
    for voucher_content in vouchers:
        ledger_count = len(re.findall(r'<TRN_LEDGERENTRIES_LEDGER_NAME>', voucher_content))
        inventory_count = len(re.findall(r'<TRN_INVENTORYENTRIES_STOCKITEM_NAME>', voucher_content))
        
        analysis['ledger_entry_patterns'][f'{ledger_count}_ledger_entries'] += 1
        analysis['inventory_entry_patterns'][f'{inventory_count}_inventory_entries'] += 1
    
    return analysis


def analyze_single_voucher(voucher_content: str, voucher_number: int) -> Dict[str, Any]:
    """Analyze a single voucher."""
    
    # Extract basic info
    voucher_id = extract_tag_value(voucher_content, 'VOUCHER_ID')
    voucher_amount = extract_tag_value(voucher_content, 'VOUCHER_AMOUNT')
    voucher_date = extract_tag_value(voucher_content, 'VOUCHER_DATE')
    voucher_type = extract_tag_value(voucher_content, 'VOUCHER_VOUCHER_TYPE')
    voucher_narration = extract_tag_value(voucher_content, 'VOUCHER_NARRATION')
    
    # Extract ledger entries
    ledger_entries = extract_ledger_entries(voucher_content)
    
    # Extract inventory entries
    inventory_entries = extract_inventory_entries(voucher_content)
    
    # Check for accounting ledger entries
    accounting_ledger_entries = extract_accounting_ledger_entries(voucher_content)
    
    return {
        'voucher_number': voucher_number,
        'voucher_id': voucher_id,
        'voucher_amount': voucher_amount,
        'voucher_date': voucher_date,
        'voucher_type': voucher_type,
        'voucher_narration': voucher_narration,
        'ledger_entries': ledger_entries,
        'inventory_entries': inventory_entries,
        'accounting_ledger_entries': accounting_ledger_entries,
        'has_inventory_item': any(entry.get('stockitem_name') for entry in inventory_entries),
        'total_ledger_entries': len(ledger_entries),
        'total_inventory_entries': len(inventory_entries),
        'total_accounting_ledger_entries': len(accounting_ledger_entries)
    }


def extract_tag_value(content: str, tag_name: str) -> str:
    """Extract value from a specific tag."""
    pattern = f'<{tag_name}>([^<]*)</{tag_name}>'
    match = re.search(pattern, content)
    return match.group(1).strip() if match else ''


def extract_ledger_entries(voucher_content: str) -> List[Dict[str, str]]:
    """Extract all ledger entries from voucher."""
    entries = []
    
    # Find all ledger-related tags
    ledger_tags = [
        'TRN_LEDGERENTRIES_AMOUNT',
        'TRN_LEDGERENTRIES_ID', 
        'TRN_LEDGERENTRIES_IS_DEBIT',
        'TRN_LEDGERENTRIES_LEDGER_NAME'
    ]
    
    entry = {}
    for tag in ledger_tags:
        value = extract_tag_value(voucher_content, tag)
        if value:
            entry[tag.replace('TRN_LEDGERENTRIES_', '').lower()] = value
    
    if entry:
        entries.append(entry)
    
    return entries


def extract_inventory_entries(voucher_content: str) -> List[Dict[str, str]]:
    """Extract all inventory entries from voucher."""
    entries = []
    
    # Find all inventory-related tags
    inventory_tags = [
        'TRN_INVENTORYENTRIES_AMOUNT',
        'TRN_INVENTORYENTRIES_ID',
        'TRN_INVENTORYENTRIES_QUANTITY',
        'TRN_INVENTORYENTRIES_RATE',
        'TRN_INVENTORYENTRIES_STOCKITEM_NAME'
    ]
    
    entry = {}
    for tag in inventory_tags:
        value = extract_tag_value(voucher_content, tag)
        if value:
            entry[tag.replace('TRN_INVENTORYENTRIES_', '').lower()] = value
    
    if entry:
        entries.append(entry)
    
    return entries


def extract_accounting_ledger_entries(voucher_content: str) -> List[Dict[str, str]]:
    """Extract all accounting ledger entries from voucher."""
    entries = []
    
    # Find all accounting ledger-related tags
    accounting_tags = [
        'TRN_INVENTORYENTRIES_ACCOUNTINGLEDGER_NAME',
        'TRN_INVENTORYENTRIES_ACCOUNTINGLEDGER_AMOUNT',
        'TRN_INVENTORYENTRIES_ACCOUNTINGLEDGER_ISDEEMEDPOSITIVE'
    ]
    
    entry = {}
    for tag in accounting_tags:
        value = extract_tag_value(voucher_content, tag)
        if value:
            entry[tag.replace('TRN_INVENTORYENTRIES_ACCOUNTINGLEDGER_', '').lower()] = value
    
    if entry:
        entries.append(entry)
    
    return entries


def print_detailed_analysis(analysis: Dict[str, Any]) -> None:
    """Print detailed analysis results."""
    
    print("=" * 80)
    print("DETAILED TALLY XML STRUCTURE ANALYSIS")
    print("=" * 80)
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"  Total Vouchers: {analysis['total_vouchers']}")
    print(f"  Vouchers with Inventory Items: {analysis['vouchers_with_inventory']}")
    print(f"  Vouchers without Inventory Items: {analysis['vouchers_without_inventory']}")
    
    print(f"\n🏷️  LEDGER ENTRY PATTERNS:")
    for pattern, count in analysis['ledger_entry_patterns'].items():
        print(f"  {pattern}: {count} vouchers")
    
    print(f"\n📦 INVENTORY ENTRY PATTERNS:")
    for pattern, count in analysis['inventory_entry_patterns'].items():
        print(f"  {pattern}: {count} vouchers")
    
    print(f"\n🔍 SAMPLE VOUCHER STRUCTURES:")
    print("-" * 80)
    
    for voucher in analysis['sample_vouchers']:
        print(f"\nVoucher #{voucher['voucher_number']}:")
        print(f"  ID: {voucher['voucher_id']}")
        print(f"  Amount: {voucher['voucher_amount']}")
        print(f"  Date: {voucher['voucher_date']}")
        print(f"  Type: {voucher['voucher_type']}")
        print(f"  Narration: {voucher['voucher_narration'][:50]}...")
        
        print(f"  Ledger Entries ({voucher['total_ledger_entries']}):")
        for entry in voucher['ledger_entries']:
            print(f"    - Ledger Name: {entry.get('ledger_name', 'N/A')}")
            print(f"    - Amount: {entry.get('amount', 'N/A')}")
            print(f"    - ID: {entry.get('id', 'N/A')}")
        
        print(f"  Inventory Entries ({voucher['total_inventory_entries']}):")
        for entry in voucher['inventory_entries']:
            print(f"    - Stock Item: {entry.get('stockitem_name', 'N/A')}")
            print(f"    - Amount: {entry.get('amount', 'N/A')}")
            print(f"    - Quantity: {entry.get('quantity', 'N/A')}")
            print(f"    - Rate: {entry.get('rate', 'N/A')}")
        
        print(f"  Accounting Ledger Entries ({voucher['total_accounting_ledger_entries']}):")
        for entry in voucher['accounting_ledger_entries']:
            print(f"    - Name: {entry.get('name', 'N/A')}")
            print(f"    - Amount: {entry.get('amount', 'N/A')}")
            print(f"    - Is Positive: {entry.get('isdeemedpositive', 'N/A')}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python3 detailed_structure_analysis.py <xml_file>")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    
    try:
        analysis = analyze_tally_xml_structure(xml_file)
        print_detailed_analysis(analysis)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
