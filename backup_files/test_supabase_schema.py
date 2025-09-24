#!/usr/bin/env python3
"""
Test Supabase Schema and Basic Operations
"""

import logging
from psycopg2.extras import RealDictCursor
from supabase_manager import SupabaseManager
from config_manager import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_schema():
    """Test the Supabase schema and basic operations."""
    manager = SupabaseManager()
    
    if not manager.connect():
        logger.error("❌ Failed to connect to Supabase")
        return False
    
    try:
        cursor = manager.conn.cursor(cursor_factory=RealDictCursor)
        
        # Set search path to tally schema
        cursor.execute('SET search_path TO tally, public')
        
        # List all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'tally' 
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        logger.info(f"📋 Tables in tally schema ({len(tables)} total):")
        for table in tables:
            logger.info(f"  - {table['table_name']}")
        
        # Check vouchers table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'tally' AND table_name = 'vouchers'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        logger.info(f"\n📋 Columns in vouchers table:")
        for col in columns:
            logger.info(f"  - {col['column_name']} ({col['data_type']}) - nullable: {col['is_nullable']}")
        
        # Test basic insert
        company_id = config.get_company_id()
        division_id = config.get_division_id()
        
        logger.info(f"\n🔄 Testing basic insert...")
        logger.info(f"Company ID: {company_id}")
        logger.info(f"Division ID: {division_id}")
        
        # Insert a test voucher type
        cursor.execute("""
            INSERT INTO voucher_types (name, description, affects_gross_profit, affects_stock, sort_position, company_id, division_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name, company_id, division_id) DO UPDATE SET
                description = EXCLUDED.description
            RETURNING id
        """, ('Test Sales', 'Test Sales Voucher', True, True, 1, company_id, division_id))
        
        result = cursor.fetchone()
        if result:
            logger.info(f"✅ Inserted voucher type with ID: {result['id']}")
        
        # Insert a test voucher
        cursor.execute("""
            INSERT INTO vouchers (id, date, voucher_number, narration, amount, company_id, division_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id, company_id, division_id) DO UPDATE SET
                narration = EXCLUDED.narration
            RETURNING id
        """, ('test-voucher-001', '2025-01-15', 'TEST001', 'Test voucher', 100.00, company_id, division_id))
        
        result = cursor.fetchone()
        if result:
            logger.info(f"✅ Inserted voucher with ID: {result['id']}")
        
        manager.conn.commit()
        logger.info("✅ Schema test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema test failed: {e}")
        manager.conn.rollback()
        return False
    finally:
        manager.disconnect()

if __name__ == "__main__":
    test_schema()
