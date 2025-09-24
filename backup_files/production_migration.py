#!/usr/bin/env python3
"""
Production Migration Script - Complete Tally to Supabase Migration
Handles both master data and transaction data in a single production-ready implementation
"""

import logging
import xml.etree.ElementTree as ET
import re
import time
from typing import Dict, List, Any
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

class ProductionMigration:
    """Production-ready complete migration from Tally to Supabase."""
    
    def __init__(self):
        self.tally_client = TallyClient()
        self.supabase_manager = SupabaseManager()
        self.company_id = config.get_company_id()
        self.division_id = config.get_division_id()
        
    def create_master_data_tdl(self, master_type: str) -> str:
        """Create TDL for specific master data type."""
        company_name = config.get_tally_company_name()

        tdl_xml = f"""<ENVELOPE>
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
        return tdl_xml

    def parse_master_records(self, xml_content: str) -> list:
        """Parse master data XML content into records."""
        records = []

        # Clean XML
        cleaned_content = re.sub(r'&#[0-9]+;', '', xml_content)
        cleaned_content = re.sub(r'&(?![a-zA-Z0-9#]+;)', '&amp;', cleaned_content)

        # Parse XML
        root = ET.fromstring(cleaned_content)

        # Parse records
        guid = None
        name = None
        alias = None
        parent = None
        description = None

        for elem in root.iter():
            if elem.tag == 'MASTER_GUID':
                # Save previous record if we have data
                if guid and name:
                    records.append({
                        'guid': guid,
                        'name': name,
                        'alias': alias or '',
                        'parent': parent or '',
                        'description': description or ''
                    })
                # Start new record
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

        # Add the last record
        if guid and name:
            records.append({
                'guid': guid,
                'name': name,
                'alias': alias or '',
                'parent': parent or '',
                'description': description or ''
            })

        return records

    def migrate_master_data_type(self, master_type: str) -> bool:
        """Migrate a specific master data type."""
        logger.info(f"🔄 Migrating {master_type} data...")

        tdl_xml = self.create_master_data_tdl(master_type)

        try:
            response = self.tally_client.send_tdl_request(tdl_xml)
            if not response:
                logger.error(f"❌ No response from Tally for {master_type}")
                return False

            logger.info(f"✅ Received {len(response)} characters for {master_type}")

            # Parse records
            records = self.parse_master_records(response)
            logger.info(f"📊 Parsed {len(records)} {master_type} records")

            # Show first few records
            for i, record in enumerate(records[:3]):
                logger.info(f"  {master_type} {i+1}: {record.get('name')} (Parent: {record.get('parent', 'None')})")

            # Migrate to Supabase
            if records:
                return self.migrate_master_records_to_supabase(master_type, records)

            return False

        except Exception as e:
            logger.error(f"❌ Error extracting {master_type} data: {e}")
            return False

    def migrate_master_records_to_supabase(self, master_type: str, records: list) -> bool:
        """Migrate master records to Supabase."""
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return False

        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')

            success_count = 0
            error_count = 0

            for record in records:
                try:
                    if master_type == 'Group':
                        cursor.execute('''
                            INSERT INTO groups (guid, name, company_id, division_id)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (guid) DO UPDATE SET name = EXCLUDED.name
                        ''', (record['guid'], record['name'], self.company_id, self.division_id))
                    elif master_type == 'Ledger':
                        cursor.execute('''
                            INSERT INTO ledgers (guid, name, company_id, division_id)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (guid) DO UPDATE SET name = EXCLUDED.name
                        ''', (record['guid'], record['name'], self.company_id, self.division_id))
                    elif master_type == 'StockItem':
                        cursor.execute('''
                            INSERT INTO stock_items (guid, name, alias, company_id, division_id)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (guid) DO UPDATE SET name = EXCLUDED.name, alias = EXCLUDED.alias
                        ''', (record['guid'], record['name'], record['alias'], self.company_id, self.division_id))
                    elif master_type == 'VoucherType':
                        cursor.execute('''
                            INSERT INTO voucher_types (guid, name, affects_stock, company_id, division_id)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (guid) DO UPDATE SET name = EXCLUDED.name
                        ''', (record['guid'], record['name'], True, self.company_id, self.division_id))
                    elif master_type == 'GoDown':
                        cursor.execute('''
                            INSERT INTO godowns (guid, name, company_id, division_id)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (guid) DO UPDATE SET name = EXCLUDED.name
                        ''', (record['guid'], record['name'], self.company_id, self.division_id))
                    elif master_type == 'StockCategory':
                        cursor.execute('''
                            INSERT INTO stock_categories (guid, name, alias, description, company_id, division_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (guid) DO UPDATE SET name = EXCLUDED.name, alias = EXCLUDED.alias, description = EXCLUDED.description
                        ''', (record['guid'], record['name'], record['alias'], record['description'], self.company_id, self.division_id))
                    elif master_type == 'StockGroup':
                        cursor.execute('''
                            INSERT INTO stock_groups (guid, name, alias, description, company_id, division_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (guid) DO UPDATE SET name = EXCLUDED.name, alias = EXCLUDED.alias, description = EXCLUDED.description
                        ''', (record['guid'], record['name'], record['alias'], record['description'], self.company_id, self.division_id))
                    elif master_type == 'Unit':
                        cursor.execute('''
                            INSERT INTO units_of_measure (guid, name, company_id, division_id)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (guid) DO UPDATE SET name = EXCLUDED.name
                        ''', (record['guid'], record['name'], self.company_id, self.division_id))
                    elif master_type == 'CostCategory':
                        cursor.execute('''
                            INSERT INTO cost_categories (guid, name, alias, description, company_id, division_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (guid) DO UPDATE SET name = EXCLUDED.name, alias = EXCLUDED.alias, description = EXCLUDED.description
                        ''', (record['guid'], record['name'], record['alias'], record['description'], self.company_id, self.division_id))
                    elif master_type == 'CostCentre':
                        cursor.execute('''
                            INSERT INTO cost_centres (guid, name, company_id, division_id)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (guid) DO UPDATE SET name = EXCLUDED.name
                        ''', (record['guid'], record['name'], self.company_id, self.division_id))

                    success_count += 1

                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting {master_type} {record['name']}: {e}")

            self.supabase_manager.conn.commit()
            logger.info(f"✅ {master_type} migrated: {success_count} success, {error_count} errors")

            self.supabase_manager.disconnect()
            return success_count > 0

        except Exception as e:
            logger.error(f"❌ Error migrating {master_type}: {e}")
            self.supabase_manager.conn.rollback()
            self.supabase_manager.disconnect()
            return False

    def migrate_all_master_data(self) -> bool:
        """Migrate all master data types."""
        logger.info("🔄 Starting master data migration...")

        # All master data types
        master_types = [
            'Group', 'Ledger', 'StockItem', 'VoucherType',
            'GoDown', 'StockCategory', 'StockGroup', 'Unit', 
            'CostCategory', 'CostCentre'
        ]

        results = {}
        for master_type in master_types:
            logger.info(f"🔄 Processing {master_type}...")
            success = self.migrate_master_data_type(master_type)
            results[master_type] = success
            # Small delay between requests
            time.sleep(2)

        # Summary
        success_count = sum(1 for success in results.values() if success)
        logger.info("=" * 60)
        logger.info("📊 MASTER DATA MIGRATION SUMMARY")
        logger.info("=" * 60)
        for master_type, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            logger.info(f"{master_type}: {status}")

        logger.info(f"Overall: {success_count}/{len(master_types)} types migrated successfully")
        return success_count == len(master_types)

    def migrate_transaction_data(self) -> bool:
        """Migrate transaction data using comprehensive TDL."""
        logger.info("🔄 Migrating transaction data...")

        try:
            # Use the comprehensive TDL that works
            tdl_xml = self.tally_client.create_comprehensive_tdl()
            
            response = self.tally_client.send_tdl_request(tdl_xml)
            if not response:
                logger.error("❌ No response from Tally for transaction data")
                return False
                
            logger.info(f"✅ Received {len(response)} characters for transaction data")
            
            # Parse and migrate transaction data
            return self.parse_and_migrate_transaction_data(response)
            
        except Exception as e:
            logger.error(f"❌ Error migrating transaction data: {e}")
            return False

    def parse_and_migrate_transaction_data(self, xml_content: str) -> bool:
        """Parse and migrate transaction data from XML."""
        try:
            # Clean XML
            cleaned_content = re.sub(r'&#[0-9]+;', '', xml_content)
            cleaned_content = re.sub(r'&(?![a-zA-Z0-9#]+;)', '&amp;', cleaned_content)

            # Parse XML
            root = ET.fromstring(cleaned_content)

            # Parse transaction data
            vouchers = []
            ledger_entries = []
            inventory_entries = []

            current_voucher = {}
            current_ledger_entry = {}
            current_inventory_entry = {}

            for elem in root.iter():
                if elem.tag == 'VOUCHER_ID':
                    # Save previous voucher if exists
                    if current_voucher.get('guid'):
                        vouchers.append(current_voucher.copy())
                    # Start new voucher
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
                    # Save previous ledger entry if exists
                    if current_ledger_entry.get('guid'):
                        ledger_entries.append(current_ledger_entry.copy())
                    # Start new ledger entry
                    current_ledger_entry = {'guid': elem.text if elem.text else ''}
                elif elem.tag == 'TRN_LEDGERENTRIES_LEDGER_NAME':
                    current_ledger_entry['ledger_name'] = elem.text if elem.text else ''
                elif elem.tag == 'TRN_LEDGERENTRIES_AMOUNT':
                    current_ledger_entry['amount'] = elem.text if elem.text else ''
                elif elem.tag == 'TRN_LEDGERENTRIES_IS_DEBIT':
                    current_ledger_entry['is_debit'] = elem.text if elem.text else ''
                elif elem.tag == 'TRN_INVENTORYENTRIES_ID':
                    # Save previous inventory entry if exists
                    if current_inventory_entry.get('guid'):
                        inventory_entries.append(current_inventory_entry.copy())
                    # Start new inventory entry
                    current_inventory_entry = {'guid': elem.text if elem.text else ''}
                elif elem.tag == 'TRN_INVENTORYENTRIES_STOCKITEM_NAME':
                    current_inventory_entry['stockitem_name'] = elem.text if elem.text else ''
                elif elem.tag == 'TRN_INVENTORYENTRIES_QUANTITY':
                    current_inventory_entry['quantity'] = elem.text if elem.text else ''
                elif elem.tag == 'TRN_INVENTORYENTRIES_RATE':
                    current_inventory_entry['rate'] = elem.text if elem.text else ''
                elif elem.tag == 'TRN_INVENTORYENTRIES_AMOUNT':
                    current_inventory_entry['amount'] = elem.text if elem.text else ''

            # Add the last records
            if current_voucher.get('guid'):
                vouchers.append(current_voucher)
            if current_ledger_entry.get('guid'):
                ledger_entries.append(current_ledger_entry)
            if current_inventory_entry.get('guid'):
                inventory_entries.append(current_inventory_entry)

            logger.info(f"📊 Parsed transaction data:")
            logger.info(f"  Vouchers: {len(vouchers)}")
            logger.info(f"  Ledger Entries: {len(ledger_entries)}")
            logger.info(f"  Inventory Entries: {len(inventory_entries)}")

            # Migrate to Supabase
            return self.migrate_transaction_records_to_supabase(vouchers, ledger_entries, inventory_entries)

        except Exception as e:
            logger.error(f"❌ Error parsing transaction data: {e}")
            return False

    def migrate_transaction_records_to_supabase(self, vouchers: list, ledger_entries: list, inventory_entries: list) -> bool:
        """Migrate transaction records to Supabase."""
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return False

        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')

            # Migrate vouchers first
            voucher_success = 0
            voucher_errors = 0

            for voucher in vouchers:
                try:
                    cursor.execute('''
                        INSERT INTO vouchers (
                            guid, date, voucher_type, voucher_number, amount, 
                            party_name, narration, reference, company_id, division_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (guid) DO UPDATE SET
                            date = EXCLUDED.date,
                            voucher_type = EXCLUDED.voucher_type,
                            voucher_number = EXCLUDED.voucher_number,
                            amount = EXCLUDED.amount,
                            party_name = EXCLUDED.party_name,
                            narration = EXCLUDED.narration,
                            reference = EXCLUDED.reference
                    ''', (
                        voucher['guid'], voucher['date'], voucher['voucher_type'],
                        voucher['voucher_number'], voucher['amount'], voucher['party_name'],
                        voucher['narration'], voucher['reference'], self.company_id, self.division_id
                    ))
                    voucher_success += 1
                except Exception as e:
                    voucher_errors += 1
                    logger.warning(f"⚠️  Error inserting voucher {voucher.get('guid')}: {e}")

            logger.info(f"✅ Vouchers migrated: {voucher_success} success, {voucher_errors} errors")

            # Migrate ledger entries
            ledger_success = 0
            ledger_errors = 0

            for ledger_entry in ledger_entries:
                try:
                    cursor.execute('''
                        INSERT INTO ledger_entries (
                            guid, ledger_name, amount, is_debit, company_id, division_id
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (guid) DO UPDATE SET
                            ledger_name = EXCLUDED.ledger_name,
                            amount = EXCLUDED.amount,
                            is_debit = EXCLUDED.is_debit
                    ''', (
                        ledger_entry['guid'], ledger_entry['ledger_name'],
                        ledger_entry['amount'], ledger_entry['is_debit'],
                        self.company_id, self.division_id
                    ))
                    ledger_success += 1
                except Exception as e:
                    ledger_errors += 1
                    logger.warning(f"⚠️  Error inserting ledger entry {ledger_entry.get('guid')}: {e}")

            logger.info(f"✅ Ledger entries migrated: {ledger_success} success, {ledger_errors} errors")

            # Migrate inventory entries
            inventory_success = 0
            inventory_errors = 0

            for inventory_entry in inventory_entries:
                try:
                    cursor.execute('''
                        INSERT INTO inventory_entries (
                            guid, stockitem_name, quantity, rate, amount, company_id, division_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (guid) DO UPDATE SET
                            stockitem_name = EXCLUDED.stockitem_name,
                            quantity = EXCLUDED.quantity,
                            rate = EXCLUDED.rate,
                            amount = EXCLUDED.amount
                    ''', (
                        inventory_entry['guid'], inventory_entry['stockitem_name'],
                        inventory_entry['quantity'], inventory_entry['rate'],
                        inventory_entry['amount'], self.company_id, self.division_id
                    ))
                    inventory_success += 1
                except Exception as e:
                    inventory_errors += 1
                    logger.warning(f"⚠️  Error inserting inventory entry {inventory_entry.get('guid')}: {e}")

            logger.info(f"✅ Inventory entries migrated: {inventory_success} success, {inventory_errors} errors")

            self.supabase_manager.conn.commit()
            self.supabase_manager.disconnect()
            return True

        except Exception as e:
            logger.error(f"❌ Error migrating transaction records: {e}")
            self.supabase_manager.conn.rollback()
            self.supabase_manager.disconnect()
            return False

    def get_migration_summary(self) -> Dict[str, Any]:
        """Get summary of migrated data."""
        if not self.supabase_manager.connect():
            return {}
            
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            summary = {}
            
            # Count records in each table
            tables = [
                'vouchers', 'ledger_entries', 'inventory_entries',
                'groups', 'ledgers', 'stock_items', 'voucher_types',
                'godowns', 'stock_categories', 'stock_groups', 
                'units_of_measure', 'cost_categories', 'cost_centres'
            ]
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    result = cursor.fetchone()
                    count = result['count'] if result else 0
                    summary[table] = count
                except Exception as e:
                    logger.warning(f"⚠️  Could not count {table}: {e}")
                    summary[table] = 0
                    
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error getting migration summary: {e}")
            return {}
        finally:
            self.supabase_manager.disconnect()

    def run_complete_migration(self) -> bool:
        """Run complete migration from Tally to Supabase."""
        logger.info("🚀 Starting COMPLETE Tally to Supabase migration...")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Step 1: Migrate all master data
        logger.info("📋 STEP 1: Migrating Master Data")
        logger.info("-" * 40)
        if not self.migrate_all_master_data():
            logger.error("❌ Master data migration failed")
            return False
        
        # Step 2: Migrate transaction data
        logger.info("📋 STEP 2: Migrating Transaction Data")
        logger.info("-" * 40)
        if not self.migrate_transaction_data():
            logger.error("❌ Transaction data migration failed")
            return False
        
        # Step 3: Show final summary
        logger.info("📋 STEP 3: Migration Summary")
        logger.info("-" * 40)
        summary = self.get_migration_summary()
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info("=" * 80)
        logger.info("🎉 COMPLETE MIGRATION SUMMARY")
        logger.info("=" * 80)
        
        # Master data summary
        logger.info("📊 MASTER DATA:")
        master_tables = ['groups', 'ledgers', 'stock_items', 'voucher_types', 
                        'godowns', 'stock_categories', 'stock_groups', 
                        'units_of_measure', 'cost_categories', 'cost_centres']
        for table in master_tables:
            count = summary.get(table, 0)
            logger.info(f"  {table}: {count:,} records")
        
        # Transaction data summary
        logger.info("📊 TRANSACTION DATA:")
        transaction_tables = ['vouchers', 'ledger_entries', 'inventory_entries']
        for table in transaction_tables:
            count = summary.get(table, 0)
            logger.info(f"  {table}: {count:,} records")
        
        total_records = sum(summary.values())
        logger.info(f"📈 TOTAL RECORDS MIGRATED: {total_records:,}")
        logger.info(f"⏱️  TOTAL MIGRATION TIME: {duration:.2f} seconds")
        logger.info("✅ COMPLETE MIGRATION FINISHED SUCCESSFULLY!")
        
        return True

def main():
    migration = ProductionMigration()
    migration.run_complete_migration()

if __name__ == "__main__":
    main()
