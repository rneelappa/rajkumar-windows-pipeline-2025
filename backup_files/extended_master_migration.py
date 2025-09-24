#!/usr/bin/env python3
"""
Extended Master Data Migration
Extract all master data types from Tally including godowns, stock categories, stock groups, units, cost categories, cost centres
"""

import logging
import xml.etree.ElementTree as ET
import re
import time
from psycopg2.extras import RealDictCursor
from supabase_manager import SupabaseManager
from config_manager import config
from tally_client import TallyClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ExtendedMasterMigration:
    def __init__(self):
        self.tally_client = TallyClient()
        self.supabase_manager = SupabaseManager()
        self.company_id = config.get_company_id()
        self.division_id = config.get_division_id()

    def create_tdl(self, master_type: str) -> str:
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

    def parse_records(self, xml_content: str) -> list:
        """Parse XML content into records."""
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

    def migrate_master_type(self, master_type: str, records: list) -> bool:
        """Migrate records to Supabase."""
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
                    if master_type == 'GoDown':
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

    def migrate_master_data_type(self, master_type: str) -> bool:
        """Migrate a specific master data type."""
        logger.info(f"🔄 Migrating {master_type} data...")

        tdl_xml = self.create_tdl(master_type)

        try:
            response = self.tally_client.send_tdl_request(tdl_xml)
            if not response:
                logger.error(f"❌ No response from Tally for {master_type}")
                return False

            logger.info(f"✅ Received {len(response)} characters for {master_type}")

            # Parse records
            records = self.parse_records(response)
            logger.info(f"📊 Parsed {len(records)} {master_type} records")

            # Show first few records
            for i, record in enumerate(records[:3]):
                logger.info(f"  {master_type} {i+1}: {record.get('name')} (Parent: {record.get('parent', 'None')})")

            # Migrate to Supabase
            if records:
                return self.migrate_master_type(master_type, records)

            return False

        except Exception as e:
            logger.error(f"❌ Error extracting {master_type} data: {e}")
            return False

    def run_extended_migration(self):
        """Run extended master data migration."""
        logger.info("🚀 Starting extended master data migration...")

        # Additional master data types
        master_types = ['GoDown', 'StockCategory', 'StockGroup', 'Unit', 'CostCategory', 'CostCentre']

        results = {}
        for master_type in master_types:
            logger.info(f"🔄 Processing {master_type}...")
            success = self.migrate_master_data_type(master_type)
            results[master_type] = success
            # Small delay between requests
            time.sleep(3)

        # Summary
        success_count = sum(1 for success in results.values() if success)
        logger.info("=" * 60)
        logger.info("📊 EXTENDED MASTER DATA MIGRATION SUMMARY")
        logger.info("=" * 60)
        for master_type, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            logger.info(f"{master_type}: {status}")

        logger.info(f"Overall: {success_count}/{len(master_types)} types migrated successfully")

        if success_count == len(master_types):
            logger.info("🎉 All extended master data types migrated successfully!")
        else:
            logger.warning(f"⚠️  {success_count}/{len(master_types)} extended master data types migrated")

        return success_count == len(master_types)

def main():
    migration = ExtendedMasterMigration()
    migration.run_extended_migration()

if __name__ == "__main__":
    main()
