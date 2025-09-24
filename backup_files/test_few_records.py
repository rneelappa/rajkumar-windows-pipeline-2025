#!/usr/bin/env python3
"""
Test Few Records - Insert just a few sample records to understand the process
"""

import logging
from psycopg2.extras import RealDictCursor
from supabase_manager import SupabaseManager
from config_manager import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_few_records():
    """Test inserting just a few sample records."""
    manager = SupabaseManager()
    
    if not manager.connect():
        logger.error("❌ Failed to connect to Supabase")
        return False
    
    try:
        cursor = manager.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SET search_path TO tally, public')
        
        company_id = config.get_company_id()
        division_id = config.get_division_id()
        
        logger.info(f"🔄 Testing with few sample records...")
        logger.info(f"Company ID: {company_id}")
        logger.info(f"Division ID: {division_id}")
        
        # Test 1: Insert a simple voucher
        logger.info("📝 Test 1: Inserting a simple voucher...")
        cursor.execute("""
            INSERT INTO vouchers (
                guid, date, voucher_number, narration, company_id, division_id
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (guid) DO UPDATE SET
                narration = EXCLUDED.narration
            RETURNING id, guid, date, voucher_number, narration
        """, (
            'test-voucher-sample-001',
            '2025-01-15',
            'SAMPLE001',
            'Sample voucher for testing',
            company_id,
            division_id
        ))
        
        result = cursor.fetchone()
        if result:
            logger.info(f"✅ Inserted voucher: ID={result['id']}, GUID={result['guid']}, Date={result['date']}, Number={result['voucher_number']}")
            voucher_id = result['id']
        else:
            logger.error("❌ Failed to insert voucher")
            return False
        
        # Test 2: Insert a ledger entry
        logger.info("📝 Test 2: Inserting a ledger entry...")
        cursor.execute("""
            INSERT INTO ledger_entries (
                guid, voucher_id, ledger_name, amount, company_id, division_id
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (guid) DO UPDATE SET
                amount = EXCLUDED.amount
            RETURNING id, guid, voucher_id, ledger_name, amount
        """, (
            'test-ledger-sample-001',
            voucher_id,
            'Cash Account',
            1000.00,
            company_id,
            division_id
        ))
        
        result = cursor.fetchone()
        if result:
            logger.info(f"✅ Inserted ledger entry: ID={result['id']}, GUID={result['guid']}, Voucher ID={result['voucher_id']}, Ledger={result['ledger_name']}, Amount={result['amount']}")
        else:
            logger.error("❌ Failed to insert ledger entry")
            return False
        
        # Test 3: Insert an inventory entry
        logger.info("📝 Test 3: Inserting an inventory entry...")
        cursor.execute("""
            INSERT INTO inventory_entries (
                guid, voucher_id, stock_item_name, quantity, rate, amount, company_id, division_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (guid) DO UPDATE SET
                amount = EXCLUDED.amount
            RETURNING id, guid, voucher_id, stock_item_name, quantity, rate, amount
        """, (
            'test-inventory-sample-001',
            voucher_id,
            'Sample Stock Item',
            10.0,
            100.0,
            1000.0,
            company_id,
            division_id
        ))
        
        result = cursor.fetchone()
        if result:
            logger.info(f"✅ Inserted inventory entry: ID={result['id']}, GUID={result['guid']}, Voucher ID={result['voucher_id']}, Item={result['stock_item_name']}, Qty={result['quantity']}, Rate={result['rate']}, Amount={result['amount']}")
        else:
            logger.error("❌ Failed to insert inventory entry")
            return False
        
        # Test 4: Query the data back to verify
        logger.info("📝 Test 4: Querying inserted data...")
        cursor.execute("""
            SELECT v.id, v.guid, v.date, v.voucher_number, v.narration,
                   COUNT(le.id) as ledger_count,
                   COUNT(ie.id) as inventory_count
            FROM vouchers v
            LEFT JOIN ledger_entries le ON v.id = le.voucher_id
            LEFT JOIN inventory_entries ie ON v.id = ie.voucher_id
            WHERE v.guid = %s
            GROUP BY v.id, v.guid, v.date, v.voucher_number, v.narration
        """, ('test-voucher-sample-001',))
        
        result = cursor.fetchone()
        if result:
            logger.info(f"✅ Verified voucher: ID={result['id']}, GUID={result['guid']}, Date={result['date']}, Number={result['voucher_number']}")
            logger.info(f"   Ledger entries: {result['ledger_count']}, Inventory entries: {result['inventory_count']}")
        else:
            logger.error("❌ Failed to verify inserted data")
            return False
        
        manager.conn.commit()
        logger.info("✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        manager.conn.rollback()
        return False
    finally:
        manager.disconnect()

if __name__ == "__main__":
    test_few_records()
