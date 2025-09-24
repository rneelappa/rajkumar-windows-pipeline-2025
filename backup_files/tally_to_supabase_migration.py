#!/usr/bin/env python3
"""
Tally to Supabase Migration Script
==================================

Main script for migrating data from Tally to Supabase PostgreSQL database.
Handles schema creation, data extraction, and upsert operations.
"""

import argparse
import logging
import sys
from datetime import datetime
from config_manager import config
from tally_client import TallyClient
from supabase_manager import SupabaseManager

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('migration.log')
        ]
    )

def create_schema(supabase_manager: SupabaseManager) -> bool:
    """Create Supabase schema and tables"""
    logging.info("🏗️  Creating Supabase schema and tables...")
    
    # Create schema
    if not supabase_manager.create_schema():
        logging.error("❌ Failed to create schema")
        return False
    
    # Create tables
    if not supabase_manager.create_tables():
        logging.error("❌ Failed to create tables")
        return False
    
    logging.info("✅ Schema and tables created successfully")
    return True

def extract_tally_data(tally_client: TallyClient) -> str:
    """Extract data from Tally and save to XML file"""
    logging.info("📤 Extracting data from Tally...")
    
    # Test connection first
    if not tally_client.test_connection():
        logging.error("❌ Cannot connect to Tally server")
        return None
    
    # Create comprehensive TDL
    tdl_xml = tally_client.create_comprehensive_tdl()
    
    # Export data
    response = tally_client.send_tdl_request(tdl_xml)
    
    if not response:
        logging.error("❌ Failed to extract data from Tally")
        return None
    
    # Save response to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    xml_filename = f"tally_export_{timestamp}.xml"
    
    with open(xml_filename, 'w', encoding='utf-8') as f:
        f.write(response)
    
    logging.info(f"✅ Data extracted and saved to {xml_filename}")
    return xml_filename

def migrate_data(supabase_manager: SupabaseManager, xml_file: str) -> bool:
    """Migrate data from XML to Supabase"""
    logging.info(f"📥 Migrating data from {xml_file} to Supabase...")
    
    # Parse XML data
    data = supabase_manager.parse_xml_data(xml_file)
    
    if not data or not data.get('vouchers'):
        logging.error("❌ No data to migrate")
        return False
    
    # Upsert vouchers
    voucher_count = supabase_manager.upsert_vouchers(data['vouchers'])
    
    if voucher_count == 0:
        logging.error("❌ Failed to migrate vouchers")
        return False
    
    logging.info(f"✅ Successfully migrated {voucher_count} vouchers")
    return True

def show_statistics(supabase_manager: SupabaseManager):
    """Show database statistics"""
    logging.info("📊 Database Statistics:")
    logging.info("=" * 50)
    
    stats = supabase_manager.get_database_statistics()
    
    for table, count in stats.items():
        logging.info(f"{table:<30}: {count:>8} records")
    
    total_records = sum(stats.values())
    logging.info("=" * 50)
    logging.info(f"{'Total Records':<30}: {total_records:>8}")

def main():
    """Main migration function"""
    parser = argparse.ArgumentParser(description='Tally to Supabase Migration')
    parser.add_argument('--action', choices=['create-schema', 'extract', 'migrate', 'full-migration', 'stats'], 
                       default='full-migration', help='Action to perform')
    parser.add_argument('--xml-file', help='XML file for migration (required for migrate action)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Validate configuration
    if not config.validate_config():
        logging.error("❌ Invalid configuration")
        return 1
    
    logging.info("🚀 Starting Tally to Supabase Migration")
    logging.info(f"Company: {config.get_tally_company_name()}")
    logging.info(f"Tally URL: {config.get_tally_url()}")
    logging.info(f"Supabase Schema: {config.get_supabase_schema()}")
    
    # Initialize managers
    tally_client = TallyClient()
    supabase_manager = SupabaseManager()
    
    try:
        if args.action == 'create-schema':
            # Create schema only
            if not create_schema(supabase_manager):
                return 1
            
        elif args.action == 'extract':
            # Extract data from Tally only
            xml_file = extract_tally_data(tally_client)
            if not xml_file:
                return 1
            
        elif args.action == 'migrate':
            # Migrate data from XML file
            if not args.xml_file:
                logging.error("❌ XML file required for migrate action")
                return 1
            
            if not migrate_data(supabase_manager, args.xml_file):
                return 1
            
        elif args.action == 'full-migration':
            # Full migration: create schema, extract data, and migrate
            if not create_schema(supabase_manager):
                return 1
            
            xml_file = extract_tally_data(tally_client)
            if not xml_file:
                return 1
            
            if not migrate_data(supabase_manager, xml_file):
                return 1
            
        elif args.action == 'stats':
            # Show statistics
            show_statistics(supabase_manager)
        
        logging.info("✅ Migration completed successfully")
        return 0
        
    except Exception as e:
        logging.error(f"❌ Migration failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
