#!/usr/bin/env python3
"""
Ultra Simple Tally to Supabase Migration
One record at a time, no transactions, maximum error tolerance
"""

import argparse
import logging
import xml.etree.ElementTree as ET
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Any, Optional
from psycopg2.extras import RealDictCursor

from config_manager import config
from tally_client import TallyClient
from supabase_manager import SupabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class UltraSimpleMigration:
    def __init__(self):
        self.tally_client = TallyClient()
        self.supabase_manager = SupabaseManager()
        self.company_id = config.get_company_id()
        self.division_id = config.get_division_id()
        
    def safe_decimal(self, value: str) -> Optional[float]:
        """Convert string to decimal, handling commas and empty values."""
        if not value or value.strip() == '':
            return None
        try:
            cleaned_value = str(value).replace(',', '').strip()
            if cleaned_value == '':
                return None
            return float(cleaned_value)
        except (ValueError, TypeError):
            return None
    
    def safe_date(self, date_str: str) -> Optional[str]:
        """Convert Tally date format to PostgreSQL date format."""
        if not date_str or date_str.strip() == '':
            return None
        try:
            parts = date_str.strip().split('-')
            if len(parts) != 3:
                return None
            
            day = int(parts[0])
            month_str = parts[1]
            year = int(parts[2])
            
            if year < 50:
                year += 2000
            else:
                year += 1900
            
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            
            month = month_map.get(month_str)
            if not month:
                return None
            
            return f"{year:04d}-{month:02d}-{day:02d}"
        except (ValueError, TypeError, KeyError):
            return None
    
    def extract_data_from_tally(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extract data from Tally using the working TDL approach."""
        logger.info("🔄 Extracting data from Tally...")
        
        tdl_xml = self.tally_client.create_comprehensive_tdl()
        
        try:
            response = self.tally_client.send_tdl_request(tdl_xml)
            if not response:
                logger.error("❌ No response from Tally")
                return {}
            
            logger.info(f"✅ Received {len(response)} characters from Tally")
            
            # Parse the XML response
            root = ET.fromstring(response)
            
            # Extract data by parsing XML tags
            data = {
                'vouchers': [],
                'ledger_entries': [],
                'inventory_entries': []
            }
            
            # Parse voucher data
            for elem in root.iter():
                if elem.tag.startswith('VOUCHER_'):
                    voucher_data = {}
                    for child in elem.iter():
                        if child.tag.startswith('VOUCHER_'):
                            tag_name = child.tag.replace('VOUCHER_', '').lower()
                            voucher_data[tag_name] = child.text
                    
                    if voucher_data:
                        data['vouchers'].append(voucher_data)
            
            # Parse ledger entries
            for elem in root.iter():
                if elem.tag.startswith('TRN_LEDGERENTRIES_'):
                    ledger_data = {}
                    for child in elem.iter():
                        if child.tag.startswith('TRN_LEDGERENTRIES_'):
                            tag_name = child.tag.replace('TRN_LEDGERENTRIES_', '').lower()
                            ledger_data[tag_name] = child.text
                    
                    if ledger_data:
                        data['ledger_entries'].append(ledger_data)
            
            # Parse inventory entries
            for elem in root.iter():
                if elem.tag.startswith('TRN_INVENTORYENTRIES_'):
                    inventory_data = {}
                    for child in elem.iter():
                        if child.tag.startswith('TRN_INVENTORYENTRIES_'):
                            tag_name = child.tag.replace('TRN_INVENTORYENTRIES_', '').lower()
                            inventory_data[tag_name] = child.text
                    
                    if inventory_data:
                        data['inventory_entries'].append(inventory_data)
            
            logger.info(f"📊 Extracted data: {len(data['vouchers'])} vouchers, {len(data['ledger_entries'])} ledger entries, {len(data['inventory_entries'])} inventory entries")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error extracting data from Tally: {e}")
            return {}
    
    def insert_single_voucher(self, voucher_data: Dict[str, Any]) -> bool:
        """Insert a single voucher with individual connection."""
        try:
            if not self.supabase_manager.connect():
                return False
            
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            # Insert with minimal required fields only
            cursor.execute("""
                INSERT INTO vouchers (
                    guid, date, voucher_number, narration, company_id, division_id
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (guid) DO UPDATE SET
                    date = EXCLUDED.date,
                    voucher_number = EXCLUDED.voucher_number,
                    narration = EXCLUDED.narration
            """, (
                voucher_data.get('id'),
                self.safe_date(voucher_data.get('date')),
                voucher_data.get('voucher_number'),
                voucher_data.get('narration'),
                self.company_id,
                self.division_id
            ))
            
            self.supabase_manager.conn.commit()
            self.supabase_manager.disconnect()
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Error inserting voucher {voucher_data.get('id', 'unknown')}: {e}")
            try:
                self.supabase_manager.conn.rollback()
                self.supabase_manager.disconnect()
            except:
                pass
            return False
    
    def insert_single_ledger_entry(self, ledger_data: Dict[str, Any]) -> bool:
        """Insert a single ledger entry with individual connection."""
        try:
            if not self.supabase_manager.connect():
                return False
            
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            # Insert with minimal required fields only
            cursor.execute("""
                INSERT INTO ledger_entries (
                    guid, voucher_id, ledger_name, amount, company_id, division_id
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (guid) DO UPDATE SET
                    voucher_id = EXCLUDED.voucher_id,
                    ledger_name = EXCLUDED.ledger_name,
                    amount = EXCLUDED.amount
            """, (
                ledger_data.get('id'),
                ledger_data.get('id'),  # Same as voucher ID in flat structure
                ledger_data.get('ledger_name'),
                self.safe_decimal(ledger_data.get('amount')),
                self.company_id,
                self.division_id
            ))
            
            self.supabase_manager.conn.commit()
            self.supabase_manager.disconnect()
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Error inserting ledger entry {ledger_data.get('id', 'unknown')}: {e}")
            try:
                self.supabase_manager.conn.rollback()
                self.supabase_manager.disconnect()
            except:
                pass
            return False
    
    def insert_single_inventory_entry(self, inventory_data: Dict[str, Any]) -> bool:
        """Insert a single inventory entry with individual connection."""
        try:
            if not self.supabase_manager.connect():
                return False
            
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            # Insert with minimal required fields only
            cursor.execute("""
                INSERT INTO inventory_entries (
                    guid, voucher_id, stock_item_name, quantity, rate, amount, company_id, division_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (guid) DO UPDATE SET
                    voucher_id = EXCLUDED.voucher_id,
                    stock_item_name = EXCLUDED.stock_item_name,
                    quantity = EXCLUDED.quantity,
                    rate = EXCLUDED.rate,
                    amount = EXCLUDED.amount
            """, (
                inventory_data.get('id'),
                inventory_data.get('id'),  # Same as voucher ID in flat structure
                inventory_data.get('stockitem_name'),
                self.safe_decimal(inventory_data.get('quantity')),
                self.safe_decimal(inventory_data.get('rate')),
                self.safe_decimal(inventory_data.get('amount')),
                self.company_id,
                self.division_id
            ))
            
            self.supabase_manager.conn.commit()
            self.supabase_manager.disconnect()
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Error inserting inventory entry {inventory_data.get('id', 'unknown')}: {e}")
            try:
                self.supabase_manager.conn.rollback()
                self.supabase_manager.disconnect()
            except:
                pass
            return False
    
    def migrate_data_ultra_simple(self):
        """Ultra simple migration - one record at a time."""
        logger.info("🚀 Starting ultra simple Tally to Supabase data migration...")
        
        # Step 1: Extract data from Tally
        data = self.extract_data_from_tally()
        if not data:
            logger.error("❌ No data extracted from Tally")
            return False
        
        # Step 2: Insert vouchers one by one
        vouchers = data.get('vouchers', [])
        logger.info(f"🔄 Inserting {len(vouchers)} vouchers one by one...")
        
        success_count = 0
        error_count = 0
        
        for i, voucher_data in enumerate(vouchers):
            if self.insert_single_voucher(voucher_data):
                success_count += 1
            else:
                error_count += 1
            
            if (i + 1) % 10 == 0:
                logger.info(f"📊 Progress: {i + 1}/{len(vouchers)} vouchers processed")
        
        logger.info(f"✅ Vouchers: {success_count} success, {error_count} errors")
        
        # Step 3: Insert ledger entries one by one
        ledger_entries = data.get('ledger_entries', [])
        logger.info(f"🔄 Inserting {len(ledger_entries)} ledger entries one by one...")
        
        success_count = 0
        error_count = 0
        
        for i, ledger_data in enumerate(ledger_entries):
            if self.insert_single_ledger_entry(ledger_data):
                success_count += 1
            else:
                error_count += 1
            
            if (i + 1) % 10 == 0:
                logger.info(f"📊 Progress: {i + 1}/{len(ledger_entries)} ledger entries processed")
        
        logger.info(f"✅ Ledger entries: {success_count} success, {error_count} errors")
        
        # Step 4: Insert inventory entries one by one
        inventory_entries = data.get('inventory_entries', [])
        logger.info(f"🔄 Inserting {len(inventory_entries)} inventory entries one by one...")
        
        success_count = 0
        error_count = 0
        
        for i, inventory_data in enumerate(inventory_entries):
            if self.insert_single_inventory_entry(inventory_data):
                success_count += 1
            else:
                error_count += 1
            
            if (i + 1) % 10 == 0:
                logger.info(f"📊 Progress: {i + 1}/{len(inventory_entries)} inventory entries processed")
        
        logger.info(f"✅ Inventory entries: {success_count} success, {error_count} errors")
        
        logger.info("✅ Ultra simple data migration completed!")
        return True

def main():
    parser = argparse.ArgumentParser(description='Ultra Simple Tally to Supabase Migration')
    parser.add_argument('--action', choices=['migrate', 'extract-only'], 
                       default='migrate', help='Action to perform')
    
    args = parser.parse_args()
    
    migration = UltraSimpleMigration()
    
    if args.action == 'extract-only':
        logger.info("🔄 Extracting data from Tally only...")
        data = migration.extract_data_from_tally()
        logger.info(f"📊 Extracted {len(data)} data types")
        for data_type, records in data.items():
            logger.info(f"  - {data_type}: {len(records)} records")
    else:
        migration.migrate_data_ultra_simple()

if __name__ == "__main__":
    main()
