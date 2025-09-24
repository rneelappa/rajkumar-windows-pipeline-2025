#!/usr/bin/env python3
"""
Flat XML Parser for Tally Data
Specialized parser for flat XML structures where records are delimited by VOUCHER_AMOUNT tags.
Each record starts with <VOUCHER_AMOUNT> and continues until the next <VOUCHER_AMOUNT> or </ENVELOPE>.
"""

import xml.etree.ElementTree as ET
import csv
import os
import argparse
import re
from typing import Dict, List, Any, Optional
from pathlib import Path


class FlatXMLParser:
    """Parser for flat XML structures with VOUCHER_AMOUNT as record delimiter."""
    
    def __init__(self, xml_file_path: str, output_csv_path: Optional[str] = None):
        """
        Initialize the parser.
        
        Args:
            xml_file_path: Path to the input XML file
            output_csv_path: Path for the output CSV file (optional)
        """
        self.xml_file_path = Path(xml_file_path)
        self.output_csv_path = output_csv_path or self._generate_output_path()
        self.records = []
        
    def _generate_output_path(self) -> str:
        """Generate output CSV path based on input XML file."""
        return str(self.xml_file_path.with_suffix('.csv'))
    
    def parse_flat_xml(self) -> List[Dict[str, Any]]:
        """
        Parse flat XML structure where records are delimited by VOUCHER_AMOUNT.
        
        Returns:
            List of dictionaries containing the parsed records
        """
        try:
            with open(self.xml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Remove XML declaration and root tags for easier parsing
            content = self._clean_xml_content(content)
            
            # Split content into records based on VOUCHER_AMOUNT tags
            records = self._split_into_records(content)
            
            # Parse each record
            parsed_records = []
            for i, record_content in enumerate(records):
                if record_content.strip():
                    record_data = self._parse_record(record_content, i + 1)
                    if record_data:
                        parsed_records.append(record_data)
            
            self.records = parsed_records
            print(f"Successfully parsed {len(parsed_records)} records from flat XML")
            return parsed_records
            
        except Exception as e:
            print(f"Error parsing flat XML file: {e}")
            raise
    
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
    
    def _split_into_records(self, content: str) -> List[str]:
        """Split content into individual records based on VOUCHER_AMOUNT tags."""
        # Find all VOUCHER_AMOUNT positions
        voucher_amount_pattern = r'<VOUCHER_AMOUNT>'
        matches = list(re.finditer(voucher_amount_pattern, content))
        
        if not matches:
            print("No VOUCHER_AMOUNT tags found in the XML")
            return []
        
        records = []
        
        # Extract records between VOUCHER_AMOUNT tags
        for i, match in enumerate(matches):
            start_pos = match.start()
            
            # Find the end position (next VOUCHER_AMOUNT or end of content)
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)
            
            # Extract record content
            record_content = content[start_pos:end_pos].strip()
            if record_content:
                records.append(record_content)
        
        return records
    
    def _parse_record(self, record_content: str, record_number: int) -> Dict[str, Any]:
        """Parse a single record into a dictionary."""
        record_data = {'record_number': record_number}
        
        # Extract all XML tags and their values
        tag_pattern = r'<([^>]+)>([^<]*)</\1>'
        matches = re.findall(tag_pattern, record_content)
        
        for tag_name, tag_value in matches:
            # Clean tag name and value
            clean_tag_name = tag_name.strip()
            clean_tag_value = str(tag_value).strip()
            
            # Add to record data
            record_data[clean_tag_name] = clean_tag_value
        
        return record_data
    
    def save_to_csv(self, csv_path: Optional[str] = None) -> str:
        """
        Save the parsed records to a CSV file.
        
        Args:
            csv_path: Path for the CSV file (optional)
        
        Returns:
            Path to the saved CSV file
        """
        if not self.records:
            raise ValueError("No records to save. Parse XML first.")
        
        output_path = csv_path or self.output_csv_path
        
        # Get all unique field names
        all_fields = set()
        for record in self.records:
            all_fields.update(record.keys())
        
        fieldnames = sorted(list(all_fields))
        
        # Write to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.records)
        
        print(f"Records saved to CSV: {output_path}")
        print(f"Total records: {len(self.records)}")
        print(f"Total columns: {len(fieldnames)}")
        
        return output_path
    
    def preview_records(self, num_records: int = 3) -> None:
        """Preview the parsed records."""
        if not self.records:
            print("No records parsed yet.")
            return
        
        print(f"\nRecords Preview (showing first {min(num_records, len(self.records))} records):")
        print("=" * 80)
        
        for i, record in enumerate(self.records[:num_records]):
            print(f"\nRecord {i + 1}:")
            print("-" * 40)
            for key, value in record.items():
                if value and str(value).strip():  # Only show non-empty values
                    print(f"  {key}: {value}")
    
    def get_field_summary(self) -> Dict[str, int]:
        """Get summary of field usage across all records."""
        if not self.records:
            return {}
        
        field_counts = {}
        for record in self.records:
            for field_name, field_value in record.items():
                if field_name not in field_counts:
                    field_counts[field_name] = 0
                if field_value and str(field_value).strip():
                    field_counts[field_name] += 1
        
        return field_counts
    
    def print_field_summary(self) -> None:
        """Print summary of field usage."""
        field_counts = self.get_field_summary()
        
        print(f"\nField Usage Summary:")
        print("=" * 50)
        print(f"{'Field Name':<40} {'Records':<10}")
        print("-" * 50)
        
        for field_name, count in sorted(field_counts.items()):
            print(f"{field_name:<40} {count:<10}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Parse flat XML files with VOUCHER_AMOUNT delimiters')
    parser.add_argument('xml_file', help='Path to the input XML file')
    parser.add_argument('-o', '--output', help='Output CSV file path')
    parser.add_argument('-p', '--preview', action='store_true', help='Preview records before saving')
    parser.add_argument('--preview-records', type=int, default=3, help='Number of records to preview')
    parser.add_argument('-s', '--summary', action='store_true', help='Show field usage summary')
    
    args = parser.parse_args()
    
    try:
        # Initialize parser
        flat_parser = FlatXMLParser(args.xml_file, args.output)
        
        # Parse flat XML
        records = flat_parser.parse_flat_xml()
        
        if not records:
            print("No records found in the XML file.")
            return 1
        
        # Show field summary if requested
        if args.summary:
            flat_parser.print_field_summary()
        
        # Preview if requested
        if args.preview:
            flat_parser.preview_records(args.preview_records)
        
        # Save to CSV
        csv_path = flat_parser.save_to_csv()
        print(f"\nConversion completed successfully!")
        print(f"Input XML: {args.xml_file}")
        print(f"Output CSV: {csv_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
