#!/usr/bin/env python3
"""
YAML Dynamic Client
===================

Implements the exact generateXMLfromYAML logic from tallymts.txt
to create dynamic nested TDL that can extract multiple children per voucher.
"""

import logging
import requests
import re
from typing import Optional, List, Dict, Any
from get_dynamic_tally_url import get_and_validate_tally_url

logger = logging.getLogger(__name__)

class YAMLDynamicClient:
    """Client using the exact generateXMLfromYAML logic from tallymts.txt."""
    
    def __init__(self, base_url: str = None, timeout: int = 120):
        # Get dynamic Tally URL from database if not provided
        if base_url:
            self.base_url = base_url
        else:
            dynamic_url = get_and_validate_tally_url()
            if not dynamic_url:
                raise ValueError("❌ No valid Tally URL available from database")
            self.base_url = dynamic_url
            
        self.timeout = timeout
        self.company_name = "SKM IMPEX-CHENNAI-(24-25)"
    
    def generate_xml_from_yaml_config(self, collection: str, fields: List[Dict[str, Any]], filters: List[str] = None) -> str:
        """Generate TDL XML using the exact logic from tallymts.txt generateXMLfromYAML function."""
        
        retval = ''
        
        try:
            # XML header
            retval = f"""<?xml version="1.0" encoding="utf-8"?><ENVELOPE><HEADER><VERSION>1</VERSION><TALLYREQUEST>Export</TALLYREQUEST><TYPE>Data</TYPE><ID>TallyDatabaseLoaderReport</ID></HEADER><BODY><DESC><STATICVARIABLES><SVEXPORTFORMAT>XML (Data Interchange)</SVEXPORTFORMAT><SVCURRENTCOMPANY>{self.company_name}</SVCURRENTCOMPANY></STATICVARIABLES><TDL><TDLMESSAGE><REPORT NAME="TallyDatabaseLoaderReport"><FORMS>MyForm</FORMS></REPORT><FORM NAME="MyForm"><PARTS>MyPart01</PARTS></FORM>"""
            
            # Push routes list
            lst_routes = collection.split('.')
            target_collection = lst_routes.pop(0)  # Remove first element
            lst_routes.insert(0, 'MyCollection')  # Add basic collection level route
            
            # Loop through and append PART XML
            for i in range(len(lst_routes)):
                xml_part = f"MyPart{i+1:02d}"
                xml_line = f"MyLine{i+1:02d}"
                retval += f'<PART NAME="{xml_part}"><LINES>{xml_line}</LINES><REPEAT>{xml_line} : {lst_routes[i]}</REPEAT><SCROLLED>Vertical</SCROLLED></PART>'
            
            # Loop through and append LINE XML (except last line which contains field data)
            for i in range(len(lst_routes) - 1):
                xml_line = f"MyLine{i+1:02d}"
                xml_part = f"MyPart{i+2:02d}"
                retval += f'<LINE NAME="{xml_line}"><FIELDS>FldBlank</FIELDS><EXPLODE>{xml_part}</EXPLODE></LINE>'
            
            retval += f'<LINE NAME="MyLine{len(lst_routes):02d}">'
            retval += '<FIELDS>'  # field end
            
            # Append field declaration list
            for i in range(len(fields)):
                retval += f'Fld{i+1:02d},'
            retval = retval.rstrip(',')
            retval += '</FIELDS></LINE>'  # End of Field declaration
            
            # Loop through each field
            for i, field in enumerate(fields):
                field_xml = f'<FIELD NAME="Fld{i+1:02d}">'
                
                # Set field TDL XML expression based on type of data
                if re.match(r'^(\.\.)?[a-zA-Z0-9_]+$', field['field']):
                    if field['type'] == 'text':
                        field_xml += f'<SET>${field["field"]}</SET>'
                    elif field['type'] == 'logical':
                        field_xml += f'<SET>if ${field["field"]} then 1 else 0</SET>'
                    elif field['type'] == 'date':
                        field_xml += f'<SET>${field["field"]}</SET>'
                    elif field['type'] in ['amount', 'number', 'quantity', 'rate']:
                        field_xml += f'<SET>${field["field"]}</SET>'
                    else:
                        field_xml += f'<SET>${field["field"]}</SET>'
                else:
                    # Complex field expression
                    field_xml += f'<SET>{field["field"]}</SET>'
                
                field_xml += '</FIELD>'
                retval += field_xml
            
            # Add blank field specification (required for intermediate LINE definitions)
            retval += '<FIELD NAME="FldBlank"><SET>""</SET></FIELD>'
            
            # Add collection definition
            retval += f'<COLLECTION NAME="MyCollection"><TYPE>{target_collection}</TYPE>'
            
            # Add FETCH list (based on field requirements)
            fetch_fields = []
            for field in fields:
                if re.match(r'^[a-zA-Z0-9_]+$', field['field']):
                    fetch_fields.append(field['field'])
            
            if fetch_fields:
                retval += f'<FETCH>{",".join(fetch_fields)}</FETCH>'
            
            # Add filters if provided
            if filters:
                retval += '<FILTER>'
                for j, filter_expr in enumerate(filters):
                    filter_name = f'Fltr{j+1:02d}'
                    retval += f'{filter_name},'
                retval = retval.rstrip(',')  # Remove last comma
                retval += '</FILTER>'
            
            retval += '</COLLECTION>'
            
            # Add filter definitions
            if filters:
                for j, filter_expr in enumerate(filters):
                    filter_name = f'Fltr{j+1:02d}'
                    retval += f'<SYSTEM TYPE="Formulae" NAME="{filter_name}">{filter_expr}</SYSTEM>'
            
            # XML footer
            retval += '</TDLMESSAGE></TDL></DESC></BODY></ENVELOPE>'
            
        except Exception as e:
            logger.error(f"Error in generate_xml_from_yaml_config: {e}")
        
        return retval
    
    def create_trn_accounting_tdl(self) -> str:
        """Create TDL for trn_accounting using the YAML dynamic approach."""
        
        # Define the collection path and fields based on YAML configuration
        collection = "Voucher.AllLedgerEntries"
        fields = [
            {"name": "guid", "field": "Guid", "type": "text"},
            {"name": "ledger", "field": "LedgerName", "type": "text"},
            {"name": "amount", "field": "Amount", "type": "amount"},
            {"name": "is_debit", "field": "IsDebit", "type": "logical"},
            {"name": "voucher_guid", "field": "MasterID", "type": "text"},
            {"name": "voucher_number", "field": "VoucherNumber", "type": "text"},
            {"name": "voucher_date", "field": "Date", "type": "date"},
            {"name": "voucher_type", "field": "VoucherTypeName", "type": "text"}
        ]
        filters = ["NOT $IsCancelled", "NOT $IsOptional"]
        
        return self.generate_xml_from_yaml_config(collection, fields, filters)
    
    def create_trn_inventory_tdl(self) -> str:
        """Create TDL for trn_inventory using the YAML dynamic approach."""
        
        # Define the collection path and fields based on FULL YAML configuration
        collection = "Voucher.AllInventoryEntries"
        fields = [
            {"name": "guid", "field": "Guid", "type": "text"},
            {"name": "item", "field": "StockItemName", "type": "text"},
            {"name": "quantity", "field": "ActualQty", "type": "quantity"},
            {"name": "rate", "field": "Rate", "type": "rate"},
            {"name": "amount", "field": "Amount", "type": "amount"},
            {"name": "additional_amount", "field": "AddlAmount", "type": "amount"},
            {"name": "discount_amount", "field": "Discount", "type": "number"},
            {"name": "godown", "field": "GodownName", "type": "text"},
            {"name": "tracking_number", "field": "TrackingNumber", "type": "text"},
            {"name": "order_number", "field": "OrderNo", "type": "text"},
            {"name": "order_duedate", "field": "OrderDueDate", "type": "date"},
            {"name": "voucher_guid", "field": "..Guid", "type": "text"}
        ]
        filters = []  # Remove complex filters that cause issues
        
        return self.generate_xml_from_yaml_config(collection, fields, filters)

    def create_trn_voucher_tdl(self) -> str:
        """Create TDL for trn_voucher using the YAML dynamic approach."""
        
        # Define the collection path and fields for vouchers
        collection = "Voucher"
        fields = [
            {"name": "guid", "field": "Guid", "type": "text"},
            {"name": "voucher_number", "field": "VoucherNumber", "type": "text"},
            {"name": "voucher_type", "field": "VoucherTypeName", "type": "text"},
            {"name": "date", "field": "Date", "type": "date"},
            {"name": "amount", "field": "Amount", "type": "amount"},
            {"name": "reference", "field": "Reference", "type": "text"},
            {"name": "narration", "field": "Narration", "type": "text"},
            {"name": "party_name", "field": "PartyLedgerName", "type": "text"},
            {"name": "is_cancelled", "field": "IsCancelled", "type": "logical"},
            {"name": "is_optional", "field": "IsOptional", "type": "logical"}
        ]
        filters = []  # Remove complex filters that cause issues
        
        return self.generate_xml_from_yaml_config(collection, fields, filters)
    
    def create_mst_stock_item_tdl(self) -> str:
        """Create TDL for mst_stock_item using the YAML dynamic approach."""
        
        # Define the collection path and fields based on YAML configuration
        collection = "StockItem"
        fields = [
            {"name": "guid", "field": "Guid", "type": "text"},
            {"name": "name", "field": "Name", "type": "text"},
            {"name": "parent", "field": "Parent", "type": "text"},
            {"name": "category", "field": "Category", "type": "text"},
            {"name": "uom", "field": "BaseUnits", "type": "text"},
            {"name": "opening_balance", "field": "OpeningBalance", "type": "number"},
            {"name": "opening_rate", "field": "OpeningRate", "type": "rate"},
            {"name": "opening_value", "field": "OpeningValue", "type": "amount"},
            {"name": "gst_hsn_code", "field": "GstDetails.HSNCode", "type": "text"},
            {"name": "gst_taxability", "field": "GstDetails.Taxability", "type": "text"},
            {"name": "part_number", "field": "PartNo", "type": "text"}
        ]
        filters = []
        
        return self.generate_xml_from_yaml_config(collection, fields, filters)
    
    def create_mst_ledger_tdl(self) -> str:
        """Create TDL for mst_ledger using the YAML dynamic approach."""
        
        # Define the collection path and fields based on YAML configuration
        collection = "Ledger"
        fields = [
            {"name": "guid", "field": "Guid", "type": "text"},
            {"name": "name", "field": "Name", "type": "text"},
            {"name": "parent", "field": "Parent", "type": "text"},
            {"name": "alias", "field": "Alias", "type": "text"},
            {"name": "opening_balance", "field": "OpeningBalance", "type": "amount"},
            {"name": "closing_balance", "field": "ClosingBalance", "type": "amount"},
            {"name": "is_revenue", "field": "IsRevenue", "type": "logical"},
            {"name": "is_deemedpositive", "field": "IsDeemedPositive", "type": "logical"},
            {"name": "gstn", "field": "GSTN", "type": "text"},
            {"name": "bank_account_number", "field": "BankAccountNumber", "type": "text"},
            {"name": "bank_name", "field": "BankName", "type": "text"},
            {"name": "bank_ifsc", "field": "IFSC", "type": "text"}
        ]
        filters = []
        
        return self.generate_xml_from_yaml_config(collection, fields, filters)
    
    def create_mst_voucher_type_tdl(self) -> str:
        """Create TDL for mst_vouchertype using the YAML dynamic approach."""
        
        # Define the collection path and fields based on YAML configuration
        collection = "VoucherType"
        fields = [
            {"name": "guid", "field": "Guid", "type": "text"},
            {"name": "name", "field": "Name", "type": "text"},
            {"name": "parent", "field": "Parent", "type": "text"},
            {"name": "affects_stock", "field": "AffectsStock", "type": "logical"},
            {"name": "numbering_method", "field": "NumberingMethod", "type": "text"},
            {"name": "is_deemedpositive", "field": "IsDeemedPositive", "type": "logical"}
        ]
        filters = []
        
        return self.generate_xml_from_yaml_config(collection, fields, filters)
    
    def test_mst_stock_item_extraction(self) -> Optional[str]:
        """Test master data extraction for stock items."""
        tdl_xml = self.create_mst_stock_item_tdl()
        return self.send_tdl_request(tdl_xml)
    
    def test_mst_ledger_extraction(self) -> Optional[str]:
        """Test master data extraction for ledgers."""
        tdl_xml = self.create_mst_ledger_tdl()
        return self.send_tdl_request(tdl_xml)
    
    def test_mst_voucher_type_extraction(self) -> Optional[str]:
        """Test master data extraction for voucher types."""
        tdl_xml = self.create_mst_voucher_type_tdl()
        return self.send_tdl_request(tdl_xml)
    
    def send_tdl_request(self, tdl_xml: str) -> Optional[str]:
        """Send TDL request to Tally server."""
        try:
            headers = {
                'Content-Type': 'application/xml',
                'Content-Length': str(len(tdl_xml))
            }
            
            logger.info(f"🔄 Sending YAML dynamic TDL to {self.base_url}")
            logger.info(f"📊 TDL size: {len(tdl_xml)} characters")
            
            response = requests.post(
                self.base_url,
                data=tdl_xml,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info(f"✅ TDL request successful: {len(response.text)} characters received")
                return response.text
            else:
                logger.error(f"❌ TDL request failed with status: {response.status_code}")
                logger.error(f"Response: {response.text[:500]}")
                return None
                
        except Exception as e:
            logger.error(f"❌ TDL request failed: {e}")
            return None
    
    def test_trn_accounting_extraction(self) -> Optional[str]:
        """Test trn_accounting extraction using YAML dynamic approach."""
        logger.info("🔍 Testing trn_accounting extraction with YAML dynamic approach")
        
        tdl_xml = self.create_trn_accounting_tdl()
        response = self.send_tdl_request(tdl_xml)
        
        if response:
            logger.info("✅ trn_accounting extraction successful")
            return response
        else:
            logger.error("❌ trn_accounting extraction failed")
            return None
    
    def test_trn_inventory_extraction(self) -> Optional[str]:
        """Test trn_inventory extraction using YAML dynamic approach."""
        logger.info("🔍 Testing trn_inventory extraction with YAML dynamic approach")
        
        tdl_xml = self.create_trn_inventory_tdl()
        response = self.send_tdl_request(tdl_xml)
        
        if response:
            logger.info("✅ trn_inventory extraction successful")
            return response
        else:
            logger.error("❌ trn_inventory extraction failed")
            return None

    def test_trn_voucher_extraction(self) -> Optional[str]:
        """Test trn_voucher extraction using YAML dynamic approach."""
        logger.info("🔍 Testing trn_voucher extraction with YAML dynamic approach")
        
        tdl_xml = self.create_trn_voucher_tdl()
        response = self.send_tdl_request(tdl_xml)
        
        if response:
            logger.info("✅ trn_voucher extraction successful")
            return response
        else:
            logger.error("❌ trn_voucher extraction failed")
            return None

def main():
    """Test YAML dynamic extraction approaches."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    client = YAMLDynamicClient()
    
    print("🔍 Testing YAML Dynamic Extraction Approaches")
    print("=" * 60)
    
    # Test 1: trn_accounting (Voucher.AllLedgerEntries)
    print("\n📊 Test 1: trn_accounting (Voucher.AllLedgerEntries)...")
    response1 = client.test_trn_accounting_extraction()
    if response1:
        print(f"   ✅ Response Size: {len(response1)} characters")
        
        # Quick analysis
        ledger_guids = len(re.findall(r'<FLD01>', response1, re.IGNORECASE))
        voucher_guids = len(re.findall(r'<FLD05>', response1, re.IGNORECASE))
        print(f"   📈 Ledger records found: {ledger_guids}")
        print(f"   📈 Voucher references found: {voucher_guids}")
        
        if ledger_guids > 0:
            print(f"   📈 Total ledger entries: {ledger_guids}")
            
            # Check for unique vouchers
            voucher_pattern = r'<FLD05>([^<]+)</FLD05>'
            voucher_matches = re.findall(voucher_pattern, response1, re.IGNORECASE)
            unique_vouchers = len(set(voucher_matches))
            
            if unique_vouchers > 0:
                print(f"   📈 Unique vouchers: {unique_vouchers}")
                print(f"   📈 Ratio: {ledger_guids/unique_vouchers:.2f} ledger entries per voucher")
                
                if ledger_guids > unique_vouchers:
                    print(f"   🎉 SUCCESS: Multiple ledger entries per voucher detected!")
                else:
                    print(f"   ⚠️  Still only 1 ledger entry per voucher")
        
        # Show sample data
        print(f"   \n📋 Sample data (first 10 lines):")
        lines = response1.split('\n')[:10]
        for line in lines:
            if line.strip() and ('<' in line and '>' in line):
                print(f"     {line.strip()}")
    else:
        print("   ❌ Test 1 failed")
    
    # Test 2: trn_inventory (Voucher.AllInventoryEntries)
    print("\n📊 Test 2: trn_inventory (Voucher.AllInventoryEntries)...")
    response2 = client.test_trn_inventory_extraction()
    if response2:
        print(f"   ✅ Response Size: {len(response2)} characters")
        
        # Quick analysis
        inventory_guids = len(re.findall(r'<FLD01>', response2, re.IGNORECASE))
        voucher_guids = len(re.findall(r'<FLD06>', response2, re.IGNORECASE))
        print(f"   📈 Inventory records found: {inventory_guids}")
        print(f"   📈 Voucher references found: {voucher_guids}")
        
        if inventory_guids > 0:
            print(f"   📈 Total inventory entries: {inventory_guids}")
            
            # Check for unique vouchers
            voucher_pattern = r'<FLD06>([^<]+)</FLD06>'
            voucher_matches = re.findall(voucher_pattern, response2, re.IGNORECASE)
            unique_vouchers = len(set(voucher_matches))
            
            if unique_vouchers > 0:
                print(f"   📈 Unique vouchers: {unique_vouchers}")
                print(f"   📈 Ratio: {inventory_guids/unique_vouchers:.2f} inventory entries per voucher")
                
                if inventory_guids > unique_vouchers:
                    print(f"   🎉 SUCCESS: Multiple inventory entries per voucher detected!")
                else:
                    print(f"   ⚠️  Still only 1 inventory entry per voucher")
    else:
        print("   ❌ Test 2 failed")
    
    print("\n✅ YAML dynamic extraction test completed!")

if __name__ == "__main__":
    main()
