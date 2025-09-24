#!/usr/bin/env python3
"""
SQLite to Supabase Migration
Migrate validated data from SQLite to Supabase
"""

import argparse
import logging
import sqlite3
from psycopg2.extras import RealDictCursor
from supabase_manager import SupabaseManager
from config_manager import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SQLiteToSupabaseMigration:
    def __init__(self):
        self.supabase_manager = SupabaseManager()
        self.company_id = config.get_company_id()
        self.division_id = config.get_division_id()
        self.sqlite_db = 'tally_data.db'
        
    def migrate_vouchers(self):
        """Migrate vouchers from SQLite to Supabase."""
        logger.info("🔄 Migrating vouchers from SQLite to Supabase...")
        
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(self.sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Connect to Supabase
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return False
        
        try:
            supabase_cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            supabase_cursor.execute('SET search_path TO tally, public')
            
            # Get vouchers from SQLite
            sqlite_cursor.execute('''
                SELECT guid, date, voucher_type, voucher_number, reference_number, 
                       reference_date, narration, party_name, place_of_supply,
                       is_invoice, is_accounting_voucher, is_inventory_voucher, is_order_voucher
                FROM vouchers
            ''')
            
            vouchers = sqlite_cursor.fetchall()
            logger.info(f"📊 Found {len(vouchers)} vouchers in SQLite")
            
            success_count = 0
            error_count = 0
            
            for voucher in vouchers:
                try:
                    supabase_cursor.execute('''
                        INSERT INTO vouchers (
                            guid, date, voucher_type, voucher_number, reference_number,
                            reference_date, narration, party_name, place_of_supply,
                            is_invoice, is_accounting_voucher, is_inventory_voucher, is_order_voucher,
                            company_id, division_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (guid) DO UPDATE SET
                            date = EXCLUDED.date,
                            voucher_type = EXCLUDED.voucher_type,
                            voucher_number = EXCLUDED.voucher_number,
                            reference_number = EXCLUDED.reference_number,
                            reference_date = EXCLUDED.reference_date,
                            narration = EXCLUDED.narration,
                            party_name = EXCLUDED.party_name,
                            place_of_supply = EXCLUDED.place_of_supply,
                            is_invoice = EXCLUDED.is_invoice,
                            is_accounting_voucher = EXCLUDED.is_accounting_voucher,
                            is_inventory_voucher = EXCLUDED.is_inventory_voucher,
                            is_order_voucher = EXCLUDED.is_order_voucher
                    ''', (
                        voucher[0],  # guid
                        voucher[1],  # date
                        voucher[2],  # voucher_type
                        voucher[3],  # voucher_number
                        voucher[4],  # reference_number
                        voucher[5],  # reference_date
                        voucher[6],  # narration
                        voucher[7],  # party_name
                        voucher[8],  # place_of_supply
                        voucher[9],  # is_invoice
                        voucher[10], # is_accounting_voucher
                        voucher[11], # is_inventory_voucher
                        voucher[12], # is_order_voucher
                        self.company_id,
                        self.division_id
                    ))
                    success_count += 1
                    
                    if success_count % 100 == 0:
                        logger.info(f"📊 Progress: {success_count}/{len(vouchers)} vouchers migrated")
                        
                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting voucher {voucher[0]}: {e}")
            
            self.supabase_manager.conn.commit()
            logger.info(f"✅ Vouchers migrated: {success_count} success, {error_count} errors")
            
        except Exception as e:
            logger.error(f"❌ Error migrating vouchers: {e}")
            self.supabase_manager.conn.rollback()
        finally:
            sqlite_conn.close()
            self.supabase_manager.disconnect()
        
        return success_count > 0
    
    def migrate_ledger_entries(self):
        """Migrate ledger entries from SQLite to Supabase."""
        logger.info("🔄 Migrating ledger entries from SQLite to Supabase...")
        
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(self.sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Connect to Supabase
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return False
        
        try:
            supabase_cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            supabase_cursor.execute('SET search_path TO tally, public')
            
            # Get ledger entries from SQLite with voucher GUID
            sqlite_cursor.execute('''
                SELECT le.guid, le.ledger_name, le.amount, le.is_debit, v.guid as voucher_guid
                FROM ledger_entries le
                JOIN vouchers v ON le.voucher_id = v.id
            ''')
            
            ledger_entries = sqlite_cursor.fetchall()
            logger.info(f"📊 Found {len(ledger_entries)} ledger entries in SQLite")
            
            success_count = 0
            error_count = 0
            
            for ledger_entry in ledger_entries:
                try:
                    # Get the Supabase voucher ID using the voucher GUID
                    supabase_cursor.execute('SELECT id FROM vouchers WHERE guid = %s', (ledger_entry[4],))
                    voucher_result = supabase_cursor.fetchone()
                    
                    if not voucher_result:
                        logger.warning(f"⚠️  Voucher not found for GUID: {ledger_entry[4]}")
                        error_count += 1
                        continue
                    
                    voucher_id = voucher_result['id']
                    
                    supabase_cursor.execute('''
                        INSERT INTO ledger_entries (
                            guid, voucher_id, ledger_name, amount, is_debit,
                            company_id, division_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (guid) DO UPDATE SET
                            voucher_id = EXCLUDED.voucher_id,
                            ledger_name = EXCLUDED.ledger_name,
                            amount = EXCLUDED.amount,
                            is_debit = EXCLUDED.is_debit
                    ''', (
                        ledger_entry[0],  # guid
                        voucher_id,       # voucher_id from Supabase
                        ledger_entry[1],  # ledger_name
                        ledger_entry[2],  # amount
                        ledger_entry[3],  # is_debit
                        self.company_id,
                        self.division_id
                    ))
                    success_count += 1
                    
                    if success_count % 100 == 0:
                        logger.info(f"📊 Progress: {success_count}/{len(ledger_entries)} ledger entries migrated")
                        
                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting ledger entry {ledger_entry[0]}: {e}")
            
            self.supabase_manager.conn.commit()
            logger.info(f"✅ Ledger entries migrated: {success_count} success, {error_count} errors")
            
        except Exception as e:
            logger.error(f"❌ Error migrating ledger entries: {e}")
            self.supabase_manager.conn.rollback()
        finally:
            sqlite_conn.close()
            self.supabase_manager.disconnect()
        
        return success_count > 0
    
    def migrate_inventory_entries(self):
        """Migrate inventory entries from SQLite to Supabase."""
        logger.info("🔄 Migrating inventory entries from SQLite to Supabase...")
        
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(self.sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Connect to Supabase
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return False
        
        try:
            supabase_cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            supabase_cursor.execute('SET search_path TO tally, public')
            
            # Get inventory entries from SQLite with voucher GUID
            sqlite_cursor.execute('''
                SELECT ie.guid, ie.stock_item_name, ie.quantity, ie.rate, ie.amount, v.guid as voucher_guid
                FROM inventory_entries ie
                JOIN vouchers v ON ie.voucher_id = v.id
            ''')
            
            inventory_entries = sqlite_cursor.fetchall()
            logger.info(f"📊 Found {len(inventory_entries)} inventory entries in SQLite")
            
            success_count = 0
            error_count = 0
            
            for inventory_entry in inventory_entries:
                try:
                    # Get the Supabase voucher ID using the voucher GUID
                    supabase_cursor.execute('SELECT id FROM vouchers WHERE guid = %s', (inventory_entry[5],))
                    voucher_result = supabase_cursor.fetchone()
                    
                    if not voucher_result:
                        logger.warning(f"⚠️  Voucher not found for GUID: {inventory_entry[5]}")
                        error_count += 1
                        continue
                    
                    voucher_id = voucher_result['id']
                    
                    supabase_cursor.execute('''
                        INSERT INTO inventory_entries (
                            guid, voucher_id, stock_item_name, quantity, rate, amount,
                            company_id, division_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (guid) DO UPDATE SET
                            voucher_id = EXCLUDED.voucher_id,
                            stock_item_name = EXCLUDED.stock_item_name,
                            quantity = EXCLUDED.quantity,
                            rate = EXCLUDED.rate,
                            amount = EXCLUDED.amount
                    ''', (
                        inventory_entry[0],  # guid
                        voucher_id,         # voucher_id from Supabase
                        inventory_entry[1], # stock_item_name
                        inventory_entry[2], # quantity
                        inventory_entry[3], # rate
                        inventory_entry[4], # amount
                        self.company_id,
                        self.division_id
                    ))
                    success_count += 1
                    
                    if success_count % 100 == 0:
                        logger.info(f"📊 Progress: {success_count}/{len(inventory_entries)} inventory entries migrated")
                        
                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting inventory entry {inventory_entry[0]}: {e}")
            
            self.supabase_manager.conn.commit()
            logger.info(f"✅ Inventory entries migrated: {success_count} success, {error_count} errors")
            
        except Exception as e:
            logger.error(f"❌ Error migrating inventory entries: {e}")
            self.supabase_manager.conn.rollback()
        finally:
            sqlite_conn.close()
            self.supabase_manager.disconnect()
        
        return success_count > 0
    
    def migrate_all_data(self):
        """Migrate all data from SQLite to Supabase."""
        logger.info("🚀 Starting SQLite to Supabase migration...")
        
        # Migrate vouchers
        if not self.migrate_vouchers():
            logger.error("❌ Voucher migration failed")
            return False
        
        # Migrate ledger entries
        if not self.migrate_ledger_entries():
            logger.error("❌ Ledger entries migration failed")
            return False
        
        # Migrate inventory entries
        if not self.migrate_inventory_entries():
            logger.error("❌ Inventory entries migration failed")
            return False
        
        logger.info("✅ All data migrated successfully from SQLite to Supabase!")
        return True

def main():
    parser = argparse.ArgumentParser(description='SQLite to Supabase Migration')
    parser.add_argument('--action', choices=['migrate', 'vouchers-only', 'ledgers-only', 'inventory-only'], 
                       default='migrate', help='Action to perform')
    
    args = parser.parse_args()
    
    migration = SQLiteToSupabaseMigration()
    
    if args.action == 'vouchers-only':
        migration.migrate_vouchers()
    elif args.action == 'ledgers-only':
        migration.migrate_ledger_entries()
    elif args.action == 'inventory-only':
        migration.migrate_inventory_entries()
    else:
        migration.migrate_all_data()

if __name__ == "__main__":
    main()
