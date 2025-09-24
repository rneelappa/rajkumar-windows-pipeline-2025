#!/usr/bin/env python3
"""
Simple Tally to Supabase Migration
Focus on basic data migration without complex relationships
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

class SimpleTallyMigration:
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
    
    def insert_vouchers_simple(self, vouchers: List[Dict[str, Any]]):
        """Insert vouchers with minimal fields."""
        logger.info(f"🔄 Inserting {len(vouchers)} vouchers...")
        
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return
        
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            success_count = 0
            error_count = 0
            
            for voucher_data in vouchers:
                try:
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
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting voucher {voucher_data.get('id', 'unknown')}: {e}")
                    # Continue with next voucher instead of aborting transaction
            
            self.supabase_manager.conn.commit()
            logger.info(f"✅ Vouchers inserted: {success_count} success, {error_count} errors")
            
        except Exception as e:
            logger.error(f"❌ Error inserting vouchers: {e}")
            self.supabase_manager.conn.rollback()
        finally:
            self.supabase_manager.disconnect()
    
    def insert_ledger_entries_simple(self, ledger_entries: List[Dict[str, Any]]):
        """Insert ledger entries with minimal fields."""
        logger.info(f"🔄 Inserting {len(ledger_entries)} ledger entries...")
        
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return
        
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            success_count = 0
            error_count = 0
            
            for ledger_data in ledger_entries:
                try:
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
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting ledger entry {ledger_data.get('id', 'unknown')}: {e}")
                    # Continue with next entry
            
            self.supabase_manager.conn.commit()
            logger.info(f"✅ Ledger entries inserted: {success_count} success, {error_count} errors")
            
        except Exception as e:
            logger.error(f"❌ Error inserting ledger entries: {e}")
            self.supabase_manager.conn.rollback()
        finally:
            self.supabase_manager.disconnect()
    
    def insert_inventory_entries_simple(self, inventory_entries: List[Dict[str, Any]]):
        """Insert inventory entries with minimal fields."""
        logger.info(f"🔄 Inserting {len(inventory_entries)} inventory entries...")
        
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return
        
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            success_count = 0
            error_count = 0
            
            for inventory_data in inventory_entries:
                try:
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
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting inventory entry {inventory_data.get('id', 'unknown')}: {e}")
                    # Continue with next entry
            
            self.supabase_manager.conn.commit()
            logger.info(f"✅ Inventory entries inserted: {success_count} success, {error_count} errors")
            
        except Exception as e:
            logger.error(f"❌ Error inserting inventory entries: {e}")
            self.supabase_manager.conn.rollback()
        finally:
            self.supabase_manager.disconnect()
    
    def migrate_data_simple(self):
        """Simple migration focusing on basic data insertion."""
        logger.info("🚀 Starting simple Tally to Supabase data migration...")
        
        # Step 1: Extract data from Tally
        data = self.extract_data_from_tally()
        if not data:
            logger.error("❌ No data extracted from Tally")
            return False
        
        # Step 2: Insert data in separate transactions to avoid rollbacks
        self.insert_vouchers_simple(data.get('vouchers', []))
        self.insert_ledger_entries_simple(data.get('ledger_entries', []))
        self.insert_inventory_entries_simple(data.get('inventory_entries', []))
        
        logger.info("✅ Simple data migration completed!")
        return True

def main():
    parser = argparse.ArgumentParser(description='Simple Tally to Supabase Migration')
    parser.add_argument('--action', choices=['migrate', 'extract-only'], 
                       default='migrate', help='Action to perform')
    
    args = parser.parse_args()
    
    migration = SimpleTallyMigration()
    
    if args.action == 'extract-only':
        logger.info("🔄 Extracting data from Tally only...")
        data = migration.extract_data_from_tally()
        logger.info(f"📊 Extracted {len(data)} data types")
        for data_type, records in data.items():
            logger.info(f"  - {data_type}: {len(records)} records")
    else:
        migration.migrate_data_simple()

if __name__ == "__main__":
    main()
