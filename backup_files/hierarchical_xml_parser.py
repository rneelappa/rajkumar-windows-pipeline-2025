#!/usr/bin/env python3
"""
Hierarchical XML Parser for Tally Data
Parses nested XML structures where vouchers can have multiple ledger and inventory entries.
"""

import xml.etree.ElementTree as ET
import csv
import os
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path


class HierarchicalXMLParser:
    """Parser for hierarchical XML structures with nested voucher entries."""
    
    def __init__(self, xml_file_path: str, output_csv_path: Optional[str] = None):
        """
        Initialize the parser.
        
        Args:
            xml_file_path: Path to the input XML file
            output_csv_path: Path for the output CSV file (optional)
        """
        self.xml_file_path = Path(xml_file_path)
        self.output_csv_path = output_csv_path or self._generate_output_path()
        self.vouchers = []
        
    def _generate_output_path(self) -> str:
        """Generate output CSV path based on input XML file."""
        return str(self.xml_file_path.with_suffix('.csv'))
    
    def parse_hierarchical_xml(self) -> List[Dict[str, Any]]:
        """
        Parse hierarchical XML structure where vouchers can have multiple entries.
        
        Returns:
            List of dictionaries containing the parsed vouchers with their entries
        """
        try:
            tree = ET.parse(self.xml_file_path)
            root = tree.getroot()
            print(f"Successfully parsed hierarchical XML file: {self.xml_file_path}")
            
            # Parse vouchers
            vouchers = []
            
            # Look for voucher elements or flat structure
            if self._is_flat_structure(root):
                print("📋 Detected flat XML structure - using flat parser approach")
                vouchers = self._parse_flat_structure(root)
            else:
                print("📋 Detected hierarchical XML structure - using nested parser approach")
                vouchers = self._parse_hierarchical_structure(root)
            
            self.vouchers = vouchers
            print(f"Successfully parsed {len(vouchers)} vouchers from hierarchical XML")
            return vouchers
            
        except ET.ParseError as e:
            print(f"Error parsing XML file: {e}")
            raise
        except FileNotFoundError:
            print(f"XML file not found: {self.xml_file_path}")
            raise
    
    def _is_flat_structure(self, root: ET.Element) -> bool:
        """Check if the XML has a flat structure (like our current data)."""
        # Check if we have VOUCHER_AMOUNT tags at the root level
        voucher_amounts = root.findall('.//VOUCHER_AMOUNT')
        return len(voucher_amounts) > 0
    
    def _parse_flat_structure(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Parse flat XML structure (fallback for current data format)."""
        import re
        
        # Convert to string and use regex parsing like flat parser
        xml_str = ET.tostring(root, encoding='unicode')
        
        # Clean XML content
        xml_str = re.sub(r'<\?xml[^>]*\?>', '', xml_str)
        xml_str = re.sub(r'<TALLYMESSAGE[^>]*>', '', xml_str)
        xml_str = re.sub(r'</TALLYMESSAGE>', '', xml_str)
        xml_str = re.sub(r'<ENVELOPE[^>]*>', '', xml_str)
        xml_str = re.sub(r'</ENVELOPE>', '', xml_str)
        
        # Split into vouchers
        voucher_pattern = r'<VOUCHER_AMOUNT>'
        matches = list(re.finditer(voucher_pattern, xml_str))
        
        vouchers = []
        for i, match in enumerate(matches):
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(xml_str)
            voucher_content = xml_str[start_pos:end_pos].strip()
            
            if voucher_content:
                voucher_data = self._parse_flat_voucher(voucher_content, i + 1)
                vouchers.append(voucher_data)
        
        return vouchers
    
    def _parse_flat_voucher(self, voucher_content: str, voucher_number: int) -> Dict[str, Any]:
        """Parse a single flat voucher."""
        import re
        
        voucher_data = {
            'voucher_number': voucher_number,
            'voucher_id': '',
            'voucher_amount': '',
            'voucher_date': '',
            'voucher_type': '',
            'voucher_narration': '',
            'voucher_party_name': '',
            'voucher_reference': '',
            'voucher_voucher_number': '',
            'ledger_entries': [],
            'inventory_entries': []
        }
        
        # Extract voucher fields
        fields = {
            'voucher_id': r'<VOUCHER_ID>([^<]*)</VOUCHER_ID>',
            'voucher_amount': r'<VOUCHER_AMOUNT>([^<]*)</VOUCHER_AMOUNT>',
            'voucher_date': r'<VOUCHER_DATE>([^<]*)</VOUCHER_DATE>',
            'voucher_type': r'<VOUCHER_VOUCHER_TYPE>([^<]*)</VOUCHER_VOUCHER_TYPE>',
            'voucher_narration': r'<VOUCHER_NARRATION>([^<]*)</VOUCHER_NARRATION>',
            'voucher_party_name': r'<VOUCHER_PARTY_NAME>([^<]*)</VOUCHER_PARTY_NAME>',
            'voucher_reference': r'<VOUCHER_REFERENCE>([^<]*)</VOUCHER_REFERENCE>',
            'voucher_voucher_number': r'<VOUCHER_VOUCHER_NUMBER>([^<]*)</VOUCHER_VOUCHER_NUMBER>'
        }
        
        for field_name, pattern in fields.items():
            match = re.search(pattern, voucher_content)
            if match:
                voucher_data[field_name] = match.group(1).strip()
        
        # Extract ledger entry
        ledger_amount = re.search(r'<TRN_LEDGERENTRIES_AMOUNT>([^<]*)</TRN_LEDGERENTRIES_AMOUNT>', voucher_content)
        ledger_id = re.search(r'<TRN_LEDGERENTRIES_ID>([^<]*)</TRN_LEDGERENTRIES_ID>', voucher_content)
        ledger_name = re.search(r'<TRN_LEDGERENTRIES_LEDGER_NAME>([^<]*)</TRN_LEDGERENTRIES_LEDGER_NAME>', voucher_content)
        ledger_is_debit = re.search(r'<TRN_LEDGERENTRIES_IS_DEBIT>([^<]*)</TRN_LEDGERENTRIES_IS_DEBIT>', voucher_content)
        
        if ledger_amount or ledger_id or ledger_name:
            voucher_data['ledger_entries'].append({
                'amount': ledger_amount.group(1).strip() if ledger_amount else '',
                'id': ledger_id.group(1).strip() if ledger_id else '',
                'ledger_name': ledger_name.group(1).strip() if ledger_name else '',
                'is_debit': ledger_is_debit.group(1).strip() if ledger_is_debit else ''
            })
        
        # Extract inventory entry
        inv_amount = re.search(r'<TRN_INVENTORYENTRIES_AMOUNT>([^<]*)</TRN_INVENTORYENTRIES_AMOUNT>', voucher_content)
        inv_id = re.search(r'<TRN_INVENTORYENTRIES_ID>([^<]*)</TRN_INVENTORYENTRIES_ID>', voucher_content)
        inv_quantity = re.search(r'<TRN_INVENTORYENTRIES_QUANTITY>([^<]*)</TRN_INVENTORYENTRIES_QUANTITY>', voucher_content)
        inv_rate = re.search(r'<TRN_INVENTORYENTRIES_RATE>([^<]*)</TRN_INVENTORYENTRIES_RATE>', voucher_content)
        inv_stockitem = re.search(r'<TRN_INVENTORYENTRIES_STOCKITEM_NAME>([^<]*)</TRN_INVENTORYENTRIES_STOCKITEM_NAME>', voucher_content)
        
        if inv_amount or inv_id or inv_stockitem:
            voucher_data['inventory_entries'].append({
                'amount': inv_amount.group(1).strip() if inv_amount else '',
                'id': inv_id.group(1).strip() if inv_id else '',
                'quantity': inv_quantity.group(1).strip() if inv_quantity else '',
                'rate': inv_rate.group(1).strip() if inv_rate else '',
                'stockitem_name': inv_stockitem.group(1).strip() if inv_stockitem else ''
            })
        
        return voucher_data
    
    def _parse_hierarchical_structure(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Parse hierarchical XML structure (for future nested data)."""
        vouchers = []
        
        # Look for voucher containers
        voucher_containers = root.findall('.//VOUCHER') or root.findall('.//VOUCHERENTRY')
        
        if not voucher_containers:
            print("⚠️  No hierarchical voucher containers found")
            return []
        
        for i, voucher_elem in enumerate(voucher_containers):
            voucher_data = self._parse_hierarchical_voucher(voucher_elem, i + 1)
            vouchers.append(voucher_data)
        
        return vouchers
    
    def _parse_hierarchical_voucher(self, voucher_elem: ET.Element, voucher_number: int) -> Dict[str, Any]:
        """Parse a single hierarchical voucher."""
        voucher_data = {
            'voucher_number': voucher_number,
            'voucher_id': '',
            'voucher_amount': '',
            'voucher_date': '',
            'voucher_type': '',
            'voucher_narration': '',
            'voucher_party_name': '',
            'voucher_reference': '',
            'voucher_voucher_number': '',
            'ledger_entries': [],
            'inventory_entries': []
        }
        
        # Extract voucher fields
        voucher_data['voucher_id'] = self._get_text(voucher_elem, 'VOUCHER_ID')
        voucher_data['voucher_amount'] = self._get_text(voucher_elem, 'VOUCHER_AMOUNT')
        voucher_data['voucher_date'] = self._get_text(voucher_elem, 'VOUCHER_DATE')
        voucher_data['voucher_type'] = self._get_text(voucher_elem, 'VOUCHER_VOUCHER_TYPE')
        voucher_data['voucher_narration'] = self._get_text(voucher_elem, 'VOUCHER_NARRATION')
        voucher_data['voucher_party_name'] = self._get_text(voucher_elem, 'VOUCHER_PARTY_NAME')
        voucher_data['voucher_reference'] = self._get_text(voucher_elem, 'VOUCHER_REFERENCE')
        voucher_data['voucher_voucher_number'] = self._get_text(voucher_elem, 'VOUCHER_VOUCHER_NUMBER')
        
        # Extract ledger entries
        ledger_entries = voucher_elem.findall('.//LEDGERENTRY') or voucher_elem.findall('.//LEDGER_ENTRIES')
        for ledger_elem in ledger_entries:
            ledger_data = {
                'amount': self._get_text(ledger_elem, 'AMOUNT'),
                'id': self._get_text(ledger_elem, 'ID'),
                'ledger_name': self._get_text(ledger_elem, 'LEDGER_NAME'),
                'is_debit': self._get_text(ledger_elem, 'IS_DEBIT')
            }
            voucher_data['ledger_entries'].append(ledger_data)
        
        # Extract inventory entries
        inventory_entries = voucher_elem.findall('.//INVENTORYENTRY') or voucher_elem.findall('.//INVENTORY_ENTRIES')
        for inv_elem in inventory_entries:
            inv_data = {
                'amount': self._get_text(inv_elem, 'AMOUNT'),
                'id': self._get_text(inv_elem, 'ID'),
                'quantity': self._get_text(inv_elem, 'QUANTITY'),
                'rate': self._get_text(inv_elem, 'RATE'),
                'stockitem_name': self._get_text(inv_elem, 'STOCKITEM_NAME')
            }
            voucher_data['inventory_entries'].append(inv_data)
        
        return voucher_data
    
    def _get_text(self, element: ET.Element, tag_name: str) -> str:
        """Get text content from a child element."""
        child = element.find(tag_name)
        return child.text.strip() if child is not None and child.text else ''
    
    def save_to_csv(self, csv_path: Optional[str] = None) -> str:
        """
        Save the parsed vouchers to a CSV file with expanded entries.
        
        Args:
            csv_path: Path for the CSV file (optional)
        
        Returns:
            Path to the saved CSV file
        """
        if not self.vouchers:
            raise ValueError("No vouchers to save. Parse XML first.")
        
        output_path = csv_path or self.output_csv_path
        
        # Create expanded records (one row per ledger/inventory entry)
        expanded_records = []
        
        for voucher in self.vouchers:
            # Create base voucher record
            base_record = {
                'voucher_number': voucher['voucher_number'],
                'voucher_id': voucher['voucher_id'],
                'voucher_amount': voucher['voucher_amount'],
                'voucher_date': voucher['voucher_date'],
                'voucher_type': voucher['voucher_type'],
                'voucher_narration': voucher['voucher_narration'],
                'voucher_party_name': voucher['voucher_party_name'],
                'voucher_reference': voucher['voucher_reference'],
                'voucher_voucher_number': voucher['voucher_voucher_number'],
                'total_ledger_entries': len(voucher['ledger_entries']),
                'total_inventory_entries': len(voucher['inventory_entries'])
            }
            
            # If no entries, create one record
            if not voucher['ledger_entries'] and not voucher['inventory_entries']:
                expanded_records.append(base_record)
            else:
                # Create records for each ledger entry
                for i, ledger_entry in enumerate(voucher['ledger_entries']):
                    record = base_record.copy()
                    record.update({
                        'entry_type': 'ledger',
                        'entry_index': i + 1,
                        'ledger_amount': ledger_entry['amount'],
                        'ledger_id': ledger_entry['id'],
                        'ledger_name': ledger_entry['ledger_name'],
                        'ledger_is_debit': ledger_entry['is_debit'],
                        'inventory_amount': '',
                        'inventory_id': '',
                        'inventory_quantity': '',
                        'inventory_rate': '',
                        'inventory_stockitem_name': ''
                    })
                    expanded_records.append(record)
                
                # Create records for each inventory entry
                for i, inv_entry in enumerate(voucher['inventory_entries']):
                    record = base_record.copy()
                    record.update({
                        'entry_type': 'inventory',
                        'entry_index': i + 1,
                        'ledger_amount': '',
                        'ledger_id': '',
                        'ledger_name': '',
                        'ledger_is_debit': '',
                        'inventory_amount': inv_entry['amount'],
                        'inventory_id': inv_entry['id'],
                        'inventory_quantity': inv_entry['quantity'],
                        'inventory_rate': inv_entry['rate'],
                        'inventory_stockitem_name': inv_entry['stockitem_name']
                    })
                    expanded_records.append(record)
        
        # Write to CSV
        if expanded_records:
            fieldnames = list(expanded_records[0].keys())
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(expanded_records)
        
        print(f"Hierarchical data saved to CSV: {output_path}")
        print(f"Total vouchers: {len(self.vouchers)}")
        print(f"Total expanded records: {len(expanded_records)}")
        
        return output_path
    
    def preview_vouchers(self, num_vouchers: int = 3) -> None:
        """Preview the parsed vouchers."""
        if not self.vouchers:
            print("No vouchers parsed yet.")
            return
        
        print(f"\nVouchers Preview (showing first {min(num_vouchers, len(self.vouchers))} vouchers):")
        print("=" * 80)
        
        for i, voucher in enumerate(self.vouchers[:num_vouchers]):
            print(f"\nVoucher {i + 1}:")
            print("-" * 40)
            print(f"  ID: {voucher['voucher_id']}")
            print(f"  Amount: {voucher['voucher_amount']}")
            print(f"  Date: {voucher['voucher_date']}")
            print(f"  Type: {voucher['voucher_type']}")
            print(f"  Ledger Entries ({len(voucher['ledger_entries'])}):")
            for j, entry in enumerate(voucher['ledger_entries']):
                print(f"    {j+1}. {entry['ledger_name']} - {entry['amount']}")
            print(f"  Inventory Entries ({len(voucher['inventory_entries'])}):")
            for j, entry in enumerate(voucher['inventory_entries']):
                print(f"    {j+1}. {entry['stockitem_name']} - {entry['amount']}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Parse hierarchical XML files with nested voucher entries')
    parser.add_argument('xml_file', help='Path to the input XML file')
    parser.add_argument('-o', '--output', help='Output CSV file path')
    parser.add_argument('-p', '--preview', action='store_true', help='Preview vouchers before saving')
    parser.add_argument('--preview-vouchers', type=int, default=3, help='Number of vouchers to preview')
    
    args = parser.parse_args()
    
    try:
        # Initialize parser
        hierarchical_parser = HierarchicalXMLParser(args.xml_file, args.output)
        
        # Parse hierarchical XML
        vouchers = hierarchical_parser.parse_hierarchical_xml()
        
        if not vouchers:
            print("No vouchers found in the XML file.")
            return 1
        
        # Preview if requested
        if args.preview:
            hierarchical_parser.preview_vouchers(args.preview_vouchers)
        
        # Save to CSV
        csv_path = hierarchical_parser.save_to_csv()
        print(f"\nConversion completed successfully!")
        print(f"Input XML: {args.xml_file}")
        print(f"Output CSV: {csv_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
