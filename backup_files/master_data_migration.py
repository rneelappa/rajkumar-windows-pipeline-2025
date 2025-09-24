#!/usr/bin/env python3
"""
Master Data Migration from Tally to Supabase
Extract master data (groups, ledgers, stock items, etc.) from Tally and migrate to Supabase
"""

import argparse
import logging
import xml.etree.ElementTree as ET
from psycopg2.extras import RealDictCursor
from supabase_manager import SupabaseManager
from config_manager import config
from tally_client import TallyClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class MasterDataMigration:
    def __init__(self):
        self.tally_client = TallyClient()
        self.supabase_manager = SupabaseManager()
        self.company_id = config.get_company_id()
        self.division_id = config.get_division_id()
        
    def create_comprehensive_master_data_tdl(self) -> str:
        """Create comprehensive TDL for extracting all master data types from Tally."""
        company_name = config.get_tally_company_name()
        
        tdl_xml = f"""<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Data</TYPE>
        <ID>ComprehensiveMasterExport</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>XML (Data Interchange)</SVEXPORTFORMAT>
                <SVCOMPANYNAME>{company_name}</SVCOMPANYNAME>
            </STATICVARIABLES>
            <TDL>
                <TDLMESSAGE>
                    <REPORT NAME="ComprehensiveMasterExport">
                        <FORMS>ComprehensiveMasterForm</FORMS>
                    </REPORT>
                    <FORM NAME="ComprehensiveMasterForm">
                        <PARTS>ComprehensiveMasterPart</PARTS>
                    </FORM>
                    <PART NAME="ComprehensiveMasterPart">
                        <LINES>ComprehensiveMasterLine</LINES>
                        <REPEAT>ComprehensiveMasterLine : ComprehensiveMasterCollection</REPEAT>
                        <SCROLLED>Vertical</SCROLLED>
                    </PART>
                    <LINE NAME="ComprehensiveMasterLine">
                        <FIELDS>master_type,master_guid,master_name,master_alias,master_parent,master_description,master_opening_balance,master_unit</FIELDS>
                    </LINE>
                    <FIELD NAME="master_type"><SET>$Type</SET></FIELD>
                    <FIELD NAME="master_guid"><SET>$Guid</SET></FIELD>
                    <FIELD NAME="master_name"><SET>$Name</SET></FIELD>
                    <FIELD NAME="master_alias"><SET>$Alias</SET></FIELD>
                    <FIELD NAME="master_parent"><SET>$Parent</SET></FIELD>
                    <FIELD NAME="master_description"><SET>$Description</SET></FIELD>
                    <FIELD NAME="master_opening_balance"><SET>$OpeningBalance</SET></FIELD>
                    <FIELD NAME="master_unit"><SET>$BaseUnits</SET></FIELD>
                    <COLLECTION NAME="ComprehensiveMasterCollection">
                        <TYPE>Group : Ledger : StockItem : VoucherType : Unit : StockGroup : StockCategory : GoDown : CostCentre</TYPE>
                        <COMPANY>{company_name}</COMPANY>
                        <FETCH>Type, Guid, Name, Alias, Parent, Description, OpeningBalance, BaseUnits</FETCH>
                    </COLLECTION>
                </TDLMESSAGE>
            </TDL>
        </DESC>
    </BODY>
</ENVELOPE>"""
        return tdl_xml

    def create_master_data_tdl(self, master_type: str = 'Group') -> str:
        """Create TDL for extracting master data using the exact same pattern as successful transaction data."""
        company_name = config.get_tally_company_name()

        tdl_xml = f"""<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Data</TYPE>
        <ID>MasterDataExport</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>XML (Data Interchange)</SVEXPORTFORMAT>
                <SVCOMPANYNAME>{company_name}</SVCOMPANYNAME>
            </STATICVARIABLES>
            <TDL>
                <TDLMESSAGE>
                    <REPORT NAME="MasterDataExport">
                        <FORMS>MasterDataForm</FORMS>
                    </REPORT>
                    <FORM NAME="MasterDataForm">
                        <PARTS>MasterDataPart</PARTS>
                    </FORM>
                    <PART NAME="MasterDataPart">
                        <LINES>MasterDataLine</LINES>
                        <REPEAT>MasterDataLine : MasterDataCollection</REPEAT>
                        <SCROLLED>Vertical</SCROLLED>
                    </PART>
                    <LINE NAME="MasterDataLine">
                        <FIELDS>master_guid,master_name,master_alias,master_parent,master_description</FIELDS>
                    </LINE>
                    <FIELD NAME="master_guid"><SET>$Guid</SET></FIELD>
                    <FIELD NAME="master_name"><SET>$Name</SET></FIELD>
                    <FIELD NAME="master_alias"><SET>$Alias</SET></FIELD>
                    <FIELD NAME="master_parent"><SET>$Parent</SET></FIELD>
                    <FIELD NAME="master_description"><SET>$Description</SET></FIELD>
                    <COLLECTION NAME="MasterDataCollection">
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

    def extract_master_data_from_tally(self) -> dict:
        """Extract master data from Tally."""
        logger.info("🔄 Extracting master data from Tally...")
        
        tdl_xml = self.create_master_data_tdl('Group')
        
        try:
            response = self.tally_client.send_tdl_request(tdl_xml)
            if not response:
                logger.error("❌ No response from Tally")
                return {}
            
            logger.info(f"✅ Received {len(response)} characters from Tally")
            
            # Clean the XML response to remove invalid characters
            import re
            cleaned_response = re.sub(r'&#[0-9]+;', '', response)  # Remove invalid character references
            # Fix unescaped ampersands (but not already escaped ones)
            cleaned_response = re.sub(r'&(?![a-zA-Z0-9#]+;)', '&amp;', cleaned_response)
            
            # Save cleaned XML for debugging
            with open('master_data_response.xml', 'w', encoding='utf-8') as f:
                f.write(cleaned_response)
            logger.info("💾 Saved cleaned master data XML response")
            
            # Parse the cleaned XML response
            root = ET.fromstring(cleaned_response)
            
            master_data = {
                'groups': [],
                'ledgers': [],
                'stock_items': [],
                'voucher_types': [],
                'employees': [],
                'payheads': []
            }
            
            # Parse master data elements - simple approach matching successful transaction pattern
            records = []

            # Process each element individually
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

            logger.info(f"📊 Parsed {len(records)} real master data records from Tally")

            # Show first few records
            for i, record in enumerate(records[:5]):
                logger.info(f"  Record {i+1}: {record.get('name')} (Parent: {record.get('parent', 'None')})")
            
            # Categorize records based on name patterns (similar to transaction data success)
            groups = []
            ledgers = []
            voucher_types = []
            stock_items = []
            godowns = []
            cost_centres = []
            units = []
            stock_groups = []
            stock_categories = []

            for record in records:
                name = record.get('name', '').lower()
                parent = record.get('parent', '').lower()

                # Categorize based on name patterns (matching successful transaction pattern)
                if 'voucher' in name or 'sales' in name or 'purchase' in name or 'receipt' in name or 'payment' in name:
                    voucher_types.append({
                        'guid': record.get('guid', ''),
                        'name': record.get('name', ''),
                        'alias': record.get('alias', ''),
                        'parent': record.get('parent', '') if record.get('parent') else None,
                        'description': record.get('description', '')
                    })
                elif 'group' in name or 'account' in name or parent == 'primary' or parent == '':
                    # This is likely a group
                    groups.append({
                        'guid': record.get('guid', ''),
                        'name': record.get('name', ''),
                        'alias': record.get('alias', ''),
                        'parent': record.get('parent', '') if record.get('parent') and record.get('parent') != 'primary' else None,
                        'description': record.get('description', '')
                    })
                elif 'stock' in name or 'item' in name or 'product' in name:
                    # This is likely a stock item
                    stock_items.append({
                        'guid': record.get('guid', ''),
                        'name': record.get('name', ''),
                        'alias': record.get('alias', ''),
                        'parent': record.get('parent', '') if record.get('parent') else None,
                        'description': record.get('description', ''),
                        'unit': '',
                        'opening_balance': ''
                    })
                elif 'godown' in name or 'warehouse' in name:
                    # This is likely a godown
                    godowns.append({
                        'guid': record.get('guid', ''),
                        'name': record.get('name', ''),
                        'alias': record.get('alias', ''),
                        'parent': record.get('parent', '') if record.get('parent') else None,
                        'description': record.get('description', '')
                    })
                elif 'cost' in name or 'centre' in name:
                    # This is likely a cost centre
                    cost_centres.append({
                        'guid': record.get('guid', ''),
                        'name': record.get('name', ''),
                        'alias': record.get('alias', ''),
                        'parent': record.get('parent', '') if record.get('parent') else None,
                        'description': record.get('description', '')
                    })
                else:
                    # Everything else is likely a ledger
                    ledgers.append({
                        'guid': record.get('guid', ''),
                        'name': record.get('name', ''),
                        'alias': record.get('alias', ''),
                        'parent': record.get('parent', '') if record.get('parent') else None,
                        'description': record.get('description', ''),
                        'opening_balance': ''
                    })
            
            master_data['groups'] = groups
            master_data['ledgers'] = ledgers
            master_data['voucher_types'] = voucher_types
            master_data['stock_items'] = stock_items
            master_data['godowns'] = godowns
            master_data['cost_centres'] = cost_centres
            master_data['units'] = units
            master_data['stock_groups'] = stock_groups
            master_data['stock_categories'] = stock_categories

            logger.info(f"📊 Categorized master data from Tally:")
            logger.info(f"  Groups: {len(groups)} records")
            logger.info(f"  Ledgers: {len(ledgers)} records")
            logger.info(f"  Voucher Types: {len(voucher_types)} records")
            logger.info(f"  Stock Items: {len(stock_items)} records")
            logger.info(f"  Godowns: {len(godowns)} records")
            logger.info(f"  Cost Centres: {len(cost_centres)} records")
            logger.info(f"  Units: {len(units)} records")
            logger.info(f"  Stock Groups: {len(stock_groups)} records")
            logger.info(f"  Stock Categories: {len(stock_categories)} records")

            # Show samples
            if groups:
                logger.info(f"  Sample Groups: {', '.join([g['name'] for g in groups[:3]])}")
            if ledgers:
                logger.info(f"  Sample Ledgers: {', '.join([l['name'] for l in ledgers[:3]])}")
            if voucher_types:
                logger.info(f"  Sample Voucher Types: {', '.join([vt['name'] for vt in voucher_types[:3]])}")
            if stock_items:
                logger.info(f"  Sample Stock Items: {', '.join([si['name'] for si in stock_items[:3]])}")
            if godowns:
                logger.info(f"  Sample Godowns: {', '.join([g['name'] for g in godowns[:3]])}")
            if cost_centres:
                logger.info(f"  Sample Cost Centres: {', '.join([cc['name'] for cc in cost_centres[:3]])}")
            
            return master_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting master data from Tally: {e}")
            return {}
    
    def migrate_voucher_types(self, voucher_types: list):
        """Migrate voucher types to Supabase."""
        logger.info(f"🔄 Migrating {len(voucher_types)} voucher types...")
        
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return False
        
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            success_count = 0
            error_count = 0
            
            for vt in voucher_types:
                try:
                    cursor.execute('''
                        INSERT INTO voucher_types (
                            guid, name, affects_stock, company_id, division_id
                        ) VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (guid) DO UPDATE SET
                            name = EXCLUDED.name,
                            affects_stock = EXCLUDED.affects_stock
                    ''', (
                        vt['guid'],
                        vt['name'],
                        True,  # Default to affecting stock
                        self.company_id,
                        self.division_id
                    ))
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting voucher type {vt['name']}: {e}")
            
            self.supabase_manager.conn.commit()
            logger.info(f"✅ Voucher types migrated: {success_count} success, {error_count} errors")
            
        except Exception as e:
            logger.error(f"❌ Error migrating voucher types: {e}")
            self.supabase_manager.conn.rollback()
        finally:
            self.supabase_manager.disconnect()
        
        return success_count > 0
    
    def migrate_groups(self, groups: list):
        """Migrate groups to Supabase."""
        logger.info(f"🔄 Migrating {len(groups)} groups...")
        
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return False
        
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            success_count = 0
            error_count = 0
            
            for group in groups:
                try:
                    cursor.execute('''
                        INSERT INTO groups (
                            guid, name, company_id, division_id
                        ) VALUES (%s, %s, %s, %s)
                        ON CONFLICT (guid) DO UPDATE SET
                            name = EXCLUDED.name
                    ''', (
                        group['guid'],
                        group['name'],
                        self.company_id,
                        self.division_id
                    ))
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting group {group['name']}: {e}")
            
            self.supabase_manager.conn.commit()
            logger.info(f"✅ Groups migrated: {success_count} success, {error_count} errors")
            
        except Exception as e:
            logger.error(f"❌ Error migrating groups: {e}")
            self.supabase_manager.conn.rollback()
        finally:
            self.supabase_manager.disconnect()
        
        return success_count > 0
    
    def migrate_ledgers(self, ledgers: list):
        """Migrate ledgers to Supabase."""
        logger.info(f"🔄 Migrating {len(ledgers)} ledgers...")
        
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return False
        
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            success_count = 0
            error_count = 0
            
            for ledger in ledgers:
                try:
                    # Get parent group ID
                    parent_id = None
                    if ledger.get('parent'):
                        cursor.execute('SELECT id FROM groups WHERE guid = %s', (ledger['parent'],))
                        parent_result = cursor.fetchone()
                        if parent_result:
                            parent_id = parent_result['id']
                    
                    cursor.execute('''
                        INSERT INTO ledgers (
                            guid, name, parent_id, company_id, division_id
                        ) VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (guid) DO UPDATE SET
                            name = EXCLUDED.name,
                            parent_id = EXCLUDED.parent_id
                    ''', (
                        ledger['guid'],
                        ledger['name'],
                        parent_id,
                        self.company_id,
                        self.division_id
                    ))
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting ledger {ledger['name']}: {e}")
            
            self.supabase_manager.conn.commit()
            logger.info(f"✅ Ledgers migrated: {success_count} success, {error_count} errors")
            
        except Exception as e:
            logger.error(f"❌ Error migrating ledgers: {e}")
            self.supabase_manager.conn.rollback()
        finally:
            self.supabase_manager.disconnect()
        
        return success_count > 0
    
    def migrate_stock_items(self, stock_items: list):
        """Migrate stock items to Supabase."""
        logger.info(f"🔄 Migrating {len(stock_items)} stock items...")
        
        if not self.supabase_manager.connect():
            logger.error("❌ Failed to connect to Supabase")
            return False
        
        try:
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally, public')
            
            success_count = 0
            error_count = 0
            
            for item in stock_items:
                try:
                    cursor.execute('''
                        INSERT INTO stock_items (
                            guid, name, alias, company_id, division_id
                        ) VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (guid) DO UPDATE SET
                            name = EXCLUDED.name,
                            alias = EXCLUDED.alias
                    ''', (
                        item['guid'],
                        item['name'],
                        item.get('alias', ''),
                        self.company_id,
                        self.division_id
                    ))
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting stock item {item['name']}: {e}")
            
            self.supabase_manager.conn.commit()
            logger.info(f"✅ Stock items migrated: {success_count} success, {error_count} errors")
            
        except Exception as e:
            logger.error(f"❌ Error migrating stock items: {e}")
            self.supabase_manager.conn.rollback()
        finally:
            self.supabase_manager.disconnect()
        
        return success_count > 0
    
    def migrate_master_data_type(self, master_type: str):
        """Migrate a specific master data type."""
        logger.info(f"🔄 Migrating {master_type} data from Tally...")

        tdl_xml = self.create_master_data_tdl(master_type)

        try:
            response = self.tally_client.send_tdl_request(tdl_xml)
            if not response:
                logger.error(f"❌ No response from Tally for {master_type}")
                return False

            logger.info(f"✅ Received {len(response)} characters for {master_type}")

            # Clean the XML response
            import re
            cleaned_response = re.sub(r'&#[0-9]+;', '', response)
            cleaned_response = re.sub(r'&(?![a-zA-Z0-9#]+;)', '&amp;', cleaned_response)

            # Parse the cleaned XML response
            root = ET.fromstring(cleaned_response)

            # Parse master data elements
            current_record = {}
            records = []

            for elem in root.iter():
                if elem.tag.startswith('MASTER_'):
                    tag_name = elem.tag.replace('MASTER_', '').lower()
                    text = elem.text if elem.text else ''
                    text = text.replace('&#4;', '').replace('&amp;', '&').strip()
                    current_record[tag_name] = text

                    if len(current_record) >= 8:
                        records.append(current_record.copy())
                        current_record = {}

            logger.info(f"📊 Parsed {len(records)} {master_type} records from Tally")

            # Categorize and migrate based on type
            if master_type == 'Group' and records:
                groups = []
                for record in records:
                    groups.append({
                        'guid': record.get('guid', ''),
                        'name': record.get('name', ''),
                        'alias': record.get('alias', ''),
                        'parent': record.get('parent', '') if record.get('parent') and record.get('parent') != 'Primary' else None,
                        'description': record.get('description', '')
                    })
                return self.migrate_groups(groups)

            elif master_type == 'Ledger' and records:
                ledgers = []
                for record in records:
                    ledgers.append({
                        'guid': record.get('guid', ''),
                        'name': record.get('name', ''),
                        'alias': record.get('alias', ''),
                        'parent': record.get('parent', '') if record.get('parent') else None,
                        'description': record.get('description', ''),
                        'opening_balance': record.get('opening_balance', '')
                    })
                return self.migrate_ledgers(ledgers)

            elif master_type == 'StockItem' and records:
                stock_items = []
                for record in records:
                    stock_items.append({
                        'guid': record.get('guid', ''),
                        'name': record.get('name', ''),
                        'alias': record.get('alias', ''),
                        'parent': record.get('parent', '') if record.get('parent') else None,
                        'description': record.get('description', ''),
                        'unit': record.get('unit', ''),
                        'opening_balance': record.get('opening_balance', '')
                    })
                return self.migrate_stock_items(stock_items)

            elif master_type == 'VoucherType' and records:
                voucher_types = []
                for record in records:
                    voucher_types.append({
                        'guid': record.get('guid', ''),
                        'name': record.get('name', ''),
                        'alias': record.get('alias', ''),
                        'parent': record.get('parent', '') if record.get('parent') else None,
                        'description': record.get('description', '')
                    })
                return self.migrate_voucher_types(voucher_types)

            return False

        except Exception as e:
            logger.error(f"❌ Error extracting {master_type} data from Tally: {e}")
            return False

    def migrate_all_master_data(self):
        """Migrate all master data one type at a time."""
        logger.info("🚀 Starting master data migration...")

        # Test each master data type individually
        master_types = ['Group', 'Ledger', 'StockItem', 'VoucherType']

        success_count = 0
        for master_type in master_types:
            logger.info(f"🔄 Processing {master_type}...")
            if self.migrate_master_data_type(master_type):
                success_count += 1
            # Small delay between requests
            import time
            time.sleep(2)

        if success_count == len(master_types):
            logger.info("✅ All master data migrated successfully!")
        else:
            logger.warning(f"⚠️  {success_count}/{len(master_types)} master data types migrated")

        return success_count > 0

    def extract_and_migrate_groups(self):
        """Extract and migrate groups only."""
        logger.info("🔄 Extracting Groups from Tally...")
        tdl_xml = self.create_master_data_tdl('Group')

        try:
            response = self.tally_client.send_tdl_request(tdl_xml)
            if not response:
                logger.error("❌ No response from Tally for Groups")
                return False

            logger.info(f"✅ Received {len(response)} characters for Groups")

            # Clean the XML response
            import re
            cleaned_response = re.sub(r'&#[0-9]+;', '', response)
            cleaned_response = re.sub(r'&(?![a-zA-Z0-9#]+;)', '&amp;', cleaned_response)

            # Parse the cleaned XML response
            root = ET.fromstring(cleaned_response)

            # Parse groups - simple approach
            groups = []
            guid = None
            name = None
            alias = None
            parent = None
            description = None

            for elem in root.iter():
                if elem.tag == 'MASTER_GUID':
                    # Save previous record if we have data
                    if guid and name:
                        groups.append({
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
                groups.append({
                    'guid': guid,
                    'name': name,
                    'alias': alias or '',
                    'parent': parent or '',
                    'description': description or ''
                })

            logger.info(f"📊 Parsed {len(groups)} groups from Tally")

            # Show first few groups
            for i, group in enumerate(groups[:5]):
                logger.info(f"  Group {i+1}: {group.get('name')} (Parent: {group.get('parent', 'None')})")

            # Migrate groups
            return self.migrate_groups(groups)

        except Exception as e:
            logger.error(f"❌ Error extracting groups from Tally: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Master Data Migration')
    parser.add_argument('--action', choices=['migrate', 'extract-only'], 
                       default='migrate', help='Action to perform')
    
    args = parser.parse_args()
    
    migration = MasterDataMigration()
    
    if args.action == 'extract-only':
        logger.info("🔄 Extracting master data from Tally only...")
        data = migration.extract_master_data_from_tally()
        logger.info(f"📊 Extracted master data: {len(data)} types")
        for data_type, records in data.items():
            logger.info(f"  - {data_type}: {len(records)} records")
    else:
        migration.migrate_all_master_data()

if __name__ == "__main__":
    main()
