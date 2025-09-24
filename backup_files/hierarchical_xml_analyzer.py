#!/usr/bin/env python3
"""
Hierarchical XML Analyzer for Tally Data
Analyzes the structure of XML files to understand hierarchical relationships,
particularly focusing on ledger entries and inventory entries within vouchers.
"""

import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import defaultdict


class HierarchicalXMLAnalyzer:
    """Analyzer for understanding hierarchical XML structures in Tally data."""
    
    def __init__(self, xml_file_path: str):
        """
        Initialize the analyzer.
        
        Args:
            xml_file_path: Path to the input XML file
        """
        self.xml_file_path = Path(xml_file_path)
        self.content = ""
        self.vouchers = []
        self.analysis_results = {}
        
    def load_xml_content(self) -> None:
        """Load XML content from file."""
        try:
            with open(self.xml_file_path, 'r', encoding='utf-8') as file:
                self.content = file.read()
            print(f"Successfully loaded XML file: {self.xml_file_path}")
        except Exception as e:
            print(f"Error loading XML file: {e}")
            raise
    
    def analyze_structure(self) -> Dict[str, Any]:
        """
        Analyze the hierarchical structure of the XML.
        
        Returns:
            Dictionary containing analysis results
        """
        if not self.content:
            raise ValueError("XML content not loaded. Call load_xml_content() first.")
        
        # Clean XML content
        cleaned_content = self._clean_xml_content(self.content)
        
        # Split into vouchers
        vouchers = self._split_into_vouchers(cleaned_content)
        
        # Analyze each voucher
        voucher_analysis = []
        for i, voucher_content in enumerate(vouchers):
            if voucher_content.strip():
                analysis = self._analyze_voucher(voucher_content, i + 1)
                voucher_analysis.append(analysis)
        
        # Overall analysis
        overall_analysis = self._analyze_overall_structure(voucher_analysis)
        
        self.analysis_results = {
            'total_vouchers': len(voucher_analysis),
            'voucher_analysis': voucher_analysis,
            'overall_analysis': overall_analysis
        }
        
        return self.analysis_results
    
    def _clean_xml_content(self, content: str) -> str:
        """Clean XML content by removing declaration and root tags."""
        # Remove XML declaration
        content = re.sub(r'<\?xml[^>]*\?>', '', content)
        
        # Remove TALLYMESSAGE and ENVELOPE tags
        content = re.sub(r'<TALLYMESSAGE[^>]*>', '', content)
        content = re.sub(r'</TALLYMESSAGE>', '', content)
        content = re.sub(r'<ENVELOPE[^>]*>', '', content)
        content = re.sub(r'</ENVELOPE>', '', content)
        
        return content.strip()
    
    def _split_into_vouchers(self, content: str) -> List[str]:
        """Split content into individual vouchers based on VOUCHER_AMOUNT tags."""
        voucher_amount_pattern = r'<VOUCHER_AMOUNT>'
        matches = list(re.finditer(voucher_amount_pattern, content))
        
        if not matches:
            print("No VOUCHER_AMOUNT tags found in the XML")
            return []
        
        vouchers = []
        
        # Extract vouchers between VOUCHER_AMOUNT tags
        for i, match in enumerate(matches):
            start_pos = match.start()
            
            # Find the end position (next VOUCHER_AMOUNT or end of content)
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)
            
            # Extract voucher content
            voucher_content = content[start_pos:end_pos].strip()
            if voucher_content:
                vouchers.append(voucher_content)
        
        return vouchers
    
    def _analyze_voucher(self, voucher_content: str, voucher_number: int) -> Dict[str, Any]:
        """Analyze a single voucher for hierarchical structure."""
        analysis = {
            'voucher_number': voucher_number,
            'voucher_id': '',
            'voucher_amount': '',
            'voucher_date': '',
            'ledger_entries': [],
            'inventory_entries': [],
            'accounting_ledger_entries': [],
            'total_tags': 0,
            'unique_tag_types': set()
        }
        
        # Extract basic voucher info
        voucher_id_match = re.search(r'<VOUCHER_ID>([^<]*)</VOUCHER_ID>', voucher_content)
        if voucher_id_match:
            analysis['voucher_id'] = voucher_id_match.group(1)
        
        voucher_amount_match = re.search(r'<VOUCHER_AMOUNT>([^<]*)</VOUCHER_AMOUNT>', voucher_content)
        if voucher_amount_match:
            analysis['voucher_amount'] = voucher_amount_match.group(1)
        
        voucher_date_match = re.search(r'<VOUCHER_DATE>([^<]*)</VOUCHER_DATE>', voucher_content)
        if voucher_date_match:
            analysis['voucher_date'] = voucher_date_match.group(1)
        
        # Extract all tags and their values
        tag_pattern = r'<([^>]+)>([^<]*)</\1>'
        matches = re.findall(tag_pattern, voucher_content)
        
        analysis['total_tags'] = len(matches)
        
        # Categorize tags
        for tag_name, tag_value in matches:
            analysis['unique_tag_types'].add(tag_name)
            
            # Categorize ledger entries
            if tag_name.startswith('TRN_LEDGERENTRIES_'):
                analysis['ledger_entries'].append({
                    'tag': tag_name,
                    'value': tag_value.strip()
                })
            
            # Categorize inventory entries
            elif tag_name.startswith('TRN_INVENTORYENTRIES_'):
                analysis['inventory_entries'].append({
                    'tag': tag_name,
                    'value': tag_value.strip()
                })
            
            # Categorize accounting ledger entries
            elif tag_name.startswith('TRN_INVENTORYENTRIES_ACCOUNTINGLEDGER_'):
                analysis['accounting_ledger_entries'].append({
                    'tag': tag_name,
                    'value': tag_value.strip()
                })
        
        # Convert set to list for JSON serialization
        analysis['unique_tag_types'] = list(analysis['unique_tag_types'])
        
        return analysis
    
    def _analyze_overall_structure(self, voucher_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall structure across all vouchers."""
        overall = {
            'total_vouchers': len(voucher_analysis),
            'vouchers_with_multiple_ledger_entries': 0,
            'vouchers_with_multiple_inventory_entries': 0,
            'vouchers_with_accounting_ledger_entries': 0,
            'unique_ledger_names': set(),
            'unique_inventory_items': set(),
            'tag_frequency': defaultdict(int),
            'voucher_types': set(),
            'date_range': {'earliest': None, 'latest': None}
        }
        
        for voucher in voucher_analysis:
            # Check for multiple ledger entries (same voucher ID with different ledger names)
            ledger_names = [entry['value'] for entry in voucher['ledger_entries'] 
                          if entry['tag'] == 'TRN_LEDGERENTRIES_LEDGER_NAME' and entry['value']]
            
            if len(ledger_names) > 1:
                overall['vouchers_with_multiple_ledger_entries'] += 1
            
            # Check for multiple inventory entries
            inventory_items = [entry['value'] for entry in voucher['inventory_entries'] 
                             if entry['tag'] == 'TRN_INVENTORYENTRIES_STOCKITEM_NAME' and entry['value']]
            
            if len(inventory_items) > 1:
                overall['vouchers_with_multiple_inventory_entries'] += 1
            
            # Check for accounting ledger entries
            if voucher['accounting_ledger_entries']:
                overall['vouchers_with_accounting_ledger_entries'] += 1
            
            # Collect unique values
            overall['unique_ledger_names'].update(ledger_names)
            overall['unique_inventory_items'].update(inventory_items)
            
            # Count tag frequency
            for tag_type in voucher['unique_tag_types']:
                overall['tag_frequency'][tag_type] += 1
            
            # Collect voucher types
            voucher_type_match = re.search(r'<VOUCHER_VOUCHER_TYPE>([^<]*)</VOUCHER_VOUCHER_TYPE>', 
                                         voucher.get('voucher_content', ''))
            if voucher_type_match:
                overall['voucher_types'].add(voucher_type_match.group(1))
        
        # Convert sets to lists for JSON serialization
        overall['unique_ledger_names'] = list(overall['unique_ledger_names'])
        overall['unique_inventory_items'] = list(overall['unique_inventory_items'])
        overall['voucher_types'] = list(overall['voucher_types'])
        overall['tag_frequency'] = dict(overall['tag_frequency'])
        
        return overall
    
    def print_analysis_summary(self) -> None:
        """Print a summary of the analysis."""
        if not self.analysis_results:
            print("No analysis results available. Run analyze_structure() first.")
            return
        
        overall = self.analysis_results['overall_analysis']
        
        print("=" * 80)
        print("HIERARCHICAL XML STRUCTURE ANALYSIS")
        print("=" * 80)
        
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"  Total Vouchers: {overall['total_vouchers']}")
        print(f"  Vouchers with Multiple Ledger Entries: {overall['vouchers_with_multiple_ledger_entries']}")
        print(f"  Vouchers with Multiple Inventory Entries: {overall['vouchers_with_multiple_inventory_entries']}")
        print(f"  Vouchers with Accounting Ledger Entries: {overall['vouchers_with_accounting_ledger_entries']}")
        
        print(f"\n🏷️  TAG FREQUENCY (Top 10):")
        sorted_tags = sorted(overall['tag_frequency'].items(), key=lambda x: x[1], reverse=True)
        for tag, count in sorted_tags[:10]:
            print(f"  {tag}: {count}")
        
        print(f"\n📋 VOUCHER TYPES:")
        for vtype in sorted(overall['voucher_types']):
            print(f"  - {vtype}")
        
        print(f"\n🏦 UNIQUE LEDGER NAMES (Sample - First 10):")
        for ledger in sorted(overall['unique_ledger_names'])[:10]:
            print(f"  - {ledger}")
        
        print(f"\n📦 UNIQUE INVENTORY ITEMS (Sample - First 10):")
        for item in sorted(overall['unique_inventory_items'])[:10]:
            print(f"  - {item}")
    
    def find_hierarchical_vouchers(self) -> List[Dict[str, Any]]:
        """Find vouchers that have hierarchical structures (multiple entries)."""
        if not self.analysis_results:
            print("No analysis results available. Run analyze_structure() first.")
            return []
        
        hierarchical_vouchers = []
        
        for voucher in self.analysis_results['voucher_analysis']:
            # Check if voucher has multiple ledger entries or inventory entries
            ledger_names = [entry['value'] for entry in voucher['ledger_entries'] 
                          if entry['tag'] == 'TRN_LEDGERENTRIES_LEDGER_NAME' and entry['value']]
            
            inventory_items = [entry['value'] for entry in voucher['inventory_entries'] 
                             if entry['tag'] == 'TRN_INVENTORYENTRIES_STOCKITEM_NAME' and entry['value']]
            
            if len(ledger_names) > 1 or len(inventory_items) > 1:
                hierarchical_vouchers.append({
                    'voucher_number': voucher['voucher_number'],
                    'voucher_id': voucher['voucher_id'],
                    'voucher_amount': voucher['voucher_amount'],
                    'voucher_date': voucher['voucher_date'],
                    'ledger_names': ledger_names,
                    'inventory_items': inventory_items,
                    'total_ledger_entries': len(ledger_names),
                    'total_inventory_entries': len(inventory_items)
                })
        
        return hierarchical_vouchers
    
    def print_hierarchical_vouchers(self, limit: int = 5) -> None:
        """Print vouchers with hierarchical structures."""
        hierarchical_vouchers = self.find_hierarchical_vouchers()
        
        print(f"\n🔍 HIERARCHICAL VOUCHERS (showing first {min(limit, len(hierarchical_vouchers))}):")
        print("-" * 80)
        
        for voucher in hierarchical_vouchers[:limit]:
            print(f"\nVoucher #{voucher['voucher_number']}:")
            print(f"  ID: {voucher['voucher_id']}")
            print(f"  Amount: {voucher['voucher_amount']}")
            print(f"  Date: {voucher['voucher_date']}")
            print(f"  Ledger Entries ({voucher['total_ledger_entries']}):")
            for ledger in voucher['ledger_names']:
                print(f"    - {ledger}")
            print(f"  Inventory Entries ({voucher['total_inventory_entries']}):")
            for item in voucher['inventory_items']:
                print(f"    - {item}")


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze hierarchical structure of Tally XML files')
    parser.add_argument('xml_file', help='Path to the input XML file')
    parser.add_argument('-s', '--summary', action='store_true', help='Show analysis summary')
    parser.add_argument('--hierarchical', action='store_true', help='Show hierarchical vouchers')
    parser.add_argument('--limit', type=int, default=5, help='Limit number of hierarchical vouchers to show')
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = HierarchicalXMLAnalyzer(args.xml_file)
        
        # Load and analyze
        analyzer.load_xml_content()
        results = analyzer.analyze_structure()
        
        # Show summary if requested
        if args.summary:
            analyzer.print_analysis_summary()
        
        # Show hierarchical vouchers if requested
        if args.hierarchical:
            analyzer.print_hierarchical_vouchers(args.limit)
        
        # Default: show both summary and hierarchical vouchers
        if not args.summary and not args.hierarchical:
            analyzer.print_analysis_summary()
            analyzer.print_hierarchical_vouchers(args.limit)
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
