#!/usr/bin/env python3
"""
Test Stock Items Only - Simple extraction and migration of just Stock Items
"""

import logging
import xml.etree.ElementTree as ET
import re
from psycopg2.extras import RealDictCursor
from supabase_manager import SupabaseManager
from config_manager import config
from tally_client import TallyClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def create_stock_items_tdl():
    """Create simple TDL for extracting Stock Items only."""
    company_name = config.get_tally_company_name()

    tdl_xml = f"""<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Data</TYPE>
        <ID>StockItemsExport</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>XML (Data Interchange)</SVEXPORTFORMAT>
                <SVCOMPANYNAME>{company_name}</SVCOMPANYNAME>
            </STATICVARIABLES>
            <TDL>
                <TDLMESSAGE>
                    <REPORT NAME="StockItemsExport">
                        <FORMS>StockItemsForm</FORMS>
                    </REPORT>
                    <FORM NAME="StockItemsForm">
                        <PARTS>StockItemsPart</PARTS>
                    </FORM>
                    <PART NAME="StockItemsPart">
                        <LINES>StockItemsLine</LINES>
                        <REPEAT>StockItemsLine : StockItemsCollection</REPEAT>
                        <SCROLLED>Vertical</SCROLLED>
                    </PART>
                    <LINE NAME="StockItemsLine">
                        <FIELDS>master_guid,master_name,master_alias,master_parent,master_description</FIELDS>
                    </LINE>
                    <FIELD NAME="master_guid"><SET>$Guid</SET></FIELD>
                    <FIELD NAME="master_name"><SET>$Name</SET></FIELD>
                    <FIELD NAME="master_alias"><SET>$Alias</SET></FIELD>
                    <FIELD NAME="master_parent"><SET>$Parent</SET></FIELD>
                    <FIELD NAME="master_description"><SET>$Description</SET></FIELD>
                    <COLLECTION NAME="StockItemsCollection">
                        <TYPE>StockItem</TYPE>
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

def test_stock_items_extraction():
    """Test simple Stock Items extraction."""
    logger.info("🔄 Testing Stock Items extraction...")

    tally_client = TallyClient()
    tdl_xml = create_stock_items_tdl()

    try:
        response = tally_client.send_tdl_request(tdl_xml)
        if not response:
            logger.error("❌ No response from Tally")
            return False

        logger.info(f"✅ Received {len(response)} characters")

        # Clean XML
        cleaned_response = re.sub(r'&#[0-9]+;', '', response)
        cleaned_response = re.sub(r'&(?![a-zA-Z0-9#]+;)', '&amp;', cleaned_response)

        # Parse XML
        root = ET.fromstring(cleaned_response)

        # Parse stock items
        stock_items = []
        guid = None
        name = None
        alias = None
        parent = None
        description = None

        for elem in root.iter():
            if elem.tag == 'MASTER_GUID':
                # Save previous record if we have data
                if guid and name:
                    stock_items.append({
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
            stock_items.append({
                'guid': guid,
                'name': name,
                'alias': alias or '',
                'parent': parent or '',
                'description': description or ''
            })

        logger.info(f"📊 Parsed {len(stock_items)} stock items")

        # Show first 10 stock items
        for i, item in enumerate(stock_items[:10]):
            logger.info(f"  Stock Item {i+1}: {item.get('name')} (Parent: {item.get('parent', 'None')})")

        # Migrate to Supabase
        if stock_items:
            logger.info("🔄 Migrating stock items to Supabase...")

            supabase_manager = SupabaseManager()
            if not supabase_manager.connect():
                logger.error("❌ Failed to connect to Supabase")
                return False

            cursor = supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
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
                        item['alias'],
                        config.get_company_id(),
                        config.get_division_id()
                    ))
                    success_count += 1

                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting stock item {item['name']}: {e}")

            supabase_manager.conn.commit()
            logger.info(f"✅ Stock items migrated: {success_count} success, {error_count} errors")

            supabase_manager.disconnect()
            return True

        return False

    except Exception as e:
        logger.error(f"❌ Error in stock items extraction: {e}")
        return False

def main():
    test_stock_items_extraction()

if __name__ == "__main__":
    main()
