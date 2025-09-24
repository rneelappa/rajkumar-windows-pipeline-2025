#!/usr/bin/env python3
"""
Detailed Entry Analyzer for Tally XML
Analyzes voucher entries to detect multiple ledger or inventory entries per voucher.
"""

import re
from typing import Dict, List, Any
from collections import defaultdict


def analyze_voucher_entries(xml_file_path: str) -> Dict[str, Any]:
    """Analyze voucher entries in detail."""
    
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
    
    # Analyze each voucher
    analysis = {
        'total_vouchers': len(vouchers),
        'vouchers_with_multiple_ledger_entries': [],
        'vouchers_with_multiple_inventory_entries': [],
        'vouchers_with_multiple_accounting_entries': [],
        'entry_patterns': defaultdict(int),
        'sample_vouchers': []
    }
    
    for i, voucher_content in enumerate(vouchers[:20]):  # Analyze first 20 in detail
        voucher_analysis = analyze_single_voucher_detailed(voucher_content, i + 1)
        analysis['sample_vouchers'].append(voucher_analysis)
        
        # Count patterns
        ledger_count = len(re.findall(r'<TRN_LEDGERENTRIES_LEDGER_NAME>', voucher_content))
        inventory_count = len(re.findall(r'<TRN_INVENTORYENTRIES_STOCKITEM_NAME>', voucher_content))
        accounting_count = len(re.findall(r'<TRN_INVENTORYENTRIES_ACCOUNTINGLEDGER_NAME>', voucher_content))
        
        pattern_key = f"L:{ledger_count}_I:{inventory_count}_A:{accounting_count}"
        analysis['entry_patterns'][pattern_key] += 1
        
        if ledger_count > 1:
            analysis['vouchers_with_multiple_ledger_entries'].append({
                'voucher_number': i + 1,
                'ledger_count': ledger_count,
                'content_preview': voucher_content[:200] + "..."
            })
        
        if inventory_count > 1:
            analysis['vouchers_with_multiple_inventory_entries'].append({
                'voucher_number': i + 1,
                'inventory_count': inventory_count,
                'content_preview': voucher_content[:200] + "..."
            })
        
        if accounting_count > 1:
            analysis['vouchers_with_multiple_accounting_entries'].append({
                'voucher_number': i + 1,
                'accounting_count': accounting_count,
                'content_preview': voucher_content[:200] + "..."
            })
    
    # Analyze all vouchers for patterns
    for voucher_content in vouchers:
        ledger_count = len(re.findall(r'<TRN_LEDGERENTRIES_LEDGER_NAME>', voucher_content))
        inventory_count = len(re.findall(r'<TRN_INVENTORYENTRIES_STOCKITEM_NAME>', voucher_content))
        accounting_count = len(re.findall(r'<TRN_INVENTORYENTRIES_ACCOUNTINGLEDGER_NAME>', voucher_content))
        
        pattern_key = f"L:{ledger_count}_I:{inventory_count}_A:{accounting_count}"
        analysis['entry_patterns'][pattern_key] += 1
    
    return analysis


def analyze_single_voucher_detailed(voucher_content: str, voucher_number: int) -> Dict[str, Any]:
    """Analyze a single voucher in detail."""
    
    # Extract voucher ID
    voucher_id_match = re.search(r'<VOUCHER_ID>([^<]*)</VOUCHER_ID>', voucher_content)
    voucher_id = voucher_id_match.group(1) if voucher_id_match else ''
    
    # Count different types of entries
    ledger_entries = re.findall(r'<TRN_LEDGERENTRIES_LEDGER_NAME>([^<]*)</TRN_LEDGERENTRIES_LEDGER_NAME>', voucher_content)
    inventory_entries = re.findall(r'<TRN_INVENTORYENTRIES_STOCKITEM_NAME>([^<]*)</TRN_INVENTORYENTRIES_STOCKITEM_NAME>', voucher_content)
    accounting_entries = re.findall(r'<TRN_INVENTORYENTRIES_ACCOUNTINGLEDGER_NAME>([^<]*)</TRN_INVENTORYENTRIES_ACCOUNTINGLEDGER_NAME>', voucher_content)
    
    # Extract voucher amount
    voucher_amount_match = re.search(r'<VOUCHER_AMOUNT>([^<]*)</VOUCHER_AMOUNT>', voucher_content)
    voucher_amount = voucher_amount_match.group(1) if voucher_amount_match else ''
    
    # Extract voucher type
    voucher_type_match = re.search(r'<VOUCHER_VOUCHER_TYPE>([^<]*)</VOUCHER_VOUCHER_TYPE>', voucher_content)
    voucher_type = voucher_type_match.group(1) if voucher_type_match else ''
    
    return {
        'voucher_number': voucher_number,
        'voucher_id': voucher_id,
        'voucher_amount': voucher_amount,
        'voucher_type': voucher_type,
        'ledger_entries': ledger_entries,
        'inventory_entries': inventory_entries,
        'accounting_entries': accounting_entries,
        'ledger_count': len(ledger_entries),
        'inventory_count': len(inventory_entries),
        'accounting_count': len(accounting_entries),
        'has_multiple_ledger': len(ledger_entries) > 1,
        'has_multiple_inventory': len(inventory_entries) > 1,
        'has_multiple_accounting': len(accounting_entries) > 1
    }


def print_detailed_analysis(analysis: Dict[str, Any]) -> None:
    """Print detailed analysis results."""
    
    print("=" * 80)
    print("DETAILED VOUCHER ENTRY ANALYSIS")
    print("=" * 80)
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"  Total Vouchers: {analysis['total_vouchers']}")
    print(f"  Vouchers with Multiple Ledger Entries: {len(analysis['vouchers_with_multiple_ledger_entries'])}")
    print(f"  Vouchers with Multiple Inventory Entries: {len(analysis['vouchers_with_multiple_inventory_entries'])}")
    print(f"  Vouchers with Multiple Accounting Entries: {len(analysis['vouchers_with_multiple_accounting_entries'])}")
    
    print(f"\n🏷️  ENTRY PATTERNS (L:Ledger, I:Inventory, A:Accounting):")
    for pattern, count in sorted(analysis['entry_patterns'].items()):
        print(f"  {pattern}: {count} vouchers")
    
    print(f"\n🔍 SAMPLE VOUCHER ANALYSIS (First 10):")
    print("-" * 80)
    
    for voucher in analysis['sample_vouchers']:
        print(f"\nVoucher #{voucher['voucher_number']}:")
        print(f"  ID: {voucher['voucher_id']}")
        print(f"  Amount: {voucher['voucher_amount']}")
        print(f"  Type: {voucher['voucher_type']}")
        print(f"  Ledger Entries ({voucher['ledger_count']}): {voucher['ledger_entries']}")
        print(f"  Inventory Entries ({voucher['inventory_count']}): {voucher['inventory_entries']}")
        print(f"  Accounting Entries ({voucher['accounting_count']}): {voucher['accounting_entries']}")
        
        if voucher['has_multiple_ledger']:
            print(f"  ⚠️  MULTIPLE LEDGER ENTRIES!")
        if voucher['has_multiple_inventory']:
            print(f"  ⚠️  MULTIPLE INVENTORY ENTRIES!")
        if voucher['has_multiple_accounting']:
            print(f"  ⚠️  MULTIPLE ACCOUNTING ENTRIES!")
    
    # Show vouchers with multiple entries if any
    if analysis['vouchers_with_multiple_ledger_entries']:
        print(f"\n🚨 VOUCHERS WITH MULTIPLE LEDGER ENTRIES:")
        for voucher in analysis['vouchers_with_multiple_ledger_entries']:
            print(f"  Voucher #{voucher['voucher_number']}: {voucher['ledger_count']} ledger entries")
    
    if analysis['vouchers_with_multiple_inventory_entries']:
        print(f"\n🚨 VOUCHERS WITH MULTIPLE INVENTORY ENTRIES:")
        for voucher in analysis['vouchers_with_multiple_inventory_entries']:
            print(f"  Voucher #{voucher['voucher_number']}: {voucher['inventory_count']} inventory entries")
    
    if analysis['vouchers_with_multiple_accounting_entries']:
        print(f"\n🚨 VOUCHERS WITH MULTIPLE ACCOUNTING ENTRIES:")
        for voucher in analysis['vouchers_with_multiple_accounting_entries']:
            print(f"  Voucher #{voucher['voucher_number']}: {voucher['accounting_count']} accounting entries")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python3 detailed_entry_analyzer.py <xml_file>")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    
    try:
        analysis = analyze_voucher_entries(xml_file)
        print_detailed_analysis(analysis)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
