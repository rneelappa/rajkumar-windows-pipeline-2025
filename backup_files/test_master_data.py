#!/usr/bin/env python3
"""
Test Master Data Insertion
"""

import logging
from psycopg2.extras import RealDictCursor
from supabase_manager import SupabaseManager
from config_manager import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_master_data():
    """Test master data insertion."""
    manager = SupabaseManager()
    
    if not manager.connect():
        logger.error("❌ Failed to connect to Supabase")
        return False
    
    try:
        cursor = manager.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SET search_path TO tally, public')
        
        company_id = config.get_company_id()
        division_id = config.get_division_id()
        
        logger.info(f"🔄 Testing master data insertion...")
        
        # Insert voucher types
        voucher_types = [
            ('Sales', 'Sales Voucher', None, True),
            ('Purchase', 'Purchase Voucher', None, True),
            ('Receipt', 'Receipt Voucher', None, True),
            ('Payment', 'Payment Voucher', None, True),
            ('Journal', 'Journal Voucher', None, True),
            ('Contra', 'Contra Voucher', None, True)
        ]
        
        master_mappings = {}
        
        for name, description, parent, affects_stock in voucher_types:
            cursor.execute("""
                INSERT INTO voucher_types (guid, name, parent_id, affects_stock, company_id, division_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (guid) DO UPDATE SET
                    name = EXCLUDED.name,
                    parent_id = EXCLUDED.parent_id,
                    affects_stock = EXCLUDED.affects_stock
                RETURNING id
            """, (f'vt-{name.lower()}', name, parent, affects_stock, company_id, division_id))
            
            result = cursor.fetchone()
            if result:
                master_mappings[f'voucher_type_{name}'] = result['id']
                logger.info(f"✅ Inserted voucher type '{name}' with ID: {result['id']}")
        
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
            """, (f'grp-{name.lower().replace(" ", "-")}', name, parent, company_id, division_id))
            
            result = cursor.fetchone()
            if result:
                master_mappings[f'group_{name}'] = result['id']
                logger.info(f"✅ Inserted group '{name}' with ID: {result['id']}")
        
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
                INSERT INTO ledgers (guid, name, parent_id, company_id, division_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (guid) DO UPDATE SET
                    name = EXCLUDED.name,
                    parent_id = EXCLUDED.parent_id
                RETURNING id
            """, (f'ldg-{name.lower()}', name, parent_id, company_id, division_id))
            
            result = cursor.fetchone()
            if result:
                master_mappings[f'ledger_{name}'] = result['id']
                logger.info(f"✅ Inserted ledger '{name}' with ID: {result['id']}")
        
        manager.conn.commit()
        logger.info(f"✅ Master data insertion completed! Created {len(master_mappings)} mappings")
        return True
        
    except Exception as e:
        logger.error(f"❌ Master data insertion failed: {e}")
        manager.conn.rollback()
        return False
    finally:
        manager.disconnect()

if __name__ == "__main__":
    test_master_data()
