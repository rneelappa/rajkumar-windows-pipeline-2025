#!/usr/bin/env python3
"""
Data Quality Analysis for Supabase Tables
Analyze data quality, relationships, and integrity of migrated data
"""

import logging
from psycopg2.extras import RealDictCursor
from supabase_manager import SupabaseManager
from config_manager import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class DataQualityAnalysis:
    def __init__(self):
        self.supabase_manager = SupabaseManager()
        self.company_id = config.get_company_id()
        self.division_id = config.get_division_id()
        
    def analyze_table_counts(self):
        """Analyze record counts in all tables."""
        logger.info("📊 Analyzing table counts...")
        
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return
        
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            tables = ['vouchers', 'ledger_entries', 'inventory_entries']
            
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
                result = cursor.fetchone()
                count = result['count'] if result else 0
                logger.info(f"  📋 {table}: {count:,} records")
            
        except Exception as e:
            logger.error(f"❌ Error analyzing table counts: {e}")
        finally:
            self.supabase_manager.disconnect()
    
    def analyze_data_quality(self):
        """Analyze data quality issues."""
        logger.info("🔍 Analyzing data quality...")
        
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return
        
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            # Analyze vouchers
            logger.info("📋 VOUCHERS ANALYSIS:")
            
            # Check for NULL values in critical fields
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(guid) as guid_count,
                    COUNT(date) as date_count,
                    COUNT(voucher_type) as voucher_type_count,
                    COUNT(voucher_number) as voucher_number_count,
                    COUNT(narration) as narration_count
                FROM vouchers
            ''')
            result = cursor.fetchone()
            logger.info(f"  Total vouchers: {result['total']:,}")
            logger.info(f"  GUIDs: {result['guid_count']:,} ({result['guid_count']/result['total']*100:.1f}%)")
            logger.info(f"  Dates: {result['date_count']:,} ({result['date_count']/result['total']*100:.1f}%)")
            logger.info(f"  Voucher Types: {result['voucher_type_count']:,} ({result['voucher_type_count']/result['total']*100:.1f}%)")
            logger.info(f"  Voucher Numbers: {result['voucher_number_count']:,} ({result['voucher_number_count']/result['total']*100:.1f}%)")
            logger.info(f"  Narrations: {result['narration_count']:,} ({result['narration_count']/result['total']*100:.1f}%)")
            
            # Check for duplicate GUIDs
            cursor.execute('''
                SELECT guid, COUNT(*) as count 
                FROM vouchers 
                GROUP BY guid 
                HAVING COUNT(*) > 1
            ''')
            duplicates = cursor.fetchall()
            if duplicates:
                logger.warning(f"  ⚠️  Found {len(duplicates)} duplicate GUIDs")
                for dup in duplicates[:5]:  # Show first 5
                    logger.warning(f"    GUID {dup['guid']}: {dup['count']} occurrences")
            else:
                logger.info("  ✅ No duplicate GUIDs found")
            
            # Analyze ledger entries
            logger.info("\n📋 LEDGER ENTRIES ANALYSIS:")
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(guid) as guid_count,
                    COUNT(voucher_id) as voucher_id_count,
                    COUNT(ledger_name) as ledger_name_count,
                    COUNT(amount) as amount_count
                FROM ledger_entries
            ''')
            result = cursor.fetchone()
            logger.info(f"  Total ledger entries: {result['total']:,}")
            logger.info(f"  GUIDs: {result['guid_count']:,} ({result['guid_count']/result['total']*100:.1f}%)")
            logger.info(f"  Voucher IDs: {result['voucher_id_count']:,} ({result['voucher_id_count']/result['total']*100:.1f}%)")
            logger.info(f"  Ledger Names: {result['ledger_name_count']:,} ({result['ledger_name_count']/result['total']*100:.1f}%)")
            logger.info(f"  Amounts: {result['amount_count']:,} ({result['amount_count']/result['total']*100:.1f}%)")
            
            # Analyze inventory entries
            logger.info("\n📋 INVENTORY ENTRIES ANALYSIS:")
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(guid) as guid_count,
                    COUNT(voucher_id) as voucher_id_count,
                    COUNT(stock_item_name) as stock_item_name_count,
                    COUNT(quantity) as quantity_count,
                    COUNT(rate) as rate_count,
                    COUNT(amount) as amount_count
                FROM inventory_entries
            ''')
            result = cursor.fetchone()
            logger.info(f"  Total inventory entries: {result['total']:,}")
            logger.info(f"  GUIDs: {result['guid_count']:,} ({result['guid_count']/result['total']*100:.1f}%)")
            logger.info(f"  Voucher IDs: {result['voucher_id_count']:,} ({result['voucher_id_count']/result['total']*100:.1f}%)")
            logger.info(f"  Stock Item Names: {result['stock_item_name_count']:,} ({result['stock_item_name_count']/result['total']*100:.1f}%)")
            logger.info(f"  Quantities: {result['quantity_count']:,} ({result['quantity_count']/result['total']*100:.1f}%)")
            logger.info(f"  Rates: {result['rate_count']:,} ({result['rate_count']/result['total']*100:.1f}%)")
            logger.info(f"  Amounts: {result['amount_count']:,} ({result['amount_count']/result['total']*100:.1f}%)")
            
        except Exception as e:
            logger.error(f"❌ Error analyzing data quality: {e}")
        finally:
            self.supabase_manager.disconnect()
    
    def analyze_relationships(self):
        """Analyze foreign key relationships."""
        logger.info("🔗 Analyzing relationships...")
        
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return
        
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            # Check voucher_id relationships in ledger_entries
            logger.info("📋 LEDGER ENTRIES RELATIONSHIPS:")
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_ledger_entries,
                    COUNT(voucher_id) as entries_with_voucher_id,
                    COUNT(CASE WHEN v.id IS NOT NULL THEN 1 END) as valid_voucher_relationships
                FROM ledger_entries le
                LEFT JOIN vouchers v ON le.voucher_id = v.id
            ''')
            result = cursor.fetchone()
            logger.info(f"  Total ledger entries: {result['total_ledger_entries']:,}")
            logger.info(f"  Entries with voucher_id: {result['entries_with_voucher_id']:,}")
            logger.info(f"  Valid voucher relationships: {result['valid_voucher_relationships']:,}")
            
            if result['entries_with_voucher_id'] > 0:
                relationship_percentage = (result['valid_voucher_relationships'] / result['entries_with_voucher_id']) * 100
                logger.info(f"  Relationship integrity: {relationship_percentage:.1f}%")
            
            # Check voucher_id relationships in inventory_entries
            logger.info("\n📋 INVENTORY ENTRIES RELATIONSHIPS:")
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_inventory_entries,
                    COUNT(voucher_id) as entries_with_voucher_id,
                    COUNT(CASE WHEN v.id IS NOT NULL THEN 1 END) as valid_voucher_relationships
                FROM inventory_entries ie
                LEFT JOIN vouchers v ON ie.voucher_id = v.id
            ''')
            result = cursor.fetchone()
            logger.info(f"  Total inventory entries: {result['total_inventory_entries']:,}")
            logger.info(f"  Entries with voucher_id: {result['entries_with_voucher_id']:,}")
            logger.info(f"  Valid voucher relationships: {result['valid_voucher_relationships']:,}")
            
            if result['entries_with_voucher_id'] > 0:
                relationship_percentage = (result['valid_voucher_relationships'] / result['entries_with_voucher_id']) * 100
                logger.info(f"  Relationship integrity: {relationship_percentage:.1f}%")
            
            # Check for orphaned records
            logger.info("\n📋 ORPHANED RECORDS ANALYSIS:")
            
            cursor.execute('''
                SELECT COUNT(*) as orphaned_ledger_entries
                FROM ledger_entries le
                LEFT JOIN vouchers v ON le.voucher_id = v.id
                WHERE v.id IS NULL AND le.voucher_id IS NOT NULL
            ''')
            result = cursor.fetchone()
            logger.info(f"  Orphaned ledger entries: {result['orphaned_ledger_entries']:,}")
            
            cursor.execute('''
                SELECT COUNT(*) as orphaned_inventory_entries
                FROM inventory_entries ie
                LEFT JOIN vouchers v ON ie.voucher_id = v.id
                WHERE v.id IS NULL AND ie.voucher_id IS NOT NULL
            ''')
            result = cursor.fetchone()
            logger.info(f"  Orphaned inventory entries: {result['orphaned_inventory_entries']:,}")
            
        except Exception as e:
            logger.error(f"❌ Error analyzing relationships: {e}")
        finally:
            self.supabase_manager.disconnect()
    
    def analyze_data_patterns(self):
        """Analyze data patterns and distributions."""
        logger.info("📈 Analyzing data patterns...")
        
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return
        
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            # Analyze voucher types
            logger.info("📋 VOUCHER TYPES DISTRIBUTION:")
            cursor.execute('''
                SELECT voucher_type, COUNT(*) as count
                FROM vouchers
                WHERE voucher_type IS NOT NULL
                GROUP BY voucher_type
                ORDER BY count DESC
                LIMIT 10
            ''')
            voucher_types = cursor.fetchall()
            for vt in voucher_types:
                logger.info(f"  {vt['voucher_type']}: {vt['count']:,} vouchers")
            
            # Analyze ledger names
            logger.info("\n📋 TOP LEDGER NAMES:")
            cursor.execute('''
                SELECT ledger_name, COUNT(*) as count
                FROM ledger_entries
                WHERE ledger_name IS NOT NULL AND ledger_name != ''
                GROUP BY ledger_name
                ORDER BY count DESC
                LIMIT 10
            ''')
            ledger_names = cursor.fetchall()
            for ln in ledger_names:
                logger.info(f"  {ln['ledger_name']}: {ln['count']:,} entries")
            
            # Analyze stock item names
            logger.info("\n📋 TOP STOCK ITEM NAMES:")
            cursor.execute('''
                SELECT stock_item_name, COUNT(*) as count
                FROM inventory_entries
                WHERE stock_item_name IS NOT NULL AND stock_item_name != ''
                GROUP BY stock_item_name
                ORDER BY count DESC
                LIMIT 10
            ''')
            stock_items = cursor.fetchall()
            for si in stock_items:
                logger.info(f"  {si['stock_item_name']}: {si['count']:,} entries")
            
            # Analyze date ranges
            logger.info("\n📋 DATE RANGE ANALYSIS:")
            cursor.execute('''
                SELECT 
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date,
                    COUNT(DISTINCT date) as unique_dates
                FROM vouchers
                WHERE date IS NOT NULL
            ''')
            result = cursor.fetchone()
            logger.info(f"  Date range: {result['earliest_date']} to {result['latest_date']}")
            logger.info(f"  Unique dates: {result['unique_dates']:,}")
            
        except Exception as e:
            logger.error(f"❌ Error analyzing data patterns: {e}")
        finally:
            self.supabase_manager.disconnect()
    
    def generate_sample_queries(self):
        """Generate sample queries to test the data."""
        logger.info("🔍 Generating sample queries...")
        
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return
        
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            # Sample query 1: Voucher with its ledger and inventory entries
            logger.info("📋 SAMPLE QUERY 1: Voucher with related entries")
            cursor.execute('''
                SELECT 
                    v.guid,
                    v.date,
                    v.voucher_number,
                    v.voucher_type,
                    v.narration,
                    COUNT(le.id) as ledger_entry_count,
                    COUNT(ie.id) as inventory_entry_count
                FROM vouchers v
                LEFT JOIN ledger_entries le ON v.id = le.voucher_id
                LEFT JOIN inventory_entries ie ON v.id = ie.voucher_id
                GROUP BY v.id, v.guid, v.date, v.voucher_number, v.voucher_type, v.narration
                ORDER BY v.date DESC
                LIMIT 5
            ''')
            results = cursor.fetchall()
            for result in results:
                logger.info(f"  Voucher {result['guid'][:20]}... ({result['date']}): {result['ledger_entry_count']} ledger, {result['inventory_entry_count']} inventory entries")
            
            # Sample query 2: Top vouchers by amount
            logger.info("\n📋 SAMPLE QUERY 2: Top vouchers by ledger amount")
            cursor.execute('''
                SELECT 
                    v.guid,
                    v.date,
                    v.voucher_number,
                    v.voucher_type,
                    SUM(le.amount) as total_amount
                FROM vouchers v
                JOIN ledger_entries le ON v.id = le.voucher_id
                WHERE le.amount IS NOT NULL
                GROUP BY v.id, v.guid, v.date, v.voucher_number, v.voucher_type
                ORDER BY total_amount DESC
                LIMIT 5
            ''')
            results = cursor.fetchall()
            for result in results:
                logger.info(f"  Voucher {result['guid'][:20]}... ({result['date']}): ₹{result['total_amount']:,.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error generating sample queries: {e}")
        finally:
            self.supabase_manager.disconnect()
    
    def run_full_analysis(self):
        """Run complete data quality analysis."""
        logger.info("🚀 Starting comprehensive data quality analysis...")
        logger.info("=" * 60)
        
        self.analyze_table_counts()
        logger.info("=" * 60)
        
        self.analyze_data_quality()
        logger.info("=" * 60)
        
        self.analyze_relationships()
        logger.info("=" * 60)
        
        self.analyze_data_patterns()
        logger.info("=" * 60)
        
        self.generate_sample_queries()
        logger.info("=" * 60)
        
        logger.info("✅ Data quality analysis completed!")

def main():
    analysis = DataQualityAnalysis()
    analysis.run_full_analysis()

if __name__ == "__main__":
    main()
