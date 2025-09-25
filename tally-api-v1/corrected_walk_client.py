#!/usr/bin/env python3
"""
Corrected WALK-Based Tally Client
=================================

This implements the proven WALK approach that works without crashing Tally.
Based on the successful Coderef.txt implementation.
"""

import logging
import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from get_dynamic_tally_url import get_and_validate_tally_url

logger = logging.getLogger(__name__)

class CorrectedWALKClient:
    """Corrected Tally client using proven WALK-based approach."""
    
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
        
    def create_proven_transaction_tdl(self) -> str:
        """Create proven transaction TDL based on Coderef.txt approach."""
        
        tdl_xml = f"""<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Data</TYPE>
        <ID>MasterComprehensiveWalk</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>XML (Data Interchange)</SVEXPORTFORMAT>
                <SVCOMPANYNAME>{self.company_name}</SVCOMPANYNAME>
            </STATICVARIABLES>
            <TDL>
                <TDLMESSAGE>
                    <REPORT NAME="MasterComprehensiveWalk">
                        <FORMS>MasterComprehensiveWalkForm</FORMS>
                    </REPORT>
                    <FORM NAME="MasterComprehensiveWalkForm">
                        <PARTS>MasterComprehensiveWalkPart</PARTS>
                    </FORM>
                    <PART NAME="MasterComprehensiveWalkPart">
                        <LINES>MasterComprehensiveWalkLine</LINES>
                        <REPEAT>MasterComprehensiveWalkLine : MasterCollection</REPEAT>
                        <SCROLLED>Vertical</SCROLLED>
                    </PART>
                    <LINE NAME="MasterComprehensiveWalkLine">
                        <FIELDS>voucher_amount,voucher_date,voucher_id,voucher_narration,voucher_party_name,voucher_reference,voucher_voucher_number,voucher_voucher_type,trn_inventoryentries_amount,trn_inventoryentries_id,trn_inventoryentries_quantity,trn_inventoryentries_rate,trn_inventoryentries_stockitem_name,trn_ledgerentries_amount,trn_ledgerentries_id,trn_ledgerentries_is_debit,trn_ledgerentries_ledger_name</FIELDS>
                    </LINE>

                    <FIELD NAME="voucher_amount"><SET>$Amount</SET></FIELD>
                    <FIELD NAME="voucher_date"><SET>$Date</SET></FIELD>
                    <FIELD NAME="voucher_id"><SET>$GUID</SET></FIELD>
                    <FIELD NAME="voucher_narration"><SET>$Narration</SET></FIELD>
                    <FIELD NAME="voucher_party_name"><SET>$PartyLedgerName</SET></FIELD>
                    <FIELD NAME="voucher_reference"><SET>$Reference</SET></FIELD>
                    <FIELD NAME="voucher_voucher_number"><SET>$VoucherNumber</SET></FIELD>
                    <FIELD NAME="voucher_voucher_type"><SET>$VoucherTypeName</SET></FIELD>

                    <FIELD NAME="trn_inventoryentries_amount"><SET>$Amount</SET></FIELD>
                    <FIELD NAME="trn_inventoryentries_id"><SET>$GUID</SET></FIELD>
                    <FIELD NAME="trn_inventoryentries_quantity"><SET>$BilledQty</SET></FIELD>
                    <FIELD NAME="trn_inventoryentries_rate"><SET>$Rate</SET></FIELD>
                    <FIELD NAME="trn_inventoryentries_stockitem_name"><SET>$StockItemName</SET></FIELD>

                    <FIELD NAME="trn_ledgerentries_amount"><SET>$Amount</SET></FIELD>
                    <FIELD NAME="trn_ledgerentries_id"><SET>$GUID</SET></FIELD>
                    <FIELD NAME="trn_ledgerentries_is_debit"><SET>$IsDebit</SET></FIELD>
                    <FIELD NAME="trn_ledgerentries_ledger_name"><SET>$LedgerName</SET></FIELD>

                    <COLLECTION NAME="MasterCollection">
                        <TYPE>Voucher</TYPE>
                        <COMPANY>{self.company_name}</COMPANY>
                        <CHILDOF>$$VchTypeDayBook</CHILDOF>

                        <FETCH>GUID</FETCH>
                        <FETCH>VoucherNumber</FETCH>
                        <FETCH>VoucherTypeName</FETCH>
                        <FETCH>Date</FETCH>
                        <FETCH>Amount</FETCH>
                        <FETCH>Reference</FETCH>
                        <FETCH>Narration</FETCH>
                        <FETCH>PartyLedgerName</FETCH>
                        <FETCH>IsCancelled</FETCH>
                        <FETCH>IsOptional</FETCH>

                        <WALK>AllInventoryEntries</WALK>
                        <WALK>AllLedgerEntries</WALK>
                    </COLLECTION>
                </TDLMESSAGE>
            </TDL>
        </DESC>
    </BODY>
</ENVELOPE>"""
        
        return tdl_xml
    
    def create_simple_master_tdl(self, collection_type: str) -> str:
        """Create simple master TDL for individual collections."""
        
        # Map collection types to Tally types
        tally_type_mapping = {
            'Group': 'Group',
            'Ledger': 'Ledger', 
            'StockItem': 'StockItem',
            'VoucherType': 'VoucherType',
            'Godown': 'Godown',
            'StockGroup': 'StockGroup',
            'StockCategory': 'StockCategory',
            'Unit': 'Unit',
            'CostCategory': 'CostCategory',
            'CostCentre': 'CostCentre',
            'Employee': 'Employee',
            'PayHead': 'PayHead',
            'AttendanceType': 'AttendanceType'
        }
        
        tally_type = tally_type_mapping.get(collection_type, collection_type)
        
        tdl_xml = f"""<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Data</TYPE>
        <ID>SimpleMaster_{collection_type}</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>XML (Data Interchange)</SVEXPORTFORMAT>
                <SVCOMPANYNAME>{self.company_name}</SVCOMPANYNAME>
            </STATICVARIABLES>
            <TDL>
                <TDLMESSAGE>
                    <REPORT NAME="SimpleMaster_{collection_type}">
                        <FORMS>SimpleMasterForm_{collection_type}</FORMS>
                    </REPORT>
                    <FORM NAME="SimpleMasterForm_{collection_type}">
                        <PARTS>SimpleMasterPart_{collection_type}</PARTS>
                    </FORM>
                    <PART NAME="SimpleMasterPart_{collection_type}">
                        <LINES>SimpleMasterLine_{collection_type}</LINES>
                        <REPEAT>SimpleMasterLine_{collection_type} : SimpleMasterCollection_{collection_type}</REPEAT>
                        <SCROLLED>Vertical</SCROLLED>
                    </PART>
                    <LINE NAME="SimpleMasterLine_{collection_type}">
                        <FIELDS>guid,name,parent,alias,description</FIELDS>
                    </LINE>

                    <FIELD NAME="guid"><SET>$GUID</SET></FIELD>
                    <FIELD NAME="name"><SET>$Name</SET></FIELD>
                    <FIELD NAME="parent"><SET>$Parent</SET></FIELD>
                    <FIELD NAME="alias"><SET>$OnlyAlias</SET></FIELD>
                    <FIELD NAME="description"><SET>$Description</SET></FIELD>

                    <COLLECTION NAME="SimpleMasterCollection_{collection_type}">
                        <TYPE>{tally_type}</TYPE>
                        <COMPANY>{self.company_name}</COMPANY>
                    </COLLECTION>
                </TDLMESSAGE>
            </TDL>
        </DESC>
    </BODY>
</ENVELOPE>"""
        
        return tdl_xml
    
    def send_tdl_request(self, tdl_xml: str) -> Optional[str]:
        """Send TDL request to Tally and return response."""
        try:
            logger.info(f"🔄 Sending TDL request to {self.base_url}")
            
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'Content-Length': str(len(tdl_xml.encode('utf-8')))
            }
            
            response = requests.post(
                self.base_url,
                data=tdl_xml.encode('utf-8'),
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info(f"✅ TDL request successful, response size: {len(response.text)} characters")
                return response.text
            else:
                logger.error(f"❌ TDL request failed with status: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ TDL request timed out after {self.timeout} seconds")
            return None
        except Exception as e:
            logger.error(f"❌ TDL request failed: {e}")
            return None
    
    def extract_transaction_data(self) -> Optional[str]:
        """Extract transaction data using proven WALK method."""
        logger.info("🔄 Extracting transaction data using proven WALK method")
        
        tdl_xml = self.create_proven_transaction_tdl()
        response = self.send_tdl_request(tdl_xml)
        
        if response:
            logger.info("✅ Transaction data extracted successfully")
            return response
        else:
            logger.error("❌ Failed to extract transaction data")
            return None
    
    def extract_master_data(self, collection_type: str) -> Optional[str]:
        """Extract master data for a specific collection type."""
        logger.info(f"🔄 Extracting master data for {collection_type}")
        
        tdl_xml = self.create_simple_master_tdl(collection_type)
        response = self.send_tdl_request(tdl_xml)
        
        if response:
            logger.info(f"✅ Master data extracted for {collection_type}")
            return response
        else:
            logger.error(f"❌ Failed to extract master data for {collection_type}")
            return None

def main():
    """Test the corrected WALK client."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    client = CorrectedWALKClient()
    
    print("🔍 Testing Corrected WALK-based TDL...")
    
    # Test transaction data first (most important)
    print("\n📊 Testing transaction data TDL...")
    transaction_tdl = client.create_proven_transaction_tdl()
    print(f"   Transaction TDL Size: {len(transaction_tdl)} characters")
    
    # Test with Tally
    response = client.extract_transaction_data()
    if response:
        print(f"   ✅ Transaction Response Size: {len(response)} characters")
    else:
        print(f"   ❌ Transaction extraction failed")
    
    # Test simple master collections
    print("\n📋 Testing simple master collections...")
    master_collections = ['Group', 'Ledger', 'StockItem', 'VoucherType', 'Godown']
    
    for collection in master_collections:
        print(f"\n   Testing {collection}...")
        tdl_xml = client.create_simple_master_tdl(collection)
        print(f"   TDL Size: {len(tdl_xml)} characters")
        
        # Test with Tally
        response = client.extract_master_data(collection)
        if response:
            print(f"   ✅ Response Size: {len(response)} characters")
        else:
            print(f"   ❌ Extraction failed")
    
    print("\n✅ Corrected WALK-based TDL test completed!")

if __name__ == "__main__":
    main()
