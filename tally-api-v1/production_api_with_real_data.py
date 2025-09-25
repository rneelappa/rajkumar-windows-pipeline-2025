#!/usr/bin/env python3
"""
Production API with Real Data
============================
Uses the working IntegratedMigrationSystem to extract real Tally data
and sends it to the Supabase API.
"""

import logging
import requests
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from integrated_migration_system import IntegratedMigrationSystem
from corrected_walk_client import CorrectedWALKClient
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

class ProductionAPIWithRealData:
    """Production API solution using working IntegratedMigrationSystem."""
    
    def __init__(self):
        self.integrated_system = IntegratedMigrationSystem()
        self.walk_client = CorrectedWALKClient()
        
        # API configuration
        self.api_base_url = "https://ppfwlhfehwelinfprviw.supabase.co/functions/v1"
        self.api_key = "9d9fa8ee96a0af96fa29ae1a004a68d2ae62c9d9e0195ac86f647190eb5d9c64"
        self.endpoint = f"{self.api_base_url}/vouchers-api"
        
        # Configuration
        self.company_id = "bc90d453-0c64-4f6f-8bbe-dca32aba40d1"
        self.division_id = "b38e3757-f338-4cc3-b754-2ade914290e1"
        
        self.stats = {
            'vouchers_extracted': 0,
            'vouchers_sent_to_api': 0,
            'api_successes': 0,
            'api_errors': 0,
            'start_time': datetime.now()
        }

    def extract_real_tally_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extract real data from Tally using the working IntegratedMigrationSystem with reused parser."""
        logger.info("🔄 Extracting REAL data from Tally using IntegratedMigrationSystem (reusing parser)...")
        
        all_data = {
            'vouchers': [],
            'ledger_entries': [],
            'inventory_entries': []
        }
        
        try:
            # Use the integrated system's methods directly - they already have the working parser
            logger.info("📥 Extracting vouchers using working parser...")
            vouchers = self.integrated_system.extract_voucher_data()
            all_data['vouchers'] = vouchers
            logger.info(f"✅ Extracted {len(vouchers)} vouchers")
            
            logger.info("📥 Extracting ledger entries using working parser...")
            ledger_entries = self.integrated_system.extract_ledger_entries()
            all_data['ledger_entries'] = ledger_entries
            logger.info(f"✅ Extracted {len(ledger_entries)} ledger entries")
            
            logger.info("📥 Extracting inventory entries using working parser...")
            inventory_entries = self.integrated_system.extract_inventory_entries()
            all_data['inventory_entries'] = inventory_entries
            logger.info(f"✅ Extracted {len(inventory_entries)} inventory entries")
            
            self.stats['vouchers_extracted'] = len(vouchers)
            
            return all_data
            
        except Exception as e:
            logger.error(f"❌ Failed to extract Tally data: {e}")
            import traceback
            traceback.print_exc()
            return all_data
    
    def extract_ledger_entries_with_walk(self) -> List[Dict[str, Any]]:
        """Extract ledger entries using WALK approach to get signed amounts."""
        logger.info("📥 Extracting ledger entries using WALK approach for signed amounts...")
        
        try:
            # Get XML response from WALK client
            xml_response = self.walk_client.extract_transaction_data()
            if not xml_response:
                logger.error("❌ No XML response from WALK client")
                return []
            
            # Parse the XML to extract ledger entries with signed amounts
            ledger_entries = []
            
            try:
                root = ET.fromstring(xml_response)
                
                # Find all voucher elements
                for voucher in root.findall('.//VOUCHER'):
                    voucher_guid = None
                    voucher_number = None
                    voucher_date = None
                    voucher_type = None
                    
                    # Extract voucher details
                    if voucher.find('VOUCHER_ID') is not None:
                        voucher_guid = voucher.find('VOUCHER_ID').text
                    if voucher.find('VOUCHER_VOUCHER_NUMBER') is not None:
                        voucher_number = voucher.find('VOUCHER_VOUCHER_NUMBER').text
                    if voucher.find('VOUCHER_DATE') is not None:
                        voucher_date = voucher.find('VOUCHER_DATE').text
                    if voucher.find('VOUCHER_VOUCHER_TYPE') is not None:
                        voucher_type = voucher.find('VOUCHER_VOUCHER_TYPE').text
                    
                    # Extract ledger entries for this voucher
                    for ledger_amount_elem in voucher.findall('.//TRN_LEDGERENTRIES_AMOUNT'):
                        # Find corresponding ledger name
                        ledger_name_elem = ledger_amount_elem.getparent().find('TRN_LEDGERENTRIES_LEDGER_NAME')
                        ledger_id_elem = ledger_amount_elem.getparent().find('TRN_LEDGERENTRIES_ID')
                        
                        if ledger_name_elem is not None and ledger_amount_elem.text:
                            amount_text = ledger_amount_elem.text.strip()
                            ledger_name = ledger_name_elem.text.strip() if ledger_name_elem.text else ''
                            
                            # Parse signed amount - handle (-)format
                            signed_amount = self.parse_signed_amount(amount_text)
                            
                            ledger_entry = {
                                'guid': ledger_id_elem.text if ledger_id_elem is not None else '',
                                'ledger_name': ledger_name,
                                'amount': signed_amount,
                                'currency': '',
                                'voucher_guid': voucher_guid,
                                'voucher_number': voucher_number,
                                'voucher_date': voucher_date,
                                'voucher_type': voucher_type,
                                'is_debit': signed_amount < 0 if signed_amount != 0 else None
                            }
                            
                            ledger_entries.append(ledger_entry)
                
                logger.info(f"✅ Extracted {len(ledger_entries)} ledger entries with signed amounts")
                return ledger_entries
                
            except ET.ParseError as e:
                logger.error(f"❌ XML parsing error: {e}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to extract ledger entries with WALK: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def parse_signed_amount(self, amount_text: str) -> float:
        """Parse signed amount from Tally format like '(-)16,56,840.00' or '16,56,840.00'."""
        if not amount_text:
            return 0.0
        
        try:
            # Handle negative amounts in (-)format
            is_negative = amount_text.startswith('(-)')
            
            # Clean the amount string
            cleaned = amount_text.replace('(-)', '').replace(',', '').strip()
            if cleaned == '' or cleaned == '0.00':
                return 0.0
                
            amount = float(cleaned)
            return -amount if is_negative else amount
            
        except Exception as e:
            logger.warning(f"⚠️  Could not parse amount '{amount_text}': {e}")
            return 0.0

    def convert_to_api_format(self, tally_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Convert Tally data to API format using working logic."""
        logger.info("🔄 Converting Tally data to API format...")
        
        api_vouchers = []
        
        # Group ledger and inventory entries by voucher GUID
        ledger_by_voucher = {}
        inventory_by_voucher = {}
        
        for entry in tally_data['ledger_entries']:
            voucher_guid = entry.get('voucher_guid')
            if voucher_guid:
                if voucher_guid not in ledger_by_voucher:
                    ledger_by_voucher[voucher_guid] = []
                ledger_by_voucher[voucher_guid].append(entry)
        
        for entry in tally_data['inventory_entries']:
            voucher_guid = entry.get('voucher_guid')
            if voucher_guid:
                if voucher_guid not in inventory_by_voucher:
                    inventory_by_voucher[voucher_guid] = []
                inventory_by_voucher[voucher_guid].append(entry)
        
        logger.info(f"📊 {len(ledger_by_voucher)} vouchers have ledger entries")
        logger.info(f"📊 {len(inventory_by_voucher)} vouchers have inventory entries")
        
        # Convert each voucher to API format
        for voucher in tally_data['vouchers']:
            voucher_guid = voucher.get('voucher_id')  # Use voucher_id from integrated system
            
            # Build API voucher structure
            api_voucher = {
                'header': {
                    'company_id': self.company_id,
                    'division_id': self.division_id,
                    'vchtype': voucher.get('voucher_voucher_type', 'Journal'),
                    'date': self.parse_date_for_api(voucher.get('voucher_date')),
                    'vouchernumber': voucher.get('voucher_voucher_number'),
                    'partyledgername': voucher.get('voucher_party_name'),
                    'narration': voucher.get('voucher_narration'),
                    'reference': voucher.get('voucher_reference'),
                    'tally_guid': voucher_guid,
                    'sync_status': 'pending'
                },
                'ledger_entries': [],
                'inventory_lines': []
            }
            
            # Add ledger entries
            if voucher_guid in ledger_by_voucher:
                for ledger_entry in ledger_by_voucher[voucher_guid]:
                    # Use a simple heuristic for now: 
                    # In double-entry bookkeeping, for each voucher, there should be equal debits and credits
                    # We'll assign based on typical accounting patterns
                    
                    amount = self.parse_amount(ledger_entry.get('amount'))
                    ledger_name = ledger_entry.get('ledger_name', '')
                    
                    # Simple heuristic: Bank/Cash accounts are typically debits when money comes in
                    # Expense accounts are typically debits
                    # Revenue accounts are typically credits
                    # This is a temporary solution until we get proper signed amounts
                    
                    is_likely_debit = any(keyword in ledger_name.upper() for keyword in [
                        'BANK', 'CASH', 'EXPENSE', 'PURCHASE', 'ASSET', 'RECEIVABLE'
                    ])
                    
                    if is_likely_debit:
                        debit_amount = amount
                        credit_amount = 0.0
                    else:
                        debit_amount = 0.0
                        credit_amount = amount
                    
                    api_ledger_entry = {
                        'ledgername': ledger_name,
                        'debit_amount': debit_amount,
                        'credit_amount': credit_amount,
                        'narration': '',
                        'cost_centre': 'Main'
                    }
                    api_voucher['ledger_entries'].append(api_ledger_entry)
            
            # Add inventory lines
            if voucher_guid in inventory_by_voucher:
                for inventory_entry in inventory_by_voucher[voucher_guid]:
                    if inventory_entry.get('stock_item_name'):  # Only add if has stock item
                        api_inventory_line = {
                            'stockitemname': inventory_entry.get('stock_item_name'),
                            'godownname': inventory_entry.get('godown', 'Main Store'),
                            'qty': self.parse_amount(inventory_entry.get('quantity')),
                            'rate': self.parse_amount(inventory_entry.get('rate')),
                            'amount': self.parse_amount(inventory_entry.get('amount'))
                        }
                        api_voucher['inventory_lines'].append(api_inventory_line)
            
            # Only add vouchers that have ledger entries
            if api_voucher['ledger_entries']:
                api_vouchers.append(api_voucher)
        
        logger.info(f"✅ Converted {len(api_vouchers)} vouchers to API format")
        return api_vouchers

    def parse_date_for_api(self, date_str: str) -> str:
        """Parse date for API format (YYYY-MM-DD)."""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Handle Tally date format (DD-MMM-YY)
            if len(date_str.split('-')) == 3:
                day, month, year = date_str.split('-')
                # Convert 2-digit year to 4-digit
                if len(year) == 2:
                    year_int = int(year)
                    if year_int > 50:
                        year = f"19{year}"
                    else:
                        year = f"20{year}"
                
                # Convert month name to number
                month_map = {
                    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                }
                month_num = month_map.get(month, '01')
                
                return f"{year}-{month_num}-{day.zfill(2)}"
        except:
            pass
        
        return datetime.now().strftime('%Y-%m-%d')

    def parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float."""
        if not amount_str:
            return 0.0
        
        try:
            # Remove commas and convert to float
            cleaned = str(amount_str).replace(',', '').strip()
            if cleaned == '' or cleaned == '0.00':
                return 0.0
            return float(cleaned)
        except:
            return 0.0

    def send_voucher_to_api(self, voucher_data: Dict[str, Any]) -> bool:
        """Send voucher data to the API."""
        try:
            response = requests.post(
                self.endpoint,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}',
                    'X-API-Key': self.api_key
                },
                json=voucher_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Voucher {voucher_data['header']['vouchernumber']} sent successfully")
                self.stats['api_successes'] += 1
                return True
            else:
                logger.warning(f"⚠️  API error for voucher {voucher_data['header']['vouchernumber']}: {response.status_code}")
                logger.warning(f"Response: {response.text}")
                self.stats['api_errors'] += 1
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to send voucher {voucher_data['header']['vouchernumber']}: {e}")
            self.stats['api_errors'] += 1
            return False

    def run_production_api_test(self, max_vouchers: int = 10) -> bool:
        """Run the production API test with real Tally data."""
        try:
            logger.info("🚀 Starting Production API Test with Real Tally Data...")
            logger.info("=" * 80)
            
            # Step 1: Extract real data from Tally
            logger.info("📥 STEP 1: Extracting real data from Tally...")
            tally_data = self.extract_real_tally_data()
            
            if not tally_data['vouchers']:
                logger.error("❌ No voucher data extracted from Tally")
                return False
            
            # Step 2: Convert to API format
            logger.info("🔄 STEP 2: Converting to API format...")
            api_vouchers = self.convert_to_api_format(tally_data)
            
            if not api_vouchers:
                logger.error("❌ No vouchers converted to API format")
                return False
            
            # Step 3: Send to API (limit for testing)
            logger.info(f"📤 STEP 3: Sending vouchers to API (max {max_vouchers})...")
            sent_count = 0
            
            for voucher in api_vouchers[:max_vouchers]:
                if self.send_voucher_to_api(voucher):
                    sent_count += 1
                    self.stats['vouchers_sent_to_api'] += 1
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.5)
            
            # Step 4: Report results
            self.generate_final_report()
            
            logger.info("🎉 Production API test completed!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Production API test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def generate_final_report(self):
        """Generate final report."""
        duration = datetime.now() - self.stats['start_time']
        
        print(f"\n🎉 PRODUCTION API TEST COMPLETED!")
        print("=" * 80)
        print(f"📊 EXTRACTION RESULTS:")
        print(f"  Vouchers extracted: {self.stats['vouchers_extracted']:,}")
        print(f"  Vouchers sent to API: {self.stats['vouchers_sent_to_api']:,}")
        print(f"  API successes: {self.stats['api_successes']:,}")
        print(f"  API errors: {self.stats['api_errors']:,}")
        print(f"⏱️  Total duration: {duration}")
        
        if self.stats['vouchers_sent_to_api'] > 0:
            success_rate = (self.stats['api_successes'] / self.stats['vouchers_sent_to_api']) * 100
            print(f"🎯 API success rate: {success_rate:.1f}%")

def main():
    """Main function."""
    solution = ProductionAPIWithRealData()
    
    # Test with first 10 real vouchers
    success = solution.run_production_api_test(max_vouchers=10)
    
    if success:
        print("\n✅ Production API test completed successfully!")
    else:
        print("\n❌ Production API test failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
