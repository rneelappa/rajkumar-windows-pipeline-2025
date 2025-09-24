#!/usr/bin/env python3
"""
Test Groups Only - Simple extraction and migration of just Groups
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

def create_groups_tdl():
    """Create simple TDL for extracting Groups only."""
    company_name = config.get_tally_company_name()

    tdl_xml = f"""<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Export</TALLYREQUEST>
        <TYPE>Data</TYPE>
        <ID>GroupsExport</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVEXPORTFORMAT>XML (Data Interchange)</SVEXPORTFORMAT>
                <SVCOMPANYNAME>{company_name}</SVCOMPANYNAME>
            </STATICVARIABLES>
            <TDL>
                <TDLMESSAGE>
                    <REPORT NAME="GroupsExport">
                        <FORMS>GroupsForm</FORMS>
                    </REPORT>
                    <FORM NAME="GroupsForm">
                        <PARTS>GroupsPart</PARTS>
                    </FORM>
                    <PART NAME="GroupsPart">
                        <LINES>GroupsLine</LINES>
                        <REPEAT>GroupsLine : GroupsCollection</REPEAT>
                        <SCROLLED>Vertical</SCROLLED>
                    </PART>
                    <LINE NAME="GroupsLine">
                        <FIELDS>master_guid,master_name,master_alias,master_parent,master_description</FIELDS>
                    </LINE>
                    <FIELD NAME="master_guid"><SET>$Guid</SET></FIELD>
                    <FIELD NAME="master_name"><SET>$Name</SET></FIELD>
                    <FIELD NAME="master_alias"><SET>$Alias</SET></FIELD>
                    <FIELD NAME="master_parent"><SET>$Parent</SET></FIELD>
                    <FIELD NAME="master_description"><SET>$Description</SET></FIELD>
                    <COLLECTION NAME="GroupsCollection">
                        <TYPE>Group</TYPE>
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

def test_groups_extraction():
    """Test simple Groups extraction."""
    logger.info("🔄 Testing Groups extraction...")

    tally_client = TallyClient()
    tdl_xml = create_groups_tdl()

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

        # Parse groups
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

        logger.info(f"📊 Parsed {len(groups)} groups")

        # Show first 10 groups
        for i, group in enumerate(groups[:10]):
            logger.info(f"  Group {i+1}: {group.get('name')} (Parent: {group.get('parent', 'None')})")

        # Migrate to Supabase
        if groups:
            logger.info("🔄 Migrating groups to Supabase...")

            supabase_manager = SupabaseManager()
            if not supabase_manager.connect():
                logger.error("❌ Failed to connect to Supabase")
                return False

            cursor = supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
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
                        config.get_company_id(),
                        config.get_division_id()
                    ))
                    success_count += 1

                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️  Error inserting group {group['name']}: {e}")

            supabase_manager.conn.commit()
            logger.info(f"✅ Groups migrated: {success_count} success, {error_count} errors")

            supabase_manager.disconnect()
            return True

        return False

    except Exception as e:
        logger.error(f"❌ Error in groups extraction: {e}")
        return False

def main():
    test_groups_extraction()

if __name__ == "__main__":
    main()
