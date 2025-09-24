#!/bin/bash
# Quick script to parse flat XML files with VOUCHER_AMOUNT delimiters

# Check if XML file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <xml_file> [output_csv]"
    echo "Example: $0 xml-files/sample_flat_xml.xml"
    echo "Example: $0 xml-files/sample_flat_xml.xml output.csv"
    exit 1
fi

XML_FILE="$1"
OUTPUT_FILE="$2"

# Check if XML file exists
if [ ! -f "$XML_FILE" ]; then
    echo "Error: XML file '$XML_FILE' not found"
    exit 1
fi

echo "Parsing flat XML file: $XML_FILE"

# Run the parser with preview and summary
if [ -n "$OUTPUT_FILE" ]; then
    python3 flat_xml_parser.py "$XML_FILE" -o "$OUTPUT_FILE" -p -s
else
    python3 flat_xml_parser.py "$XML_FILE" -p -s
fi

echo "Parsing completed!"
