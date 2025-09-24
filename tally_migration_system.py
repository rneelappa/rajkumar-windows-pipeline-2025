#!/usr/bin/env python3
"""
Tally Migration System - Production Ready
4-Phase Migration: Tally -> Validate -> Supabase -> Validate
"""

import logging
import xml.etree.ElementTree as ET
import re
import time
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime
from psycopg2.extras import RealDictCursor
from supabase_manager import SupabaseManager
from config_manager import config
from tally_client import TallyClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TallyMigrationSystem:
    """Production-ready 4-phase migration system."""
    
    def __init__(self):
        self.tally_client = TallyClient()
        self.supabase_manager = SupabaseManager()
        self.company_id = config.get_company_id()
        self.division_id = config.get_division_id()
        
    def phase1_extract_from_tally(self) -> Dict[str, List[Dict]]:
        """Phase 1: Extract and validate data from Tally."""
        logger.info("🔄 PHASE 1: Extract Data from Tally")
        
        try:
            extracted_data = {
                'master_data': {},
                'transaction_data': {}
            }
            
            # Extract master data
            master_types = [
                'Group', 'Ledger', 'StockItem', 'VoucherType',
                'GoDown', 'StockCategory', 'StockGroup', 'Unit', 
                'CostCategory', 'CostCentre'
            ]
            
            for master_type in master_types:
                logger.info(f"🔄 Extracting {master_type}...")
                try:
                    tdl_xml = self.create_master_tdl(master_type)
                    response = self.tally_client.send_tdl_request(tdl_xml)
                    
                    if response:
                        records = self.parse_master_records(response)
                        extracted_data['master_data'][master_type] = records
                        logger.info(f"✅ {master_type}: {len(records)} records extracted")
                    else:
                        logger.warning(f"⚠️  No response for {master_type}")
                        extracted_data['master_data'][master_type] = []
                    
                    time.sleep(1)  # Small delay between requests
                except Exception as e:
                    logger.warning(f"⚠️  Error extracting {master_type}: {e}")
                    extracted_data['master_data'][master_type] = []
            
            # Extract transaction data
            logger.info("🔄 Extracting transaction data...")
            try:
                tdl_xml = self.tally_client.create_comprehensive_tdl()
                response = self.tally_client.send_tdl_request(tdl_xml)
                
                if response:
                    vouchers, ledger_entries, inventory_entries = self.parse_transaction_data(response)
                    extracted_data['transaction_data'] = {
                        'vouchers': vouchers,
                        'ledger_entries': ledger_entries,
                        'inventory_entries': inventory_entries
                    }
                    logger.info(f"✅ Transaction data extracted:")
                    logger.info(f"  Vouchers: {len(vouchers)}")
                    logger.info(f"  Ledger Entries: {len(ledger_entries)}")
                    logger.info(f"  Inventory Entries: {len(inventory_entries)}")
                else:
                    logger.warning("⚠️  No transaction data response")
                    extracted_data['transaction_data'] = {
                        'vouchers': [], 'ledger_entries': [], 'inventory_entries': []
                    }
            except Exception as e:
                logger.error(f"❌ Error extracting transaction data: {e}")
                extracted_data['transaction_data'] = {
                    'vouchers': [], 'ledger_entries': [], 'inventory_entries': []
                }
            
            logger.info("✅ Phase 1 completed successfully")
            return extracted_data
            
        except Exception as e:
            logger.error(f"❌ Error in Phase 1: {e}")
            return {'master_data': {}, 'transaction_data': {}}
    
    def phase2_validate_data(self, extracted_data: Dict[str, List[Dict]]) -> bool:
        """Phase 2: Validate extracted data."""
        logger.info("🔍 PHASE 2: Data Validation")
        
        try:
            # Validate master data
            master_data = extracted_data.get('master_data', {})
            total_master_records = 0
            
            logger.info("📊 Master Data Summary:")
            for master_type, records in master_data.items():
                count = len(records)
                logger.info(f"  {master_type}: {count:,} records")
                total_master_records += count
                
                # Basic validation
                if count > 0:
                    sample_record = records[0]
                    if not sample_record.get('guid') or not sample_record.get('name'):
                        logger.warning(f"⚠️  {master_type} has invalid records (missing guid/name)")
            
            # Validate transaction data
            transaction_data = extracted_data.get('transaction_data', {})
            vouchers = transaction_data.get('vouchers', [])
            ledger_entries = transaction_data.get('ledger_entries', [])
            inventory_entries = transaction_data.get('inventory_entries', [])
            
            logger.info("📊 Transaction Data Summary:")
            logger.info(f"  Vouchers: {len(vouchers):,}")
            logger.info(f"  Ledger Entries: {len(ledger_entries):,}")
            logger.info(f"  Inventory Entries: {len(inventory_entries):,}")
            
            # Basic validation
            voucher_guids = set()
            for voucher in vouchers:
                if voucher.get('guid'):
                    voucher_guids.add(voucher['guid'])
                else:
                    logger.warning("⚠️  Found voucher without GUID")
            
            logger.info(f"📈 Total records extracted: {total_master_records + len(vouchers) + len(ledger_entries) + len(inventory_entries):,}")
            
            if total_master_records > 0 and len(vouchers) > 0:
                logger.info("✅ Data validation passed")
                return True
            else:
                logger.warning("⚠️  Data validation found issues - insufficient data")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error validating data: {e}")
            return False
    
    def phase3_migrate_to_supabase(self, extracted_data: Dict[str, List[Dict]]) -> bool:
        """Phase 3: Migrate validated data to Supabase."""
        logger.info("📤 PHASE 3: Migrate to Supabase")
        
        try:
            if not self.supabase_manager.connect():
                logger.error("❌ Failed to connect to Supabase")
                return False
            
            # Migrate master data in batches
            master_data = extracted_data.get('master_data', {})
            batch_size = 1000
            
            for master_type, records in master_data.items():
                if not records:
                    continue
                    
                logger.info(f"🔄 Migrating {master_type} to Supabase...")
                table_name = self.get_master_table_name(master_type)
                
                if not self.migrate_master_batch(table_name, records, batch_size):
                    logger.warning(f"⚠️  Failed to migrate {master_type}")
                else:
                    logger.info(f"✅ {master_type}: {len(records)} records migrated")
                
                time.sleep(1)
            
            # Migrate transaction data in batches
            transaction_data = extracted_data.get('transaction_data', {})
            vouchers = transaction_data.get('vouchers', [])
            ledger_entries = transaction_data.get('ledger_entries', [])
            inventory_entries = transaction_data.get('inventory_entries', [])
            
            # Migrate vouchers first
            if vouchers:
                logger.info("🔄 Migrating vouchers to Supabase...")
                if self.migrate_transaction_batch('vouchers', vouchers, batch_size):
                    logger.info(f"✅ Vouchers: {len(vouchers)} records migrated")
                else:
                    logger.warning("⚠️  Failed to migrate vouchers")
            
            # Migrate ledger entries
            if ledger_entries:
                logger.info("🔄 Migrating ledger entries to Supabase...")
                if self.migrate_transaction_batch('ledger_entries', ledger_entries, batch_size):
                    logger.info(f"✅ Ledger Entries: {len(ledger_entries)} records migrated")
                else:
                    logger.warning("⚠️  Failed to migrate ledger entries")
            
            # Migrate inventory entries
            if inventory_entries:
                logger.info("🔄 Migrating inventory entries to Supabase...")
                if self.migrate_transaction_batch('inventory_entries', inventory_entries, batch_size):
                    logger.info(f"✅ Inventory Entries: {len(inventory_entries)} records migrated")
                else:
                    logger.warning("⚠️  Failed to migrate inventory entries")
            
            self.supabase_manager.disconnect()
            logger.info("✅ Phase 3 completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in Phase 3: {e}")
            return False
    
    def phase4_validate_supabase(self) -> bool:
        """Phase 4: Validate data in Supabase."""
        logger.info("🔍 PHASE 4: Supabase Data Validation")
        
        try:
            if not self.supabase_manager.connect():
                logger.error("❌ Failed to connect to Supabase")
                return False
            
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            # Check record counts
            tables = [
                'groups', 'ledgers', 'stock_items', 'voucher_types',
                'godowns', 'stock_categories', 'stock_groups',
                'units_of_measure', 'cost_categories', 'cost_centres',
                'vouchers', 'ledger_entries', 'inventory_entries'
            ]
            
            logger.info("📊 Supabase Data Summary:")
            total_records = 0
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    result = cursor.fetchone()
                    count = result['count'] if result else 0
                    logger.info(f"  {table}: {count:,} records")
                    total_records += count
                except Exception as e:
                    logger.warning(f"⚠️  Could not count {table}: {e}")
            
            logger.info(f"📈 Total records in Supabase: {total_records:,}")
            
            # Check relationships
            cursor.execute("""
                SELECT COUNT(*) as count FROM ledger_entries le 
                LEFT JOIN vouchers v ON le.voucher_id = v.id 
                WHERE v.id IS NULL
            """)
            orphaned_ledger = cursor.fetchone()['count']
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM inventory_entries ie 
                LEFT JOIN vouchers v ON ie.voucher_id = v.id 
                WHERE v.id IS NULL
            """)
            orphaned_inventory = cursor.fetchone()['count']
            
            if orphaned_ledger > 0:
                logger.warning(f"⚠️  Found {orphaned_ledger} orphaned ledger entries")
            if orphaned_inventory > 0:
                logger.warning(f"⚠️  Found {orphaned_inventory} orphaned inventory entries")
            
            self.supabase_manager.disconnect()
            
            if orphaned_ledger == 0 and orphaned_inventory == 0:
                logger.info("✅ Supabase data validation passed")
                return True
            else:
                logger.warning("⚠️  Supabase data validation found issues")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error validating Supabase data: {e}")
            return False
    
    def run_complete_migration(self) -> bool:
        """Run complete 4-phase migration."""
        logger.info("🚀 Starting Complete Tally Migration System")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Phase 1: Extract from Tally
        extracted_data = self.phase1_extract_from_tally()
        if not extracted_data.get('master_data') and not extracted_data.get('transaction_data'):
            logger.error("❌ Phase 1 failed - no data extracted")
            return False
        
        # Phase 2: Validate data
        if not self.phase2_validate_data(extracted_data):
            logger.error("❌ Phase 2 failed - data validation failed")
            return False
        
        # Phase 3: Migrate to Supabase
        if not self.phase3_migrate_to_supabase(extracted_data):
            logger.error("❌ Phase 3 failed - Supabase migration failed")
            return False
        
        # Phase 4: Validate Supabase
        if not self.phase4_validate_supabase():
            logger.error("❌ Phase 4 failed - Supabase validation failed")
            return False
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info("=" * 80)
        logger.info("🎉 COMPLETE MIGRATION SUCCESSFUL!")
        logger.info(f"⏱️  Total migration time: {duration:.2f} seconds")
        logger.info("=" * 80)
        
        return True
    
    # Helper methods
    def create_master_tdl(self, master_type: str) -> str:
        """Create TDL for master data type."""
        company_name = config.get_tally_company_name()
        return f"""<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Data</TYPE>
        <ID>{master_type}Export</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>XML (Data Interchange)</SVEXPORTFORMAT>
                <SVCOMPANYNAME>{company_name}</SVCOMPANYNAME>
            </STATICVARIABLES>
            <TDL>
                <TDLMESSAGE>
                    <REPORT NAME="{master_type}Export">
                        <FORMS>{master_type}Form</FORMS>
                    </REPORT>
                    <FORM NAME="{master_type}Form">
                        <PARTS>{master_type}Part</PARTS>
                    </FORM>
                    <PART NAME="{master_type}Part">
                        <LINES>{master_type}Line</LINES>
                        <REPEAT>{master_type}Line : {master_type}Collection</REPEAT>
                        <SCROLLED>Vertical</SCROLLED>
                    </PART>
                    <LINE NAME="{master_type}Line">
                        <FIELDS>master_guid,master_name,master_alias,master_parent,master_description</FIELDS>
                    </LINE>
                    <FIELD NAME="master_guid"><SET>$Guid</SET></FIELD>
                    <FIELD NAME="master_name"><SET>$Name</SET></FIELD>
                    <FIELD NAME="master_alias"><SET>$Alias</SET></FIELD>
                    <FIELD NAME="master_parent"><SET>$Parent</SET></FIELD>
                    <FIELD NAME="master_description"><SET>$Description</SET></FIELD>
                    <COLLECTION NAME="{master_type}Collection">
                        <TYPE>{master_type}</TYPE>
                        <COMPANY>{company_name}</COMPANY>
                        <FETCH>Guid</FETCH>
                        <FETCH>Name</FETCH>
                        <FETCH>Alias</FETCH>
                        <FETCH>Parent</FETCH>
                        <FETCH>Description</FETCH>
                    </COLLECTION>
                </TDLMESSAGE>
            </TDL>
        </DESC>
    </BODY>
</ENVELOPE>"""
    
    def parse_master_records(self, xml_content: str) -> list:
        """Parse master data XML."""
        records = []
        cleaned_content = re.sub(r'&#[0-9]+;', '', xml_content)
        cleaned_content = re.sub(r'&(?![a-zA-Z0-9#]+;)', '&amp;', cleaned_content)
        
        root = ET.fromstring(cleaned_content)
        
        guid = None
        name = None
        alias = None
        parent = None
        description = None
        
        for elem in root.iter():
            if elem.tag == 'MASTER_GUID':
                if guid and name:
                    records.append({
                        'guid': guid, 'name': name, 'alias': alias or '',
                        'parent': parent or '', 'description': description or ''
                    })
                guid = elem.text if elem.text else ''
                name = None
                alias = None
                parent = None
                description = None
            elif elem.tag == 'MASTER_NAME':
                name = elem.text if elem.text else ''
            elif elem.tag == 'MASTER_ALIAS':
                alias = elem.text if elem.text else ''
            elif elem.tag == 'MASTER_PARENT':
                parent = elem.text if elem.text else ''
            elif elem.tag == 'MASTER_DESCRIPTION':
                description = elem.text if elem.text else ''
        
        if guid and name:
            records.append({
                'guid': guid, 'name': name, 'alias': alias or '',
                'parent': parent or '', 'description': description or ''
            })
        
        return records
    
    def parse_transaction_data(self, xml_content: str) -> tuple:
        """Parse transaction data XML."""
        vouchers = []
        ledger_entries = []
        inventory_entries = []
        
        cleaned_content = re.sub(r'&#[0-9]+;', '', xml_content)
        cleaned_content = re.sub(r'&(?![a-zA-Z0-9#]+;)', '&amp;', cleaned_content)
        
        root = ET.fromstring(cleaned_content)
        
        current_voucher = {}
        current_ledger_entry = {}
        current_inventory_entry = {}
        
        for elem in root.iter():
            if elem.tag == 'VOUCHER_ID':
                if current_voucher.get('guid'):
                    vouchers.append(current_voucher.copy())
                current_voucher = {'guid': elem.text if elem.text else ''}
            elif elem.tag == 'VOUCHER_DATE':
                current_voucher['date'] = elem.text if elem.text else ''
            elif elem.tag == 'VOUCHER_VOUCHER_TYPE':
                current_voucher['voucher_type'] = elem.text if elem.text else ''
            elif elem.tag == 'VOUCHER_VOUCHER_NUMBER':
                current_voucher['voucher_number'] = elem.text if elem.text else ''
            elif elem.tag == 'VOUCHER_AMOUNT':
                current_voucher['amount'] = elem.text if elem.text else ''
            elif elem.tag == 'VOUCHER_PARTY_NAME':
                current_voucher['party_name'] = elem.text if elem.text else ''
            elif elem.tag == 'VOUCHER_NARRATION':
                current_voucher['narration'] = elem.text if elem.text else ''
            elif elem.tag == 'VOUCHER_REFERENCE':
                current_voucher['reference'] = elem.text if elem.text else ''
            elif elem.tag == 'TRN_LEDGERENTRIES_ID':
                if current_ledger_entry.get('guid'):
                    ledger_entries.append(current_ledger_entry.copy())
                current_ledger_entry = {'guid': elem.text if elem.text else ''}
            elif elem.tag == 'TRN_LEDGERENTRIES_LEDGER_NAME':
                current_ledger_entry['ledger_name'] = elem.text if elem.text else ''
            elif elem.tag == 'TRN_LEDGERENTRIES_AMOUNT':
                current_ledger_entry['amount'] = elem.text if elem.text else ''
            elif elem.tag == 'TRN_LEDGERENTRIES_IS_DEBIT':
                current_ledger_entry['is_debit'] = elem.text if elem.text else ''
            elif elem.tag == 'TRN_INVENTORYENTRIES_ID':
                if current_inventory_entry.get('guid'):
                    inventory_entries.append(current_inventory_entry.copy())
                current_inventory_entry = {'guid': elem.text if elem.text else ''}
            elif elem.tag == 'TRN_INVENTORYENTRIES_STOCKITEM_NAME':
                current_inventory_entry['stockitem_name'] = elem.text if elem.text else ''
            elif elem.tag == 'TRN_INVENTORYENTRIES_QUANTITY':
                current_inventory_entry['quantity'] = elem.text if elem.text else ''
            elif elem.tag == 'TRN_INVENTORYENTRIES_RATE':
                current_inventory_entry['rate'] = elem.text if elem.text else ''
            elif elem.tag == 'TRN_INVENTORYENTRIES_AMOUNT':
                current_inventory_entry['amount'] = elem.text if elem.text else ''
        
        if current_voucher.get('guid'):
            vouchers.append(current_voucher)
        if current_ledger_entry.get('guid'):
            ledger_entries.append(current_ledger_entry)
        if current_inventory_entry.get('guid'):
            inventory_entries.append(current_inventory_entry)
        
        return vouchers, ledger_entries, inventory_entries
    
    def get_master_table_name(self, master_type: str) -> str:
        """Get Supabase table name for master type."""
        mapping = {
            'Group': 'groups',
            'Ledger': 'ledgers',
            'StockItem': 'stock_items',
            'VoucherType': 'voucher_types',
            'GoDown': 'godowns',
            'StockCategory': 'stock_categories',
            'StockGroup': 'stock_groups',
            'Unit': 'units_of_measure',
            'CostCategory': 'cost_categories',
            'CostCentre': 'cost_centres'
        }
        return mapping.get(master_type, master_type.lower())
    
    def migrate_master_batch(self, table_name: str, records: list, batch_size: int) -> bool:
        """Migrate master data batch to Supabase."""
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            offset = 0
            while offset < len(records):
                batch = records[offset:offset + batch_size]
                
                for record in batch:
                    try:
                        cursor.execute(f'''
                            INSERT INTO {table_name} (guid, name, alias, description, company_id, division_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (guid) DO UPDATE SET
                            name = EXCLUDED.name,
                            alias = EXCLUDED.alias,
                            description = EXCLUDED.description
                        ''', (
                            record['guid'], record['name'], record['alias'],
                            record['description'], self.company_id, self.division_id
                        ))
                    except Exception as e:
                        logger.warning(f"⚠️  Error inserting {table_name} record {record.get('name')}: {e}")
                
                self.supabase_manager.conn.commit()
                offset += batch_size
                time.sleep(0.5)  # Small delay between batches
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrating {table_name} batch: {e}")
            return False
    
    def migrate_transaction_batch(self, table_name: str, records: list, batch_size: int) -> bool:
        """Migrate transaction data batch to Supabase."""
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            offset = 0
            while offset < len(records):
                batch = records[offset:offset + batch_size]
                
                for record in batch:
                    try:
                        if table_name == 'vouchers':
                            cursor.execute('''
                                INSERT INTO vouchers (guid, date, voucher_type, voucher_number, amount, 
                                                     party_name, narration, reference, company_id, division_id)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (guid) DO UPDATE SET
                                date = EXCLUDED.date,
                                voucher_type = EXCLUDED.voucher_type,
                                voucher_number = EXCLUDED.voucher_number,
                                amount = EXCLUDED.amount,
                                party_name = EXCLUDED.party_name,
                                narration = EXCLUDED.narration,
                                reference = EXCLUDED.reference
                            ''', (
                                record['guid'], record.get('date'), record.get('voucher_type'),
                                record.get('voucher_number'), record.get('amount'), record.get('party_name'),
                                record.get('narration'), record.get('reference'), self.company_id, self.division_id
                            ))
                        elif table_name == 'ledger_entries':
                            cursor.execute('''
                                INSERT INTO ledger_entries (guid, ledger_name, amount, is_debit, company_id, division_id)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                ON CONFLICT (guid) DO UPDATE SET
                                ledger_name = EXCLUDED.ledger_name,
                                amount = EXCLUDED.amount,
                                is_debit = EXCLUDED.is_debit
                            ''', (
                                record['guid'], record.get('ledger_name'), record.get('amount'),
                                record.get('is_debit'), self.company_id, self.division_id
                            ))
                        elif table_name == 'inventory_entries':
                            cursor.execute('''
                                INSERT INTO inventory_entries (guid, stockitem_name, quantity, rate, amount, company_id, division_id)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (guid) DO UPDATE SET
                                stockitem_name = EXCLUDED.stockitem_name,
                                quantity = EXCLUDED.quantity,
                                rate = EXCLUDED.rate,
                                amount = EXCLUDED.amount
                            ''', (
                                record['guid'], record.get('stockitem_name'), record.get('quantity'),
                                record.get('rate'), record.get('amount'), self.company_id, self.division_id
                            ))
                    except Exception as e:
                        logger.warning(f"⚠️  Error inserting {table_name} record {record.get('guid')}: {e}")
                
                self.supabase_manager.conn.commit()
                offset += batch_size
                time.sleep(0.5)  # Small delay between batches
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error migrating {table_name} batch: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Tally Migration System')
    parser.add_argument('--phase', 
                       choices=['all', '1', '2', '3', '4'],
                       default='all',
                       help='Phase to run (1=extract, 2=validate, 3=migrate, 4=validate supabase)')
    
    args = parser.parse_args()
    
    migration = TallyMigrationSystem()
    
    if args.phase == 'all':
        migration.run_complete_migration()
    elif args.phase == '1':
        data = migration.phase1_extract_from_tally()
        logger.info(f"Extracted data: {data}")
    elif args.phase == '2':
        # This would need extracted data as input
        logger.error("Phase 2 requires extracted data from Phase 1")
    elif args.phase == '3':
        # This would need extracted data as input
        logger.error("Phase 3 requires extracted data from Phase 1")
    elif args.phase == '4':
        migration.phase4_validate_supabase()

if __name__ == "__main__":
    main()