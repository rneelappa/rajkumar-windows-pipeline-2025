#!/usr/bin/env python3
"""
SQLite Test Migration - Use SQLite to test data extraction and insertion
"""

import argparse
import logging
import sqlite3
import xml.etree.ElementTree as ET
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Any, Optional

from config_manager import config
from tally_client import TallyClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SQLiteTestMigration:
    def __init__(self):
        self.tally_client = TallyClient()
        self.company_id = config.get_company_id()
        self.division_id = config.get_division_id()
        self.db_path = 'tally_test.db'
        
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
    
    def create_sqlite_schema(self):
        """Create simple SQLite schema for testing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create vouchers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vouchers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guid TEXT UNIQUE NOT NULL,
                date TEXT,
                voucher_number TEXT,
                narration TEXT,
                amount REAL,
                company_id TEXT,
                division_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create ledger_entries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ledger_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guid TEXT UNIQUE NOT NULL,
                voucher_id INTEGER,
                ledger_name TEXT,
                amount REAL,
                is_debit BOOLEAN,
                company_id TEXT,
                division_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (voucher_id) REFERENCES vouchers(id)
            )
        ''')
        
        # Create inventory_entries table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guid TEXT UNIQUE NOT NULL,
                voucher_id INTEGER,
                stock_item_name TEXT,
                quantity REAL,
                rate REAL,
                amount REAL,
                company_id TEXT,
                division_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (voucher_id) REFERENCES vouchers(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ SQLite schema created successfully")
    
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
            
            # Save XML to file for debugging
            with open('tally_response.xml', 'w', encoding='utf-8') as f:
                f.write(response)
            logger.info("💾 Saved XML response to tally_response.xml")
            
            # Parse the XML response
            root = ET.fromstring(response)
            
            # Extract data by parsing XML tags
            data = {
                'vouchers': [],
                'ledger_entries': [],
                'inventory_entries': []
            }
            
            # Parse voucher data - look for all elements that start with VOUCHER_
            voucher_data = {}
            for elem in root.iter():
                if elem.tag.startswith('VOUCHER_'):
                    tag_name = elem.tag.replace('VOUCHER_', '').lower()
                    voucher_data[tag_name] = elem.text
            
            if voucher_data:
                data['vouchers'].append(voucher_data)
                logger.info(f"📊 Found voucher data: {len(voucher_data)} fields")
                # Show first few fields
                for i, (key, value) in enumerate(list(voucher_data.items())[:5]):
                    logger.info(f"  {key}: {value}")
            
            # Parse ledger entries - look for all elements that start with TRN_LEDGERENTRIES_
            ledger_data = {}
            for elem in root.iter():
                if elem.tag.startswith('TRN_LEDGERENTRIES_'):
                    tag_name = elem.tag.replace('TRN_LEDGERENTRIES_', '').lower()
                    ledger_data[tag_name] = elem.text
            
            if ledger_data:
                data['ledger_entries'].append(ledger_data)
                logger.info(f"📊 Found ledger data: {len(ledger_data)} fields")
                # Show first few fields
                for i, (key, value) in enumerate(list(ledger_data.items())[:5]):
                    logger.info(f"  {key}: {value}")
            
            # Parse inventory entries - look for all elements that start with TRN_INVENTORYENTRIES_
            inventory_data = {}
            for elem in root.iter():
                if elem.tag.startswith('TRN_INVENTORYENTRIES_'):
                    tag_name = elem.tag.replace('TRN_INVENTORYENTRIES_', '').lower()
                    inventory_data[tag_name] = elem.text
            
            if inventory_data:
                data['inventory_entries'].append(inventory_data)
                logger.info(f"📊 Found inventory data: {len(inventory_data)} fields")
                # Show first few fields
                for i, (key, value) in enumerate(list(inventory_data.items())[:5]):
                    logger.info(f"  {key}: {value}")
            
            logger.info(f"📊 Extracted data: {len(data['vouchers'])} vouchers, {len(data['ledger_entries'])} ledger entries, {len(data['inventory_entries'])} inventory entries")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error extracting data from Tally: {e}")
            return {}
    
    def insert_data_to_sqlite(self, data: Dict[str, List[Dict[str, Any]]]):
        """Insert extracted data into SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Insert vouchers
            for voucher_data in data.get('vouchers', []):
                cursor.execute('''
                    INSERT OR REPLACE INTO vouchers (
                        guid, date, voucher_number, narration, amount, company_id, division_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    voucher_data.get('id'),
                    self.safe_date(voucher_data.get('date')),
                    voucher_data.get('voucher_number'),
                    voucher_data.get('narration'),
                    self.safe_decimal(voucher_data.get('amount')),
                    self.company_id,
                    self.division_id
                ))
                logger.info(f"✅ Inserted voucher: {voucher_data.get('id')}")
            
            # Insert ledger entries
            for ledger_data in data.get('ledger_entries', []):
                cursor.execute('''
                    INSERT OR REPLACE INTO ledger_entries (
                        guid, voucher_id, ledger_name, amount, is_debit, company_id, division_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ledger_data.get('id'),
                    ledger_data.get('id'),  # Same as voucher ID in flat structure
                    ledger_data.get('ledger_name'),
                    self.safe_decimal(ledger_data.get('amount')),
                    ledger_data.get('is_debit') == 'Yes',
                    self.company_id,
                    self.division_id
                ))
                logger.info(f"✅ Inserted ledger entry: {ledger_data.get('id')}")
            
            # Insert inventory entries
            for inventory_data in data.get('inventory_entries', []):
                cursor.execute('''
                    INSERT OR REPLACE INTO inventory_entries (
                        guid, voucher_id, stock_item_name, quantity, rate, amount, company_id, division_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    inventory_data.get('id'),
                    inventory_data.get('id'),  # Same as voucher ID in flat structure
                    inventory_data.get('stockitem_name'),
                    self.safe_decimal(inventory_data.get('quantity')),
                    self.safe_decimal(inventory_data.get('rate')),
                    self.safe_decimal(inventory_data.get('amount')),
                    self.company_id,
                    self.division_id
                ))
                logger.info(f"✅ Inserted inventory entry: {inventory_data.get('id')}")
            
            conn.commit()
            logger.info("✅ Data inserted into SQLite successfully")
            
        except Exception as e:
            logger.error(f"❌ Error inserting data into SQLite: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def query_sqlite_data(self):
        """Query and display the inserted data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Query vouchers
            cursor.execute('SELECT COUNT(*) FROM vouchers')
            voucher_count = cursor.fetchone()[0]
            logger.info(f"📊 Total vouchers in SQLite: {voucher_count}")
            
            if voucher_count > 0:
                cursor.execute('SELECT guid, date, voucher_number, narration, amount FROM vouchers LIMIT 3')
                vouchers = cursor.fetchall()
                logger.info("📋 Sample vouchers:")
                for voucher in vouchers:
                    logger.info(f"  GUID: {voucher[0]}, Date: {voucher[1]}, Number: {voucher[2]}, Narration: {voucher[3]}, Amount: {voucher[4]}")
            
            # Query ledger entries
            cursor.execute('SELECT COUNT(*) FROM ledger_entries')
            ledger_count = cursor.fetchone()[0]
            logger.info(f"📊 Total ledger entries in SQLite: {ledger_count}")
            
            if ledger_count > 0:
                cursor.execute('SELECT guid, voucher_id, ledger_name, amount FROM ledger_entries LIMIT 3')
                ledgers = cursor.fetchall()
                logger.info("📋 Sample ledger entries:")
                for ledger in ledgers:
                    logger.info(f"  GUID: {ledger[0]}, Voucher ID: {ledger[1]}, Ledger: {ledger[2]}, Amount: {ledger[3]}")
            
            # Query inventory entries
            cursor.execute('SELECT COUNT(*) FROM inventory_entries')
            inventory_count = cursor.fetchone()[0]
            logger.info(f"📊 Total inventory entries in SQLite: {inventory_count}")
            
            if inventory_count > 0:
                cursor.execute('SELECT guid, voucher_id, stock_item_name, quantity, rate, amount FROM inventory_entries LIMIT 3')
                inventories = cursor.fetchall()
                logger.info("📋 Sample inventory entries:")
                for inventory in inventories:
                    logger.info(f"  GUID: {inventory[0]}, Voucher ID: {inventory[1]}, Item: {inventory[2]}, Qty: {inventory[3]}, Rate: {inventory[4]}, Amount: {inventory[5]}")
            
        except Exception as e:
            logger.error(f"❌ Error querying SQLite data: {e}")
        finally:
            conn.close()
    
    def migrate_data(self):
        """Main migration function."""
        logger.info("🚀 Starting SQLite test migration...")
        
        # Step 1: Create SQLite schema
        self.create_sqlite_schema()
        
        # Step 2: Extract data from Tally
        data = self.extract_data_from_tally()
        if not data:
            logger.error("❌ No data extracted from Tally")
            return False
        
        # Step 3: Insert data into SQLite
        self.insert_data_to_sqlite(data)
        
        # Step 4: Query and display the data
        self.query_sqlite_data()
        
        logger.info("✅ SQLite test migration completed!")
        return True

def main():
    parser = argparse.ArgumentParser(description='SQLite Test Migration')
    parser.add_argument('--action', choices=['migrate', 'extract-only', 'query'], 
                       default='migrate', help='Action to perform')
    
    args = parser.parse_args()
    
    migration = SQLiteTestMigration()
    
    if args.action == 'extract-only':
        logger.info("🔄 Extracting data from Tally only...")
        data = migration.extract_data_from_tally()
        logger.info(f"📊 Extracted {len(data)} data types")
        for data_type, records in data.items():
            logger.info(f"  - {data_type}: {len(records)} records")
    elif args.action == 'query':
        logger.info("🔄 Querying SQLite data...")
        migration.query_sqlite_data()
    else:
        migration.migrate_data()

if __name__ == "__main__":
    main()
