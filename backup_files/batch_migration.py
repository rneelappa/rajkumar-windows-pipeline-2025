#!/usr/bin/env python3
"""
Batch Migration Script - Process data in small batches to avoid timeouts
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

class BatchMigration:
    def __init__(self):
        self.supabase_manager = SupabaseManager()
        self.company_id = config.get_company_id()
        self.division_id = config.get_division_id()
        self.sqlite_db = 'tally_data.db'
        self.batch_size = 50  # Process 50 records at a time
        
    def migrate_vouchers_batch(self, offset=0, limit=None):
        """Migrate vouchers in batches."""
        logger.info(f"🔄 Migrating vouchers batch (offset: {offset}, limit: {limit or 'all'})...")
        
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
            
            # Get vouchers from SQLite with limit
            if limit:
                sqlite_cursor.execute('''
                    SELECT guid, date, voucher_type, voucher_number, reference_number, 
                           reference_date, narration, party_name, place_of_supply,
                           is_invoice, is_accounting_voucher, is_inventory_voucher, is_order_voucher
                    FROM vouchers
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
            else:
                sqlite_cursor.execute('''
                    SELECT guid, date, voucher_type, voucher_number, reference_number, 
                           reference_date, narration, party_name, place_of_supply,
                           is_invoice, is_accounting_voucher, is_inventory_voucher, is_order_voucher
                    FROM vouchers
                    LIMIT ? OFFSET ?
                ''', (self.batch_size, offset))
            
            vouchers = sqlite_cursor.fetchall()
            logger.info(f"📊 Processing {len(vouchers)} vouchers")
            
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
                        voucher[0], voucher[1], voucher[2], voucher[3], voucher[4],
                        voucher[5], voucher[6], voucher[7], voucher[8], voucher[9],
                        voucher[10], voucher[11], voucher[12], self.company_id, self.division_id
                    ))
                    success_count += 1
                        
                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting voucher {voucher[0]}: {e}")
            
            self.supabase_manager.conn.commit()
            logger.info(f"✅ Vouchers batch completed: {success_count} success, {error_count} errors")
            
        except Exception as e:
            logger.error(f"❌ Error in voucher batch: {e}")
            self.supabase_manager.conn.rollback()
        finally:
            sqlite_conn.close()
            self.supabase_manager.disconnect()
        
        return success_count > 0
    
    def migrate_ledger_entries_batch(self, offset=0, limit=None):
        """Migrate ledger entries in batches."""
        logger.info(f"🔄 Migrating ledger entries batch (offset: {offset}, limit: {limit or 'all'})...")
        
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
            if limit:
                sqlite_cursor.execute('''
                    SELECT le.guid, le.ledger_name, le.amount, le.is_debit, v.guid as voucher_guid
                    FROM ledger_entries le
                    JOIN vouchers v ON le.voucher_id = v.id
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
            else:
                sqlite_cursor.execute('''
                    SELECT le.guid, le.ledger_name, le.amount, le.is_debit, v.guid as voucher_guid
                    FROM ledger_entries le
                    JOIN vouchers v ON le.voucher_id = v.id
                    LIMIT ? OFFSET ?
                ''', (self.batch_size, offset))
            
            ledger_entries = sqlite_cursor.fetchall()
            logger.info(f"📊 Processing {len(ledger_entries)} ledger entries")
            
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
                        ledger_entry[0], voucher_id, ledger_entry[1], ledger_entry[2], 
                        ledger_entry[3], self.company_id, self.division_id
                    ))
                    success_count += 1
                        
                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting ledger entry {ledger_entry[0]}: {e}")
            
            self.supabase_manager.conn.commit()
            logger.info(f"✅ Ledger entries batch completed: {success_count} success, {error_count} errors")
            
        except Exception as e:
            logger.error(f"❌ Error in ledger entries batch: {e}")
            self.supabase_manager.conn.rollback()
        finally:
            sqlite_conn.close()
            self.supabase_manager.disconnect()
        
        return success_count > 0
    
    def migrate_inventory_entries_batch(self, offset=0, limit=None):
        """Migrate inventory entries in batches."""
        logger.info(f"🔄 Migrating inventory entries batch (offset: {offset}, limit: {limit or 'all'})...")
        
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
            if limit:
                sqlite_cursor.execute('''
                    SELECT ie.guid, ie.stock_item_name, ie.quantity, ie.rate, ie.amount, v.guid as voucher_guid
                    FROM inventory_entries ie
                    JOIN vouchers v ON ie.voucher_id = v.id
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
            else:
                sqlite_cursor.execute('''
                    SELECT ie.guid, ie.stock_item_name, ie.quantity, ie.rate, ie.amount, v.guid as voucher_guid
                    FROM inventory_entries ie
                    JOIN vouchers v ON ie.voucher_id = v.id
                    LIMIT ? OFFSET ?
                ''', (self.batch_size, offset))
            
            inventory_entries = sqlite_cursor.fetchall()
            logger.info(f"📊 Processing {len(inventory_entries)} inventory entries")
            
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
                        inventory_entry[0], voucher_id, inventory_entry[1], inventory_entry[2],
                        inventory_entry[3], inventory_entry[4], self.company_id, self.division_id
                    ))
                    success_count += 1
                        
                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting inventory entry {inventory_entry[0]}: {e}")
            
            self.supabase_manager.conn.commit()
            logger.info(f"✅ Inventory entries batch completed: {success_count} success, {error_count} errors")
            
        except Exception as e:
            logger.error(f"❌ Error in inventory entries batch: {e}")
            self.supabase_manager.conn.rollback()
        finally:
            sqlite_conn.close()
            self.supabase_manager.disconnect()
        
        return success_count > 0
    
    def get_total_counts(self):
        """Get total counts from SQLite."""
        sqlite_conn = sqlite3.connect(self.sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        
        sqlite_cursor.execute('SELECT COUNT(*) FROM vouchers')
        voucher_count = sqlite_cursor.fetchone()[0]
        
        sqlite_cursor.execute('SELECT COUNT(*) FROM ledger_entries')
        ledger_count = sqlite_cursor.fetchone()[0]
        
        sqlite_cursor.execute('SELECT COUNT(*) FROM inventory_entries')
        inventory_count = sqlite_cursor.fetchone()[0]
        
        sqlite_conn.close()
        
        return voucher_count, ledger_count, inventory_count

def main():
    parser = argparse.ArgumentParser(description='Batch Migration Script')
    parser.add_argument('--action', choices=['vouchers', 'ledgers', 'inventory', 'all'], 
                       default='all', help='Action to perform')
    parser.add_argument('--offset', type=int, default=0, help='Starting offset')
    parser.add_argument('--limit', type=int, help='Number of records to process')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size')
    
    args = parser.parse_args()
    
    migration = BatchMigration()
    migration.batch_size = args.batch_size
    
    if args.action == 'vouchers':
        migration.migrate_vouchers_batch(args.offset, args.limit)
    elif args.action == 'ledgers':
        migration.migrate_ledger_entries_batch(args.offset, args.limit)
    elif args.action == 'inventory':
        migration.migrate_inventory_entries_batch(args.offset, args.limit)
    elif args.action == 'all':
        # Get total counts
        voucher_count, ledger_count, inventory_count = migration.get_total_counts()
        logger.info(f"📊 Total records: {voucher_count} vouchers, {ledger_count} ledger entries, {inventory_count} inventory entries")
        
        # Process vouchers in batches
        logger.info("🚀 Starting voucher migration...")
        for offset in range(0, voucher_count, migration.batch_size):
            logger.info(f"📦 Processing voucher batch {offset//migration.batch_size + 1}")
            migration.migrate_vouchers_batch(offset)
        
        # Process ledger entries in batches
        logger.info("🚀 Starting ledger entries migration...")
        for offset in range(0, ledger_count, migration.batch_size):
            logger.info(f"📦 Processing ledger batch {offset//migration.batch_size + 1}")
            migration.migrate_ledger_entries_batch(offset)
        
        # Process inventory entries in batches
        logger.info("🚀 Starting inventory entries migration...")
        for offset in range(0, inventory_count, migration.batch_size):
            logger.info(f"📦 Processing inventory batch {offset//migration.batch_size + 1}")
            migration.migrate_inventory_entries_batch(offset)
        
        logger.info("✅ All batch migrations completed!")

if __name__ == "__main__":
    main()
