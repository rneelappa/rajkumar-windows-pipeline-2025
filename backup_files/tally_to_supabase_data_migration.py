#!/usr/bin/env python3
"""
Tally to Supabase Data Migration Script
Extracts data from Tally and inserts it directly into Supabase PostgreSQL database.
"""

import argparse
import logging
import xml.etree.ElementTree as ET
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Any, Optional
from psycopg2.extras import RealDictCursor
from psycopg2 import sql

from config_manager import config
from tally_client import TallyClient
from supabase_manager import SupabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class TallyToSupabaseMigration:
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
            # Remove commas and convert to float
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
            # Tally format: DD-Mon-YY (e.g., "1-Sep-25")
            parts = date_str.strip().split('-')
            if len(parts) != 3:
                return None
            
            day = int(parts[0])
            month_str = parts[1]
            year = int(parts[2])
            
            # Convert 2-digit year to 4-digit
            if year < 50:
                year += 2000
            else:
                year += 1900
            
            # Month name to number mapping
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
        """Extract comprehensive data from Tally using the working TDL approach."""
        logger.info("🔄 Extracting data from Tally...")
        
        # Use the comprehensive TDL that we know works
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
                'inventory_entries': [],
                'employee_entries': [],
                'payhead_allocations': [],
                'attendance_entries': []
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
            
            # Parse employee entries
            for elem in root.iter():
                if elem.tag.startswith('TRN_EMPLOYEE_'):
                    employee_data = {}
                    for child in elem.iter():
                        if child.tag.startswith('TRN_EMPLOYEE_'):
                            tag_name = child.tag.replace('TRN_EMPLOYEE_', '').lower()
                            employee_data[tag_name] = child.text
                    
                    if employee_data:
                        data['employee_entries'].append(employee_data)
            
            # Parse payhead allocations
            for elem in root.iter():
                if elem.tag.startswith('TRN_PAYHEAD_'):
                    payhead_data = {}
                    for child in elem.iter():
                        if child.tag.startswith('TRN_PAYHEAD_'):
                            tag_name = child.tag.replace('TRN_PAYHEAD_', '').lower()
                            payhead_data[tag_name] = child.text
                    
                    if payhead_data:
                        data['payhead_allocations'].append(payhead_data)
            
            # Parse attendance entries
            for elem in root.iter():
                if elem.tag.startswith('TRN_ATTENDANCE_'):
                    attendance_data = {}
                    for child in elem.iter():
                        if child.tag.startswith('TRN_ATTENDANCE_'):
                            tag_name = child.tag.replace('TRN_ATTENDANCE_', '').lower()
                            attendance_data[tag_name] = child.text
                    
                    if attendance_data:
                        data['attendance_entries'].append(attendance_data)
            
            logger.info(f"📊 Extracted data: {len(data['vouchers'])} vouchers, {len(data['ledger_entries'])} ledger entries, {len(data['inventory_entries'])} inventory entries")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error extracting data from Tally: {e}")
            return {}
    
    def insert_master_data(self) -> Dict[str, int]:
        """Insert master data records and return mapping of names to IDs."""
        logger.info("🔄 Inserting master data...")
        
        master_mappings = {}
        
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return master_mappings
        
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            
            # Insert voucher types
            voucher_types = [
                ('Sales', 'Sales Voucher', None, True, True),
                ('Purchase', 'Purchase Voucher', None, True, True),
                ('Receipt', 'Receipt Voucher', None, True, True),
                ('Payment', 'Payment Voucher', None, True, True),
                ('Journal', 'Journal Voucher', None, True, True),
                ('Contra', 'Contra Voucher', None, True, True)
            ]
            
            for name, description, parent, affects_gross_profit, affects_stock in voucher_types:
                cursor.execute("""
                    INSERT INTO voucher_types (guid, name, parent_id, affects_stock, company_id, division_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (guid) DO UPDATE SET
                        name = EXCLUDED.name,
                        parent_id = EXCLUDED.parent_id,
                        affects_stock = EXCLUDED.affects_stock
                    RETURNING id
                """, (f'vt-{name.lower()}', name, parent, affects_stock, self.company_id, self.division_id))
                
                result = cursor.fetchone()
                if result:
                    master_mappings[f'voucher_type_{name}'] = result['id']
            
            # Insert groups
            groups = [
                ('Sundry Debtors', 'Sundry Debtors', None),
                ('Sundry Creditors', 'Sundry Creditors', None),
                ('Bank Accounts', 'Bank Accounts', None),
                ('Cash-in-Hand', 'Cash-in-Hand', None),
                ('Sales Accounts', 'Sales Accounts', None),
                ('Purchase Accounts', 'Purchase Accounts', None)
            ]
            
            for name, alias, parent in groups:
                cursor.execute("""
                    INSERT INTO groups (guid, name, parent_id, company_id, division_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (guid) DO UPDATE SET
                        name = EXCLUDED.name,
                        parent_id = EXCLUDED.parent_id
                    RETURNING id
                """, (f'grp-{name.lower().replace(" ", "-")}', name, parent, self.company_id, self.division_id))
                
                result = cursor.fetchone()
                if result:
                    master_mappings[f'group_{name}'] = result['id']
            
            # Insert ledgers
            ledgers = [
                ('Cash', 'Cash Account', 'Cash-in-Hand'),
                ('Bank', 'Bank Account', 'Bank Accounts'),
                ('Sales', 'Sales Account', 'Sales Accounts'),
                ('Purchase', 'Purchase Account', 'Purchase Accounts')
            ]
            
            for name, alias, parent in ledgers:
                parent_id = master_mappings.get(f'group_{parent}')
                cursor.execute("""
                    INSERT INTO ledgers (name, alias, parent_id, company_id, division_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (name, company_id, division_id) DO UPDATE SET
                        alias = EXCLUDED.alias,
                        parent_id = EXCLUDED.parent_id
                    RETURNING id
                """, (name, alias, parent_id, self.company_id, self.division_id))
                
                result = cursor.fetchone()
                if result:
                    master_mappings[f'ledger_{name}'] = result['id']
            
            # Insert stock items
            stock_items = [
                ('Stock Item 1', 'SI1', 'Primary', 'Nos', 1.0),
                ('Stock Item 2', 'SI2', 'Primary', 'Nos', 1.0)
            ]
            
            for name, alias, category, unit, opening_balance in stock_items:
                cursor.execute("""
                    INSERT INTO stock_items (name, alias, category, unit, opening_balance, company_id, division_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name, company_id, division_id) DO UPDATE SET
                        alias = EXCLUDED.alias,
                        category = EXCLUDED.category,
                        unit = EXCLUDED.unit,
                        opening_balance = EXCLUDED.opening_balance
                    RETURNING id
                """, (name, alias, category, unit, opening_balance, self.company_id, self.division_id))
                
                result = cursor.fetchone()
                if result:
                    master_mappings[f'stock_item_{name}'] = result['id']
            
            # Insert godowns
            godowns = [
                ('Main Godown', 'Main', 'Main Location'),
                ('Branch Godown', 'Branch', 'Branch Location')
            ]
            
            for name, alias, address in godowns:
                cursor.execute("""
                    INSERT INTO godowns (name, alias, address, company_id, division_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (name, company_id, division_id) DO UPDATE SET
                        alias = EXCLUDED.alias,
                        address = EXCLUDED.address
                    RETURNING id
                """, (name, alias, address, self.company_id, self.division_id))
                
                result = cursor.fetchone()
                if result:
                    master_mappings[f'godown_{name}'] = result['id']
            
            self.supabase_manager.conn.commit()
            logger.info(f"✅ Inserted master data: {len(master_mappings)} mappings created")
            
        except Exception as e:
            logger.error(f"❌ Error inserting master data: {e}")
            self.supabase_manager.conn.rollback()
        finally:
            self.supabase_manager.disconnect()
        
        return master_mappings
    
    def insert_transaction_data(self, data: Dict[str, List[Dict[str, Any]]], master_mappings: Dict[str, int]):
        """Insert transaction data into Supabase."""
        logger.info("🔄 Inserting transaction data...")
        
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return
        
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            
            # Insert vouchers
            for voucher_data in data.get('vouchers', []):
                try:
                    voucher_type_id = master_mappings.get(f"voucher_type_{voucher_data.get('voucher_type', 'Sales')}")
                    party_ledger_id = master_mappings.get(f"ledger_{voucher_data.get('party_name', 'Cash')}")
                    
                    cursor.execute("""
                        INSERT INTO vouchers (
                            guid, date, voucher_type_id, voucher_number, reference_number, 
                            narration, party_ledger_id, company_id, division_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (guid) DO UPDATE SET
                            date = EXCLUDED.date,
                            voucher_type_id = EXCLUDED.voucher_type_id,
                            voucher_number = EXCLUDED.voucher_number,
                            reference_number = EXCLUDED.reference_number,
                            narration = EXCLUDED.narration,
                            party_ledger_id = EXCLUDED.party_ledger_id
                    """, (
                        voucher_data.get('id'),
                        self.safe_date(voucher_data.get('date')),
                        voucher_type_id,
                        voucher_data.get('voucher_number'),
                        voucher_data.get('reference'),
                        voucher_data.get('narration'),
                        party_ledger_id,
                        self.company_id,
                        self.division_id
                    ))
                except Exception as e:
                    logger.warning(f"⚠️  Error inserting voucher {voucher_data.get('id', 'unknown')}: {e}")
            
            # Insert ledger entries
            for ledger_data in data.get('ledger_entries', []):
                try:
                    ledger_id = master_mappings.get(f"ledger_{ledger_data.get('ledger_name', 'Cash')}")
                    
                    cursor.execute("""
                        INSERT INTO ledger_entries (
                            id, voucher_id, ledger_id, ledger_name, amount, 
                            is_debit, company_id, division_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id, company_id, division_id) DO UPDATE SET
                            voucher_id = EXCLUDED.voucher_id,
                            ledger_id = EXCLUDED.ledger_id,
                            ledger_name = EXCLUDED.ledger_name,
                            amount = EXCLUDED.amount,
                            is_debit = EXCLUDED.is_debit
                    """, (
                        ledger_data.get('id'),
                        ledger_data.get('id'),  # Same as voucher ID in flat structure
                        ledger_id,
                        ledger_data.get('ledger_name'),
                        self.safe_decimal(ledger_data.get('amount')),
                        ledger_data.get('is_debit') == 'Yes',
                        self.company_id,
                        self.division_id
                    ))
                except Exception as e:
                    logger.warning(f"⚠️  Error inserting ledger entry {ledger_data.get('id', 'unknown')}: {e}")
            
            # Insert inventory entries
            for inventory_data in data.get('inventory_entries', []):
                try:
                    stock_item_id = master_mappings.get(f"stock_item_{inventory_data.get('stockitem_name', 'Stock Item 1')}")
                    godown_id = master_mappings.get(f"godown_{inventory_data.get('godown_name', 'Main Godown')}")
                    
                    cursor.execute("""
                        INSERT INTO inventory_entries (
                            id, voucher_id, stock_item_id, stock_item_name, 
                            quantity, rate, amount, godown_id, godown_name, company_id, division_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id, company_id, division_id) DO UPDATE SET
                            voucher_id = EXCLUDED.voucher_id,
                            stock_item_id = EXCLUDED.stock_item_id,
                            stock_item_name = EXCLUDED.stock_item_name,
                            quantity = EXCLUDED.quantity,
                            rate = EXCLUDED.rate,
                            amount = EXCLUDED.amount,
                            godown_id = EXCLUDED.godown_id,
                            godown_name = EXCLUDED.godown_name
                    """, (
                        inventory_data.get('id'),
                        inventory_data.get('id'),  # Same as voucher ID in flat structure
                        stock_item_id,
                        inventory_data.get('stockitem_name'),
                        self.safe_decimal(inventory_data.get('quantity')),
                        self.safe_decimal(inventory_data.get('rate')),
                        self.safe_decimal(inventory_data.get('amount')),
                        godown_id,
                        inventory_data.get('godown_name'),
                        self.company_id,
                        self.division_id
                    ))
                except Exception as e:
                    logger.warning(f"⚠️  Error inserting inventory entry {inventory_data.get('id', 'unknown')}: {e}")
            
            self.supabase_manager.conn.commit()
            logger.info("✅ Transaction data inserted successfully")
            
        except Exception as e:
            logger.error(f"❌ Error inserting transaction data: {e}")
            self.supabase_manager.conn.rollback()
        finally:
            self.supabase_manager.disconnect()
    
    def migrate_data(self):
        """Main migration function."""
        logger.info("🚀 Starting Tally to Supabase data migration...")
        
        # Step 1: Extract data from Tally
        data = self.extract_data_from_tally()
        if not data:
            logger.error("❌ No data extracted from Tally")
            return False
        
        # Step 2: Insert master data
        master_mappings = self.insert_master_data()
        
        # Step 3: Insert transaction data
        self.insert_transaction_data(data, master_mappings)
        
        logger.info("✅ Data migration completed successfully!")
        return True

def main():
    parser = argparse.ArgumentParser(description='Tally to Supabase Data Migration')
    parser.add_argument('--action', choices=['migrate', 'extract-only'], 
                       default='migrate', help='Action to perform')
    
    args = parser.parse_args()
    
    migration = TallyToSupabaseMigration()
    
    if args.action == 'extract-only':
        logger.info("🔄 Extracting data from Tally only...")
        data = migration.extract_data_from_tally()
        logger.info(f"📊 Extracted {len(data)} data types")
        for data_type, records in data.items():
            logger.info(f"  - {data_type}: {len(records)} records")
    else:
        migration.migrate_data()

if __name__ == "__main__":
    main()
