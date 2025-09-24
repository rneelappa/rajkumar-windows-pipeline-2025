#!/usr/bin/env python3
"""
Tally Client for Python
Sends TDL XML messages to Tally server via HTTP requests.
Based on C# implementation for comprehensive voucher data export.
"""

import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import json
import time
from datetime import datetime
import yaml
import os
from config_manager import config


class TallyClient:
    """Client for communicating with Tally server via HTTP."""
    
    def __init__(self, base_url: str = None, timeout: int = None):
        """
        Initialize Tally client.
        
        Args:
            base_url: Base URL of the Tally server (if None, uses config)
            timeout: Request timeout in seconds (if None, uses config)
        """
        self.base_url = (base_url or config.get_tally_url()).rstrip('/')
        self.timeout = timeout or config.get_tally_timeout()
        self.session = requests.Session()
        
        # Set headers for Tally requests
        self.session.headers.update({
            'Content-Type': 'application/xml',
            'Accept': 'application/xml',
            'User-Agent': 'Python-TallyClient/1.0'
        })
        
        # Add ngrok-skip-browser-warning header to avoid ngrok browser warning
        self.session.headers.update({
            'ngrok-skip-browser-warning': 'true'
        })
    
    def test_connection(self) -> bool:
        """
        Test connection to Tally server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/", timeout=self.timeout)
            if response.status_code == 200:
                print(f"✅ Connection successful to {self.base_url}")
                print(f"Response: {response.text}")
                return True
            else:
                print(f"❌ Connection failed. Status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def create_comprehensive_tdl(self, company_name: str = None) -> str:
        """
        Create comprehensive TDL XML message for voucher data export.
        Based on the C# implementation.
        
        Args:
            company_name: Name of the company in Tally (if None, uses config)
            
        Returns:
            TDL XML message string
        """
        company_name = company_name or config.get_tally_company_name()
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
        <SVCOMPANYNAME>{company_name}</SVCOMPANYNAME>
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
            <FIELDS>voucher_amount,voucher_date,voucher_id,voucher_narration,voucher_party_name,voucher_reference,voucher_voucher_number,voucher_voucher_type,trn_inventoryentries_amount,trn_inventoryentries_id,trn_inventoryentries_quantity,trn_inventoryentries_rate,trn_inventoryentries_stockitem_name,trn_ledgerentries_amount,trn_ledgerentries_id,trn_ledgerentries_is_debit,trn_ledgerentries_ledger_name,trn_employee_guid,trn_employee_category,trn_employee_name,trn_employee_amount,trn_employee_sort_order,trn_payhead_guid,trn_payhead_category,trn_payhead_employee_name,trn_payhead_employee_sort_order,trn_payhead_name,trn_payhead_sort_order,trn_payhead_amount,trn_attendance_guid,trn_attendance_employee_name,trn_attendance_type,trn_attendance_time_value,trn_attendance_type_value</FIELDS>
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

          <FIELD NAME="trn_employee_guid"><SET>$GUID</SET></FIELD>
          <FIELD NAME="trn_employee_category"><SET>$Category</SET></FIELD>
          <FIELD NAME="trn_employee_name"><SET>$EmployeeName</SET></FIELD>
          <FIELD NAME="trn_employee_amount"><SET>$Amount</SET></FIELD>
          <FIELD NAME="trn_employee_sort_order"><SET>$EmployeeSortOrder</SET></FIELD>

          <FIELD NAME="trn_payhead_guid"><SET>$GUID</SET></FIELD>
          <FIELD NAME="trn_payhead_category"><SET>$Category</SET></FIELD>
          <FIELD NAME="trn_payhead_employee_name"><SET>$EmployeeName</SET></FIELD>
          <FIELD NAME="trn_payhead_employee_sort_order"><SET>$EmployeeSortOrder</SET></FIELD>
          <FIELD NAME="trn_payhead_name"><SET>$PayheadName</SET></FIELD>
          <FIELD NAME="trn_payhead_sort_order"><SET>$PayheadSortOrder</SET></FIELD>
          <FIELD NAME="trn_payhead_amount"><SET>$Amount</SET></FIELD>

          <FIELD NAME="trn_attendance_guid"><SET>$GUID</SET></FIELD>
          <FIELD NAME="trn_attendance_employee_name"><SET>$Name</SET></FIELD>
          <FIELD NAME="trn_attendance_type"><SET>$AttendanceType</SET></FIELD>
          <FIELD NAME="trn_attendance_time_value"><SET>$AttdTypeTimeValue</SET></FIELD>
          <FIELD NAME="trn_attendance_type_value"><SET>$AttdTypeValue</SET></FIELD>

          <COLLECTION NAME="MasterCollection">
            <TYPE>Voucher</TYPE>
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

            <WALK>AllInventoryEntries.AccountingAllocations</WALK>
            <WALK>AllInventoryEntries.BatchAllocations</WALK>
            <WALK>AllInventoryEntries.CostCategoryAllocations</WALK>
            <WALK>AllInventoryEntries.CostCentreAllocations</WALK>
            <WALK>AllInventoryEntries.BillAllocations</WALK>
            <WALK>AllInventoryEntries.CostTrackingAllocations</WALK>

            <WALK>AllLedgerEntries.BillAllocations</WALK>
            <WALK>AllLedgerEntries.CostCategoryAllocations</WALK>
            <WALK>AllLedgerEntries.CostCentreAllocations</WALK>
            <WALK>AllLedgerEntries.TaxAllocations</WALK>

            <WALK>CategoryEntry.EmployeeEntry</WALK>
            <WALK>CategoryEntry.EmployeeEntry.PayheadAllocations</WALK>
            <WALK>AttendanceEntries</WALK>

            <FILTER>NotCancelled</FILTER>
            <FILTER>NotOptional</FILTER>
          </COLLECTION>

          <SYSTEM TYPE="Formulae" NAME="NotCancelled">NOT $IsCancelled</SYSTEM>
          <SYSTEM TYPE="Formulae" NAME="NotOptional">NOT $IsOptional</SYSTEM>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""
        
        return tdl_xml

    def create_yaml_based_tdl(self, report_config: dict, company_name: str = None) -> str:
        """
        Create TDL XML based on YAML configuration approach.
        This replicates the successful approach from tally_exporter.py and tally-export-config.yaml.
        
        Args:
            report_config: Dictionary containing report configuration (name, collection, fields, etc.)
            company_name: Name of the company in Tally
            
        Returns:
            TDL XML message string
        """
        company_name = company_name or config.get_tally_company_name()
        try:
            # XML header based on successful approach
            xml_parts = [
                '<ENVELOPE>',
                '<HEADER>',
                '<VERSION>1</VERSION>',
                '<TALLYREQUEST>Export</TALLYREQUEST>',
                '<TYPE>Data</TYPE>',
                f'<ID>{report_config["name"]}</ID>',
                '</HEADER>',
                '<BODY>',
                '<DESC>',
                '<STATICVARIABLES>',
                '<SVEXPORTFORMAT>XML (Data Interchange)</SVEXPORTFORMAT>',
                f'<SVCOMPANYNAME>{company_name}</SVCOMPANYNAME>',
                '</STATICVARIABLES>',
                '<TDL>',
                '<TDLMESSAGE>',
                f'<REPORT NAME="{report_config["name"]}">',
                '<FORMS>MyForm</FORMS>',
                '</REPORT>',
                '<FORM NAME="MyForm">',
                '<PARTS>MyPart</PARTS>',
                '</FORM>',
                '<PART NAME="MyPart">',
                '<LINES>MyLine</LINES>',
                '<REPEAT>MyLine : MyCollection</REPEAT>',
                '<SCROLLED>Vertical</SCROLLED>',
                '</PART>',
                '<LINE NAME="MyLine">',
                '<FIELDS>' + ','.join([f'F{i+1}' for i in range(len(report_config['fields']))]) + '</FIELDS>',
                '</LINE>'
            ]
            
            # Field definitions
            for i, field in enumerate(report_config['fields']):
                field_name = f"F{i+1}"
                field_expr = field['field']
                field_type = field.get('type', 'text')
                
                # Generate TDL expression based on type
                if field_type == 'text':
                    tdl_expr = f'${field_expr}'
                elif field_type == 'logical':
                    tdl_expr = f'if ${field_expr} then 1 else 0'
                elif field_type == 'date':
                    tdl_expr = f'if $$IsEmpty:${field_expr} then "" else $$PyrlYYYYMMDDFormat:${field_expr}:"-"'
                elif field_type == 'amount':
                    tdl_expr = f'$$StringFindAndReplace:(if $$IsDebit:${field_expr} then -$$NumValue:${field_expr} else $$NumValue:${field_expr}):"(-)":"-"'
                elif field_type == 'quantity':
                    tdl_expr = f'$$StringFindAndReplace:(if $$IsInwards:${field_expr} then $$Number:$$String:${field_expr}:"TailUnits" else -$$Number:$$String:${field_expr}:"TailUnits"):"(-)":"-"'
                elif field_type == 'rate':
                    tdl_expr = f'if $$IsEmpty:${field_expr} then 0 else $$Number:${field_expr}'
                elif field_type == 'number':
                    tdl_expr = f'if $$IsEmpty:${field_expr} then "0" else $$String:${field_expr}'
                else:
                    tdl_expr = f'${field_expr}'
                
                xml_parts.append(f'<FIELD NAME="{field_name}"><SET>{tdl_expr}</SET></FIELD>')
            
            # Collection definition
            collection_name = report_config['collection']
            xml_parts.append('<COLLECTION NAME="MyCollection">')
            xml_parts.append(f'<TYPE>{collection_name}</TYPE>')
            
            # Add fetch list if specified
            if 'fetch' in report_config and report_config['fetch']:
                for item in report_config['fetch']:
                    xml_parts.append(f'<FETCH>{item}</FETCH>')
            
            # Add filters if specified
            if 'filters' in report_config and report_config['filters']:
                for fltr in report_config['filters']:
                    xml_parts.append(f'<FILTER>{fltr}</FILTER>')
            
            xml_parts.append('</COLLECTION>')
            xml_parts.append('</TDLMESSAGE>')
            xml_parts.append('</TDL>')
            xml_parts.append('</DESC>')
            xml_parts.append('</BODY>')
            xml_parts.append('</ENVELOPE>')
            
            return '\n'.join(xml_parts)
            
        except Exception as e:
            print(f"Error generating YAML-based TDL for {report_config.get('name', 'Unknown')}: {e}")
            return ""

    def load_yaml_config(self, yaml_file: str = "tally-export-config.yaml") -> Dict[str, List[Dict]]:
        """
        Load YAML configuration file for TDL generation.
        
        Args:
            yaml_file: Path to the YAML configuration file
            
        Returns:
            Dictionary containing master and transaction report configurations
        """
        try:
            if not os.path.exists(yaml_file):
                print(f"Warning: YAML config file '{yaml_file}' not found")
                return {"master": [], "transaction": []}
            
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            return config
        except Exception as e:
            print(f"Error loading YAML config: {e}")
            return {"master": [], "transaction": []}

    def export_from_yaml_config(self, yaml_file: str = "tally-export-config.yaml", 
                               company_name: str = None,
                               report_types: List[str] = None) -> Dict[str, str]:
        """
        Export data using YAML configuration approach.
        Focuses on transaction data only (not master data).
        
        Args:
            yaml_file: Path to the YAML configuration file
            company_name: Name of the company in Tally
            report_types: List of report types to process (defaults to ['transaction'] only)
            
        Returns:
            Dictionary mapping report names to XML responses
        """
        company_name = company_name or config.get_tally_company_name()
        config = self.load_yaml_config(yaml_file)
        results = {}
        
        if report_types is None:
            report_types = ['transaction']  # Focus only on transaction data
        
        # Combine reports to process
        reports_to_process = []
        for report_type in report_types:
            if report_type in config:
                reports_to_process.extend(config[report_type])
        
        print(f"🚀 Processing {len(reports_to_process)} transaction reports from YAML config...")
        
        for report in reports_to_process:
            report_name = report['name']
            print(f"📋 Processing transaction report: {report_name}...")
            
            try:
                # Generate TDL XML from YAML config
                tdl_xml = self.create_yaml_based_tdl(report, company_name)
                if not tdl_xml:
                    print(f"❌ Failed to generate TDL for {report_name}")
                    continue
                
                # Send request to Tally
                response = self.send_tdl_request(tdl_xml)
                if response:
                    results[report_name] = response
                    print(f"✅ Successfully exported {report_name}")
                else:
                    print(f"❌ Failed to export {report_name}")
                    
            except Exception as e:
                print(f"❌ Error processing {report_name}: {e}")
        
        return results

    def create_nested_tdl(self, company_name: str = None) -> str:
        """
        Create nested TDL XML message for hierarchical voucher data export.
        This implementation uses ##AllLedgerEntries and ##AllInventoryEntries
        to capture nested data in a simplified structure.
        
        Args:
            company_name: Name of the company in Tally
            
        Returns:
            Nested TDL XML message string
        """
        company_name = company_name or config.get_tally_company_name()
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
        <SVCOMPANYNAME>{company_name}</SVCOMPANYNAME>
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
            <LINES>MasterVoucherLine</LINES>
            <REPEAT>MasterVoucherLine : MasterCollection</REPEAT>
            <SCROLLED>Vertical</SCROLLED>
          </PART>

          <LINE NAME="MasterVoucherLine">
            <FIELDS>voucher_amount, voucher_date, voucher_id, voucher_narration, voucher_party_name, voucher_reference, voucher_voucher_number, voucher_voucher_type, ledger_entries, inventory_entries</FIELDS>
          </LINE>

          <FIELD NAME="voucher_amount"><SET>$Amount</SET></FIELD>
          <FIELD NAME="voucher_date"><SET>$Date</SET></FIELD>
          <FIELD NAME="voucher_id"><SET>$Guid</SET></FIELD>
          <FIELD NAME="voucher_narration"><SET>$Narration</SET></FIELD>
          <FIELD NAME="voucher_party_name"><SET>$PartyLedgerName</SET></FIELD>
          <FIELD NAME="voucher_reference"><SET>$Reference</SET></FIELD>
          <FIELD NAME="voucher_voucher_number"><SET>$VoucherNumber</SET></FIELD>
          <FIELD NAME="voucher_voucher_type"><SET>$VoucherTypeName</SET></FIELD>
          
          <FIELD NAME="trn_ledgerentries_amount"><SET>$Amount</SET></FIELD>
          <FIELD NAME="trn_ledgerentries_id"><SET>$Guid</SET></FIELD>
          <FIELD NAME="trn_ledgerentries_is_debit"><SET>$IsDebit</SET></FIELD>
          <FIELD NAME="trn_ledgerentries_ledger_name"><SET>$LedgerName</SET></FIELD>

          <FIELD NAME="trn_inventoryentries_amount"><SET>$Amount</SET></FIELD>
          <FIELD NAME="trn_inventoryentries_id"><SET>$Guid</SET></FIELD>
          <FIELD NAME="trn_inventoryentries_quantity"><SET>$BilledQty</SET></FIELD>
          <FIELD NAME="trn_inventoryentries_rate"><SET>$Rate</SET></FIELD>
          <FIELD NAME="trn_inventoryentries_stockitem_name"><SET>$StockItemName</SET></FIELD>

          <FIELD NAME="ledger_entries"><SET>##AllLedgerEntries</SET></FIELD>
          <FIELD NAME="inventory_entries"><SET>##AllInventoryEntries</SET></FIELD>
          
          <COLLECTION NAME="MasterCollection">
            <TYPE>Voucher</TYPE>
            <COMPANY>{company_name}</COMPANY>
            <CHILDOF>$$VchTypeDayBook</CHILDOF>
            <FETCH>Guid, VoucherNumber, VoucherTypeName, Date, Amount, Reference, Narration, PartyLedgerName, IsCancelled, IsOptional</FETCH>
            <WALK>AllInventoryEntries, AllLedgerEntries</WALK>
            <FILTER>NotCancelled</FILTER>
            <FILTER>NotOptional</FILTER>
          </COLLECTION>

          <SYSTEM TYPE="Formulae" NAME="NotCancelled">NOT $IsCancelled</SYSTEM>
          <SYSTEM TYPE="Formulae" NAME="NotOptional">NOT $IsOptional</SYSTEM>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""
        
        return tdl_xml
    
    def create_basic_voucher_query(self, company_name: str = None) -> str:
        """
        Create a basic TDL query for voucher data that should work reliably.
        
        Args:
            company_name: Name of the company in Tally
            
        Returns:
            Basic TDL XML message string
        """
        company_name = company_name or config.get_tally_company_name()
        tdl_xml = f"""<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Data</TYPE>
    <ID>VoucherExport</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>XML (Data Interchange)</SVEXPORTFORMAT>
        <SVCOMPANYNAME>{company_name}</SVCOMPANYNAME>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <REPORT NAME="VoucherExport">
            <FORMS>VoucherForm</FORMS>
          </REPORT>
          <FORM NAME="VoucherForm">
            <PARTS>VoucherPart</PARTS>
          </FORM>
          <PART NAME="VoucherPart">
            <LINES>VoucherLine</LINES>
            <REPEAT>VoucherLine : VoucherCollection</REPEAT>
          </PART>
          <LINE NAME="VoucherLine">
            <FIELDS>voucher_amount,voucher_date,voucher_id,voucher_narration,voucher_party_name,voucher_reference,voucher_voucher_number,voucher_voucher_type</FIELDS>
          </LINE>

          <FIELD NAME="voucher_amount"><SET>$Amount</SET></FIELD>
          <FIELD NAME="voucher_date"><SET>$Date</SET></FIELD>
          <FIELD NAME="voucher_id"><SET>$GUID</SET></FIELD>
          <FIELD NAME="voucher_narration"><SET>$Narration</SET></FIELD>
          <FIELD NAME="voucher_party_name"><SET>$PartyLedgerName</SET></FIELD>
          <FIELD NAME="voucher_reference"><SET>$Reference</SET></FIELD>
          <FIELD NAME="voucher_voucher_number"><SET>$VoucherNumber</SET></FIELD>
          <FIELD NAME="voucher_voucher_type"><SET>$VoucherTypeName</SET></FIELD>

          <COLLECTION NAME="VoucherCollection">
            <TYPE>Voucher</TYPE>
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
            <FILTER>NotCancelled</FILTER>
            <FILTER>NotOptional</FILTER>
          </COLLECTION>

          <SYSTEM TYPE="Formulae" NAME="NotCancelled">NOT $IsCancelled</SYSTEM>
          <SYSTEM TYPE="Formulae" NAME="NotOptional">NOT $IsOptional</SYSTEM>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""
        
        return tdl_xml

    def create_simple_voucher_query(self, company_name: str = None) -> str:
        """
        Create a simple TDL query for voucher data.
        
        Args:
            company_name: Name of the company in Tally
            
        Returns:
            Simple TDL XML message string
        """
        company_name = company_name or config.get_tally_company_name()
        tdl_xml = f"""<ENVELOPE>
  <HEADER>
    <VERSION>1</VERSION>
    <TALLYREQUEST>Export</TALLYREQUEST>
    <TYPE>Data</TYPE>
    <ID>VoucherData</ID>
  </HEADER>
  <BODY>
    <DESC>
      <STATICVARIABLES>
        <SVEXPORTFORMAT>XML (Data Interchange)</SVEXPORTFORMAT>
        <SVCOMPANYNAME>{company_name}</SVCOMPANYNAME>
      </STATICVARIABLES>
      <TDL>
        <TDLMESSAGE>
          <REPORT NAME="VoucherReport">
            <FORMS>VoucherForm</FORMS>
          </REPORT>
          <FORM NAME="VoucherForm">
            <PARTS>VoucherPart</PARTS>
          </FORM>
          <PART NAME="VoucherPart">
            <LINES>VoucherLine</LINES>
            <REPEAT>VoucherLine : VoucherCollection</REPEAT>
          </PART>
          <LINE NAME="VoucherLine">
            <FIELDS>voucher_amount,voucher_date,voucher_id,voucher_narration,voucher_party_name,voucher_reference,voucher_voucher_number,voucher_voucher_type</FIELDS>
          </LINE>

          <FIELD NAME="voucher_amount"><SET>$Amount</SET></FIELD>
          <FIELD NAME="voucher_date"><SET>$Date</SET></FIELD>
          <FIELD NAME="voucher_id"><SET>$GUID</SET></FIELD>
          <FIELD NAME="voucher_narration"><SET>$Narration</SET></FIELD>
          <FIELD NAME="voucher_party_name"><SET>$PartyLedgerName</SET></FIELD>
          <FIELD NAME="voucher_reference"><SET>$Reference</SET></FIELD>
          <FIELD NAME="voucher_voucher_number"><SET>$VoucherNumber</SET></FIELD>
          <FIELD NAME="voucher_voucher_type"><SET>$VoucherTypeName</SET></FIELD>

          <COLLECTION NAME="VoucherCollection">
            <TYPE>Voucher</TYPE>
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
            <FILTER>NotCancelled</FILTER>
            <FILTER>NotOptional</FILTER>
          </COLLECTION>

          <SYSTEM TYPE="Formulae" NAME="NotCancelled">NOT $IsCancelled</SYSTEM>
          <SYSTEM TYPE="Formulae" NAME="NotOptional">NOT $IsOptional</SYSTEM>
        </TDLMESSAGE>
      </TDL>
    </DESC>
  </BODY>
</ENVELOPE>"""
        
        return tdl_xml
    
    def send_tdl_request(self, tdl_xml: str, endpoint: str = "/") -> Optional[str]:
        """
        Send TDL XML request to Tally server.
        
        Args:
            tdl_xml: TDL XML message to send
            endpoint: API endpoint (default: "/")
            
        Returns:
            Response text if successful, None if failed
        """
        try:
            url = f"{self.base_url}{endpoint}"
            print(f"📤 Sending TDL request to: {url}")
            print(f"📋 Request size: {len(tdl_xml)} characters")
            
            response = self.session.post(
                url,
                data=tdl_xml,
                timeout=self.timeout
            )
            
            print(f"📥 Response status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Request successful!")
                return response.text
            else:
                print(f"❌ Request failed with status: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            return None
    
    def export_voucher_data(self, company_name: str = None, 
                          query_type: str = "basic") -> Optional[str]:
        """
        Export voucher data from Tally.
        
        Args:
            company_name: Name of the company in Tally
            query_type: Type of query - "basic", "simple", "comprehensive", or "nested"
            
        Returns:
            XML response data if successful, None if failed
        """
        if query_type == "nested":
            tdl_xml = self.create_nested_tdl(company_name)
            print("🔍 Using nested TDL query (hierarchical structure)...")
            print("⏳ This may take 15-30 seconds to process...")
        elif query_type == "yaml":
            print("🔍 Using YAML-based TDL query (transaction data only)...")
            print("⏳ This may take 30-60 seconds to process transaction reports...")
            results = self.export_from_yaml_config(company_name=company_name)
            
            if results:
                print(f"\n🎉 Successfully exported {len(results)} reports!")
                for report_name, response in results.items():
                    if save_file:
                        filename = f"xml-files/yaml_export_{report_name}.xml"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(response)
                        print(f"💾 {report_name} saved to: {filename}")
                    else:
                        print(f"📊 {report_name}: {len(response)} characters")
                return True
            else:
                print("❌ No reports were successfully exported")
                return False
        elif query_type == "comprehensive":
            tdl_xml = self.create_comprehensive_tdl(company_name)
            print("🔍 Using comprehensive TDL query...")
            print("⏳ This may take 10-20 seconds to process...")
        elif query_type == "simple":
            tdl_xml = self.create_simple_voucher_query(company_name)
            print("🔍 Using simple TDL query...")
        else:  # basic
            tdl_xml = self.create_basic_voucher_query(company_name)
            print("🔍 Using basic TDL query...")
        
        return self.send_tdl_request(tdl_xml)
    
    def save_response_to_file(self, response_data: str, filename: str = None) -> str:
        """
        Save response data to file.
        
        Args:
            response_data: Response data to save
            filename: Output filename (optional)
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tally_response_{timestamp}.xml"
        
        filepath = f"xml-files/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response_data)
        
        print(f"💾 Response saved to: {filepath}")
        return filepath


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Tally Client for Python')
    parser.add_argument('--url', default='https://d06cf3740c40.ngrok-free.app', 
                       help='Tally server URL (default: ngrok URL)')
    parser.add_argument('--company', default='SKM IMPEX-CHENNAI-(24-25)', 
                       help='Company name in Tally')
    parser.add_argument('--test', action='store_true', help='Test connection only')
    parser.add_argument('--query-type', choices=['basic', 'simple', 'comprehensive', 'nested', 'yaml'], 
                       default='basic', help='Type of TDL query to use')
    parser.add_argument('--save', help='Save response to file')
    
    args = parser.parse_args()
    
    try:
        # Initialize client
        client = TallyClient(args.url)
        
        # Test connection
        if not client.test_connection():
            print("❌ Connection test failed. Please check your Tally server.")
            return 1
        
        if args.test:
            print("✅ Connection test completed successfully!")
            return 0
        
        # Export data
        print(f"\n🚀 Starting voucher data export...")
        print(f"Company: {args.company}")
        
        response_data = client.export_voucher_data(
            company_name=args.company,
            query_type=args.query_type
        )
        
        if response_data:
            print(f"\n📊 Export completed successfully!")
            print(f"Response size: {len(response_data)} characters")
            
            # Save to file if requested
            if args.save:
                filepath = client.save_response_to_file(response_data, args.save)
            else:
                # Auto-save with timestamp
                filepath = client.save_response_to_file(response_data)
            
            print(f"\n🎉 Data export completed!")
            print(f"📁 File saved: {filepath}")
            
        else:
            print("❌ Export failed!")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
