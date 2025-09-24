#!/usr/bin/env python3
"""
Simple Migration Test - Test basic data insertion
"""

import logging
from psycopg2.extras import RealDictCursor
from supabase_manager import SupabaseManager
from config_manager import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_basic_insertion():
    """Test basic data insertion."""
    manager = SupabaseManager()
    
    if not manager.connect():
        logger.error("❌ Failed to connect to Supabase")
        return False
    
    try:
        cursor = manager.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SET search_path TO tally, public')
        
        company_id = config.get_company_id()
        division_id = config.get_division_id()
        
        logger.info(f"🔄 Testing basic insertion...")
        logger.info(f"Company ID: {company_id}")
        logger.info(f"Division ID: {division_id}")
        
        # Insert a test voucher type
        cursor.execute("""
            INSERT INTO voucher_types (guid, name, affects_stock, company_id, division_id)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (guid) DO UPDATE SET
                name = EXCLUDED.name
            RETURNING id
        """, ('vt-test-sales', 'Test Sales', True, company_id, division_id))
        
        result = cursor.fetchone()
        if result:
            voucher_type_id = result['id']
            logger.info(f"✅ Inserted voucher type with ID: {voucher_type_id}")
        
        # Insert a test voucher
        cursor.execute("""
            INSERT INTO vouchers (guid, date, voucher_number, narration, voucher_type_id, company_id, division_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (guid) DO UPDATE SET
                narration = EXCLUDED.narration
            RETURNING id
        """, ('test-voucher-001', '2025-01-15', 'TEST001', 'Test voucher', voucher_type_id, company_id, division_id))
        
        result = cursor.fetchone()
        if result:
            logger.info(f"✅ Inserted voucher with ID: {result['id']}")
        
        manager.conn.commit()
        logger.info("✅ Basic insertion test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic insertion test failed: {e}")
        manager.conn.rollback()
        return False
    finally:
        manager.disconnect()

if __name__ == "__main__":
    test_basic_insertion()
