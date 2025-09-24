# XML Quick Parser

A flexible Python script to parse XML files and convert them to CSV format. This tool provides full control over data mapping and is perfect for recurring imports and data transformation tasks.

## Features

- **Flexible XML Parsing**: Supports various XML structures and formats
- **Multiple Extraction Methods**: Generic extraction or custom structure-based extraction
- **CSV Output**: Clean, structured CSV files with proper encoding
- **Command Line Interface**: Easy-to-use CLI with multiple options
- **Data Preview**: Preview extracted data before saving
- **Customizable Mapping**: JSON configuration for complex XML structures
- **No External Dependencies**: Uses only Python standard library (optional enhancements available)

## Installation

### Basic Installation (No External Dependencies)
The script works out of the box with Python 3.6+ using only standard library modules.

### Enhanced Installation (Optional)
For advanced features, install optional dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Basic Usage
```bash
python xml_to_csv_parser.py input.xml
```

### 2. Specify Output File
```bash
python xml_to_csv_parser.py input.xml -o output.csv
```

### 3. Extract Specific Elements
```bash
python xml_to_csv_parser.py input.xml -e "item" "product" "order"
```

### 4. Preview Data Before Saving
```bash
python xml_to_csv_parser.py input.xml -p --preview-rows 10
```

## Usage Examples

### Example 1: Generic XML Parsing
```bash
# Parse any XML file and extract all elements with text content
python xml_to_csv_parser.py data.xml -p
```

### Example 2: Tally XML Parsing
```bash
# Extract specific Tally elements
python xml_to_csv_parser.py tally_data.xml -e "VOUCHER" "LEDGER" "GROUP" -o tally_output.csv
```

### Example 3: Custom Structure Configuration
Create a `config.json` file:
```json
{
  "container_xpath": ".//VOUCHER",
  "fields": {
    "voucher_type": {
      "xpath": "VOUCHERTYPE",
      "type": "text"
    },
    "date": {
      "xpath": "DATE",
      "type": "text"
    },
    "amount": {
      "xpath": "AMOUNT",
      "type": "text",
      "default": "0"
    },
    "party_name": {
      "xpath": "PARTYNAME",
      "type": "text"
    }
  },
  "include_attributes": true
}
```

Then use it:
```bash
python xml_to_csv_parser.py tally_data.xml -c config.json -o structured_output.csv
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `xml_file` | Path to the input XML file (required) |
| `-o, --output` | Output CSV file path (optional) |
| `-e, --elements` | Specific elements to extract (space-separated) |
| `-c, --config` | JSON configuration file for custom structure |
| `-p, --preview` | Preview data before saving |
| `--preview-rows` | Number of rows to preview (default: 5) |

## Configuration File Format

The JSON configuration file allows you to define custom extraction structures:

```json
{
  "container_xpath": "XPath to find container elements",
  "fields": {
    "field_name": {
      "xpath": "XPath to field within container",
      "type": "text|attribute|count",
      "default": "default_value",
      "attribute_name": "attribute_name_for_attribute_type"
    }
  },
  "include_attributes": true
}
```

### Field Types
- **text**: Extract text content from element
- **attribute**: Extract attribute value from element
- **count**: Count number of matching elements

## Python API Usage

You can also use the parser programmatically:

```python
from xml_to_csv_parser import XMLToCSVParser

# Initialize parser
parser = XMLToCSVParser('input.xml', 'output.csv')

# Parse XML
parser.parse_xml()

# Extract data (generic method)
data = parser.extract_data_generic(['item', 'product'])

# Or extract with custom structure
config = {
    'container_xpath': './/item',
    'fields': {
        'name': {'xpath': 'name', 'type': 'text'},
        'price': {'xpath': 'price', 'type': 'text', 'default': '0'}
    }
}
data = parser.extract_data_by_structure(config)

# Preview data
parser.preview_data(5)

# Save to CSV
csv_path = parser.save_to_csv()
```

## File Structure

```
xml-quick-parser/
├── xml_to_csv_parser.py    # Main parser script
├── requirements.txt         # Optional dependencies
├── README.md              # This file
└── xml-files/             # Directory for XML files
    └── (place your XML files here)
```

## Supported XML Formats

The parser is designed to handle various XML formats:

- **Tally XML**: Financial data from Tally software
- **Generic XML**: Any well-formed XML structure
- **Nested XML**: Complex hierarchical structures
- **Attribute-rich XML**: XML with many attributes
- **Large XML files**: Efficient parsing for large datasets

## Tips for Best Results

1. **Preview First**: Always use `-p` flag to preview data before saving
2. **Specific Elements**: Use `-e` to extract only relevant elements
3. **Custom Config**: Use JSON config for complex XML structures
4. **Large Files**: For very large XML files, consider processing in chunks
5. **Encoding**: The script handles UTF-8 encoding automatically

## Troubleshooting

### Common Issues

1. **"XML file not found"**: Check the file path and ensure the file exists
2. **"No data extracted"**: Try using `-p` to preview and check XML structure
3. **"Parse error"**: Ensure XML is well-formed and valid
4. **Empty CSV**: Check if XML elements contain text content

### Debug Mode
Add print statements or use a debugger to inspect the XML structure:

```python
# Add this to debug XML structure
parser.parse_xml()
print("Root element:", parser.root.tag)
for child in parser.root:
    print(f"Child: {child.tag}, Text: {child.text}")
```

## Contributing

Feel free to enhance the parser with additional features:

- Excel output support
- JSON output format
- Batch processing multiple files
- Advanced filtering options
- Data validation and cleaning

## License

This tool is provided as-is for data processing needs. Modify and use as required for your projects.
