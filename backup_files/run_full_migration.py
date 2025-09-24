#!/usr/bin/env python3
"""
Run Full Migration in Small Batches
Automated script to migrate all data in small batches to avoid connection timeouts
"""

import subprocess
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_batch_command(action, offset, limit):
    """Run a batch migration command."""
    cmd = [
        'python3', 'batch_migration.py',
        '--action', action,
        '--offset', str(offset),
        '--limit', str(limit)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 minute timeout
        if result.returncode == 0:
            logger.info(f"✅ {action} batch {offset}-{offset+limit} completed successfully")
            return True
        else:
            logger.error(f"❌ {action} batch {offset}-{offset+limit} failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ {action} batch {offset}-{offset+limit} timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Error running {action} batch {offset}-{offset+limit}: {e}")
        return False

def migrate_table_in_batches(table_name, total_count, batch_size=50):
    """Migrate a table in small batches."""
    logger.info(f"🚀 Starting {table_name} migration ({total_count} records)")
    
    success_count = 0
    error_count = 0
    
    for offset in range(0, total_count, batch_size):
        batch_num = offset // batch_size + 1
        total_batches = (total_count + batch_size - 1) // batch_size
        
        logger.info(f"📦 Processing {table_name} batch {batch_num}/{total_batches} (offset: {offset})")
        
        if run_batch_command(table_name, offset, batch_size):
            success_count += 1
        else:
            error_count += 1
        
        # Small delay between batches to avoid overwhelming the connection
        time.sleep(2)
    
    logger.info(f"✅ {table_name} migration completed: {success_count} batches success, {error_count} batches failed")
    return success_count, error_count

def main():
    """Run the full migration in small batches."""
    logger.info("🚀 Starting full migration in small batches...")
    
    # Define the total counts (we know these from our SQLite database)
    voucher_count = 1733
    ledger_count = 1734
    inventory_count = 1734
    
    batch_size = 50  # Small batch size to avoid timeouts
    
    # Migrate vouchers
    voucher_success, voucher_errors = migrate_table_in_batches('vouchers', voucher_count, batch_size)
    
    # Small delay between tables
    time.sleep(5)
    
    # Migrate ledger entries
    ledger_success, ledger_errors = migrate_table_in_batches('ledgers', ledger_count, batch_size)
    
    # Small delay between tables
    time.sleep(5)
    
    # Migrate inventory entries
    inventory_success, inventory_errors = migrate_table_in_batches('inventory', inventory_count, batch_size)
    
    # Summary
    total_success = voucher_success + ledger_success + inventory_success
    total_errors = voucher_errors + ledger_errors + inventory_errors
    
    logger.info("=" * 60)
    logger.info("📊 MIGRATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Vouchers: {voucher_success} batches success, {voucher_errors} batches failed")
    logger.info(f"Ledger Entries: {ledger_success} batches success, {ledger_errors} batches failed")
    logger.info(f"Inventory Entries: {inventory_success} batches success, {inventory_errors} batches failed")
    logger.info(f"Total: {total_success} batches success, {total_errors} batches failed")
    
    if total_errors == 0:
        logger.info("🎉 All migrations completed successfully!")
    else:
        logger.warning(f"⚠️  {total_errors} batches failed. Check logs for details.")

if __name__ == "__main__":
    main()
