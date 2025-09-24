#!/usr/bin/env python3
"""
Debug XML Structure - See what we're actually getting from Tally
"""

import logging
import xml.etree.ElementTree as ET
from tally_client import TallyClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def debug_xml_structure():
    """Debug the XML structure from Tally."""
    tally_client = TallyClient()
    
    logger.info("🔄 Getting XML from Tally...")
    tdl_xml = tally_client.create_comprehensive_tdl()
    
    try:
        response = tally_client.send_tdl_request(tdl_xml)
        if not response:
            logger.error("❌ No response from Tally")
            return
        
        logger.info(f"✅ Received {len(response)} characters from Tally")
        
        # Parse the XML response
        root = ET.fromstring(response)
        
        # Find all elements that start with VOUCHER_
        voucher_elements = []
        for elem in root.iter():
            if elem.tag.startswith('VOUCHER_'):
                voucher_elements.append(elem)
        
        logger.info(f"📊 Found {len(voucher_elements)} VOUCHER_ elements")
        
        # Show first few voucher elements
        for i, elem in enumerate(voucher_elements[:5]):
            logger.info(f"Voucher element {i+1}: {elem.tag} = {elem.text}")
        
        # Find all elements that start with TRN_LEDGERENTRIES_
        ledger_elements = []
        for elem in root.iter():
            if elem.tag.startswith('TRN_LEDGERENTRIES_'):
                ledger_elements.append(elem)
        
        logger.info(f"📊 Found {len(ledger_elements)} TRN_LEDGERENTRIES_ elements")
        
        # Show first few ledger elements
        for i, elem in enumerate(ledger_elements[:5]):
            logger.info(f"Ledger element {i+1}: {elem.tag} = {elem.text}")
        
        # Find all elements that start with TRN_INVENTORYENTRIES_
        inventory_elements = []
        for elem in root.iter():
            if elem.tag.startswith('TRN_INVENTORYENTRIES_'):
                inventory_elements.append(elem)
        
        logger.info(f"📊 Found {len(inventory_elements)} TRN_INVENTORYENTRIES_ elements")
        
        # Show first few inventory elements
        for i, elem in enumerate(inventory_elements[:5]):
            logger.info(f"Inventory element {i+1}: {elem.tag} = {elem.text}")
        
        # Let's also check what the root structure looks like
        logger.info(f"📊 Root tag: {root.tag}")
        logger.info(f"📊 Root children count: {len(list(root))}")
        
        # Show first few direct children
        for i, child in enumerate(list(root)[:10]):
            logger.info(f"Root child {i+1}: {child.tag}")
            if child.text and child.text.strip():
                logger.info(f"  Text: {child.text.strip()}")
        
    except Exception as e:
        logger.error(f"❌ Error debugging XML structure: {e}")

if __name__ == "__main__":
    debug_xml_structure()
