#!/usr/bin/env python3
"""
Test individual fields to isolate which one causes "invalid object type error"
"""

import yaml
from tally_client import TallyClient

def test_individual_field(field_name, field_expr, field_type, collection="Voucher"):
    """Test a single field to see if it causes errors"""
    
    # Create a minimal report config with just one field
    test_config = {
        "name": f"test_{field_name}",
        "collection": collection,
        "nature": "Primary",
        "fetch": [],
        "filters": [],
        "fields": [
            {
                "name": field_name,
                "field": field_expr,
                "type": field_type
            }
        ]
    }
    
    client = TallyClient()
    tdl_xml = client.create_yaml_based_tdl(test_config)
    
    print(f"\n🔍 Testing field: {field_name}")
    print(f"   Expression: {field_expr}")
    print(f"   Type: {field_type}")
    
    # Test connection first
    if client.test_connection():
        print("   ✅ Connection successful")
        response = client.send_tdl_request(tdl_xml)
        if response:
            print(f"   ✅ Success! Response: {len(response)} chars")
            return True
        else:
            print("   ❌ No response received")
            return False
    else:
        print("   ❌ Connection failed")
        return False

def main():
    """Test all fields from trn_voucher individually"""
    
    # Load the test YAML config
    with open('tally-export-config-test.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    voucher_report = config['transaction'][0]
    fields = voucher_report['fields']
    
    print(f"🧪 Testing {len(fields)} fields individually...")
    print("=" * 60)
    
    successful_fields = []
    failed_fields = []
    
    for field in fields:
        field_name = field['name']
        field_expr = field['field']
        field_type = field['type']
        
        success = test_individual_field(field_name, field_expr, field_type)
        
        if success:
            successful_fields.append(field_name)
        else:
            failed_fields.append(field_name)
    
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY:")
    print(f"✅ Successful fields ({len(successful_fields)}): {', '.join(successful_fields)}")
    print(f"❌ Failed fields ({len(failed_fields)}): {', '.join(failed_fields)}")
    
    if failed_fields:
        print(f"\n🔍 Fields causing issues: {', '.join(failed_fields)}")
        print("These fields may have invalid object types or expressions.")

if __name__ == "__main__":
    main()
