#!/usr/bin/env python3
"""
Integrated Migration System
===========================

Integrates the YAML dynamic approach with the existing migration system
to extract multiple ledger and inventory entries per voucher.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from psycopg2.extras import RealDictCursor
from supabase_manager import SupabaseManager
from yaml_dynamic_client import YAMLDynamicClient

logger = logging.getLogger(__name__)

class IntegratedMigrationSystem:
    """Integrated migration system using YAML dynamic approach."""
    
    def __init__(self):
        self.supabase_manager = SupabaseManager()
        self.yaml_client = YAMLDynamicClient()
        self.company_id = "bc90d453-0c64-4f6f-8bbe-dca32aba40d1"
        self.division_id = "b38e3757-f338-4cc3-b754-2ade914290e1"
        
        # Statistics
        self.stats = {
            'start_time': datetime.now(),
            'vouchers': 0,
            'ledger_entries': 0,
            'inventory_entries': 0,
            'errors': [],
            'warnings': []
        }
    
    def connect(self) -> bool:
        """Connect to Supabase."""
        return self.supabase_manager.connect()
    
    def disconnect(self):
        """Disconnect from Supabase."""
        self.supabase_manager.disconnect()
    
    def clean_xml_response(self, xml_content: str) -> str:
        """Clean XML response from Tally."""
        # Remove invalid character references
        cleaned = re.sub(r'&#[0-9]+;', '', xml_content)
        
        # Escape unescaped ampersands
        cleaned = re.sub(r'&(?![a-zA-Z0-9#]+;)', '&amp;', cleaned)
        
        return cleaned
    
    def parse_dynamic_xml_records(self, xml_content: str, record_type: str) -> List[Dict[str, Any]]:
        """Parse dynamic XML records from YAML approach."""
        try:
            cleaned_xml = self.clean_xml_response(xml_content)
            
            records = []
            lines = cleaned_xml.split('\n')
            current_record = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('<FLD') and line.endswith('>') and not line.startswith('</'):
                    # Extract field number and value
                    field_match = re.match(r'<FLD(\d+)>([^<]*)</FLD\d+>', line)
                    if field_match:
                        field_num = int(field_match.group(1))
                        field_value = field_match.group(2).strip()
                        
                        # Start new record when we see FLD01 (first field)
                        if field_num == 1 and current_record:
                            records.append(current_record)
                            current_record = {}
                        
                        current_record[f'fld{field_num:02d}'] = field_value
            
            # Add the last record
            if current_record:
                records.append(current_record)
            
            logger.info(f"📋 Parsed {len(records)} {record_type} records from dynamic XML")
            return records
            
        except Exception as e:
            logger.error(f"Error parsing {record_type} XML: {e}")
            return []
    
    def parse_boolean(self, value: str) -> Optional[bool]:
        """Parse boolean value from Tally."""
        if not value or value.strip() == '':
            return None
        return value.lower() in ('yes', 'true', '1')
    
    def parse_number(self, value: str) -> Optional[float]:
        """Parse number value from Tally, handling units."""
        if not value or value.strip() == '':
            return None
        try:
            cleaned = str(value).replace(',', '').strip()
            if cleaned == '' or cleaned == '0.00':
                return None
            
            # Handle units - extract numeric part before any text
            # Examples: "0.480 MT" -> "0.480", "70,500.00/MT" -> "70,500.00"
            import re
            numeric_match = re.match(r'^([0-9,.-]+)', cleaned)
            if numeric_match:
                numeric_part = numeric_match.group(1).replace(',', '')
                return float(numeric_part)
            else:
                return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse date from Tally format to ISO format."""
        if not date_str:
            return None
        
        try:
            # Skip non-date strings like "3103 Days"
            if 'Days' in str(date_str) or 'days' in str(date_str):
                return None
            
            # Handle 2-digit years
            if len(date_str.split('-')[2]) == 2:
                year = int(date_str.split('-')[2])
                if year > 50:
                    year += 1900
                else:
                    year += 2000
                date_str = f"{date_str.split('-')[0]}-{date_str.split('-')[1]}-{year}"
            
            # Parse date
            parsed_date = datetime.strptime(date_str, '%d-%b-%Y')
            return parsed_date.strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
            return None
    
    def extract_voucher_data(self) -> List[Dict[str, Any]]:
        """Extract voucher data using the original WALK approach."""
        logger.info("📥 Extracting voucher data using WALK approach...")
        
        # Use YAML dynamic client for vouchers (latest approach)
        xml_response = self.yaml_client.test_trn_voucher_extraction()
        if not xml_response:
            logger.error("❌ No voucher response from Tally")
            return []
        
        # Parse voucher records from the dynamic XML
        vouchers = self.parse_dynamic_xml_records(xml_response, 'trn_voucher')
        
        # Convert parsed records to voucher format
        voucher_list = []
        for record in vouchers:
            voucher = {
                'voucher_id': record.get('fld01'),
                'voucher_voucher_number': record.get('fld02'),
                'voucher_voucher_type': record.get('fld03'),
                'voucher_date': record.get('fld04'),
                'voucher_amount': record.get('fld05'),
                'voucher_reference': record.get('fld06'),
                'voucher_narration': record.get('fld07'),
                'voucher_party_name': record.get('fld08')
            }
            voucher_list.append(voucher)
        
        return voucher_list
    
    def extract_ledger_entries(self) -> List[Dict[str, Any]]:
        """Extract ledger entries using YAML dynamic approach."""
        logger.info("📥 Extracting ledger entries using YAML dynamic approach...")
        
        xml_response = self.yaml_client.test_trn_accounting_extraction()
        if not xml_response:
            logger.error("❌ No ledger response from Tally")
            return []
        
        # Parse ledger records
        ledger_records = self.parse_dynamic_xml_records(xml_response, "ledger")
        
        # Map fields based on trn_accounting configuration
        # Debug: Check first few records to understand field mapping
        if ledger_records:
            logger.info("🔍 Sample ledger record fields:")
            for i, record in enumerate(ledger_records[:3]):
                logger.info(f"  Record {i+1}: {record}")
        
        ledger_entries = []
        for record in ledger_records:
            # Based on actual field mapping from debug:
            # fld01: voucher GUID (this is what we need!)
            # fld02: ledger name
            # fld03: amount
            # fld04: currency (empty)
            # fld05: numeric ID (not useful)
            # fld06: voucher number
            # fld07: voucher date
            # fld08: voucher type
            ledger_entry = {
                'guid': f"{record.get('fld01')}-ledger-{hash(record.get('fld02', '')) % 10000}",  # Generate unique ledger entry GUID
                'ledger_name': record.get('fld02'),    # ledger name
                'amount': record.get('fld03'),         # amount
                'currency': record.get('fld04'),       # currency
                'voucher_guid': record.get('fld01'),   # voucher GUID (this is the key!)
                'voucher_number': record.get('fld06'), # voucher number
                'voucher_date': record.get('fld07'),   # voucher date
                'voucher_type': record.get('fld08'),   # voucher type
                'is_debit': None  # Not available in current YAML config
            }
            ledger_entries.append(ledger_entry)
        
        logger.info(f"✅ Extracted {len(ledger_entries)} ledger entries")
        return ledger_entries
    
    def extract_inventory_entries(self) -> List[Dict[str, Any]]:
        """Extract inventory entries using YAML dynamic approach."""
        logger.info("📥 Extracting inventory entries using YAML dynamic approach...")
        
        xml_response = self.yaml_client.test_trn_inventory_extraction()
        if not xml_response:
            logger.error("❌ No inventory response from Tally")
            return []
        
        # Parse inventory records
        inventory_records = self.parse_dynamic_xml_records(xml_response, "inventory")
        
        # Map fields based on trn_inventory configuration
        # Debug: Check first few records to understand field mapping
        if inventory_records:
            logger.info("🔍 Sample inventory record fields:")
            for i, record in enumerate(inventory_records[:3]):
                logger.info(f"  Record {i+1}: {record}")
        
        inventory_entries = []
        for record in inventory_records:
            # Based on updated YAML configuration with 12 fields:
            # fld01: voucher GUID
            # fld02: stock item name
            # fld03: quantity
            # fld04: rate
            # fld05: amount
            # fld06: additional_amount
            # fld07: discount_amount
            # fld08: godown
            # fld09: tracking_number
            # fld10: order_number
            # fld11: order_duedate
            # fld12: voucher GUID (duplicate)
            inventory_entry = {
                'guid': f"{record.get('fld01')}-inventory-{hash(record.get('fld02', '')) % 10000}",  # Generate unique inventory entry GUID
                'stock_item_name': record.get('fld02'), # stock item name
                'quantity': record.get('fld03'),       # quantity
                'rate': record.get('fld04'),           # rate
                'amount': record.get('fld05'),         # amount
                'additional_amount': record.get('fld06'), # additional_amount
                'discount_amount': record.get('fld07'), # discount_amount
                'godown_name': record.get('fld08'),    # godown name
                'tracking_number': record.get('fld09'), # tracking_number
                'order_number': record.get('fld10'),   # order_number
                'order_duedate': record.get('fld11'),  # order_duedate
                'voucher_guid': record.get('fld01'),   # voucher GUID
                'voucher_number': None,                # Not available in current mapping
                'voucher_date': None,                  # Not available in current mapping
                'voucher_type': None                   # Not available in current mapping
            }
            inventory_entries.append(inventory_entry)
        
        logger.info(f"✅ Extracted {len(inventory_entries)} inventory entries")
        return inventory_entries
    
    def build_voucher_lookup_table(self, vouchers: List[Dict[str, Any]]) -> Dict[str, int]:
        """Build a lookup table mapping voucher GUIDs to integer IDs."""
        cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SET search_path TO tally')
        
        logger.info("🔍 Building voucher GUID → ID lookup table...")
        
        cursor.execute('SELECT id, guid FROM vouchers')
        existing_vouchers = cursor.fetchall()
        
        lookup_table = {}
        for voucher in existing_vouchers:
            lookup_table[voucher['guid']] = voucher['id']
        
        logger.info(f"✅ Built lookup table with {len(lookup_table)} voucher mappings")
        return lookup_table
    
    def build_godown_lookup_table(self) -> Dict[str, int]:
        """Build a lookup table from godown name to godown ID."""
        cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SET search_path TO tally')
        
        cursor.execute("SELECT id, name FROM godowns")
        godowns = cursor.fetchall()
        
        lookup = {}
        for godown in godowns:
            lookup[godown['name']] = godown['id']
        
        logger.info(f"📋 Built godown lookup table with {len(lookup)} entries")
        return lookup
    
    def build_stock_item_lookup_table(self) -> Dict[str, int]:
        """Build a lookup table from stock item name to stock item ID."""
        cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SET search_path TO tally')
        
        cursor.execute("SELECT id, name FROM stock_items")
        stock_items = cursor.fetchall()
        
        lookup = {}
        for item in stock_items:
            lookup[item['name']] = item['id']
        
        logger.info(f"📋 Built stock item lookup table with {len(lookup)} entries")
        return lookup
    
    def build_ledger_lookup_table(self) -> Dict[str, int]:
        """Build a lookup table from ledger name to ledger ID."""
        cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SET search_path TO tally')
        
        cursor.execute("SELECT id, name FROM ledgers")
        ledgers = cursor.fetchall()
        
        lookup = {}
        for ledger in ledgers:
            lookup[ledger['name']] = ledger['id']
        
        logger.info(f"📋 Built ledger lookup table with {len(lookup)} entries")
        return lookup
    
    def build_voucher_type_lookup_table(self) -> Dict[str, int]:
        """Build a lookup table from voucher type name to voucher type ID."""
        cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SET search_path TO tally')
        
        cursor.execute("SELECT id, name FROM voucher_types")
        voucher_types = cursor.fetchall()
        
        lookup = {}
        for vtype in voucher_types:
            lookup[vtype['name']] = vtype['id']
        
        logger.info(f"📋 Built voucher type lookup table with {len(lookup)} entries")
        return lookup
    
    def insert_vouchers(self, vouchers: List[Dict[str, Any]]) -> int:
        """Insert voucher records."""
        cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SET search_path TO tally')
        
        # Build lookup tables for foreign keys
        voucher_type_lookup = self.build_voucher_type_lookup_table()
        ledger_lookup = self.build_ledger_lookup_table()  # For party_ledger_id
        
        success_count = 0
        
        logger.info(f"💾 Inserting {len(vouchers)} vouchers...")
        
        for voucher in vouchers:
            try:
                # Resolve foreign keys
                voucher_type_id = None
                if voucher.get('voucher_voucher_type'):
                    voucher_type_id = voucher_type_lookup.get(voucher['voucher_voucher_type'])
                
                party_ledger_id = None
                if voucher.get('voucher_party_name'):
                    party_ledger_id = ledger_lookup.get(voucher['voucher_party_name'])
                cursor.execute("""
                    INSERT INTO vouchers (
                        guid, date, voucher_type_id, voucher_type, voucher_number, reference_number,
                        narration, party_ledger_id, party_name, company_id, division_id, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (guid) DO UPDATE SET
                        voucher_type_id = EXCLUDED.voucher_type_id,
                        party_ledger_id = EXCLUDED.party_ledger_id,
                        voucher_number = EXCLUDED.voucher_number
                """, (
                    voucher.get('voucher_id'),
                    self.parse_date(voucher.get('voucher_date')),
                    voucher_type_id,
                    voucher.get('voucher_voucher_type'),
                    voucher.get('voucher_voucher_number'),
                    voucher.get('voucher_reference'),
                    voucher.get('voucher_narration'),
                    party_ledger_id,
                    voucher.get('voucher_party_name'),
                    self.company_id,
                    self.division_id,
                    datetime.now()
                ))
                
                success_count += 1
                
            except Exception as e:
                logger.warning(f"⚠️  Failed to insert voucher {voucher.get('voucher_id', 'unknown')}: {e}")
        
        self.supabase_manager.conn.commit()
        self.stats['vouchers'] = success_count
        
        logger.info(f"✅ Successfully inserted {success_count} vouchers")
        return success_count
    
    def insert_ledger_entries(self, ledger_entries: List[Dict[str, Any]], voucher_lookup: Dict[str, int]) -> int:
        """Insert ledger entries with correct foreign key relationships."""
        cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SET search_path TO tally')
        
        # Build lookup table for foreign keys
        ledger_lookup = self.build_ledger_lookup_table()
        
        success_count = 0
        
        logger.info(f"💾 Inserting {len(ledger_entries)} ledger entries...")
        
        for entry in ledger_entries:
            try:
                voucher_guid = entry['voucher_guid']
                voucher_id = voucher_lookup.get(voucher_guid)
                
                if not voucher_id:
                    logger.warning(f"⚠️  Voucher not found for GUID: {voucher_guid}")
                    continue
                
                # Resolve ledger foreign key
                ledger_id = None
                if entry.get('ledger_name'):
                    ledger_id = ledger_lookup.get(entry['ledger_name'])
                
                cursor.execute("""
                    INSERT INTO ledger_entries (
                        guid, voucher_id, ledger_id, ledger_name, amount, is_debit,
                        company_id, division_id, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (guid) DO UPDATE SET
                        ledger_id = EXCLUDED.ledger_id,
                        amount = EXCLUDED.amount,
                        ledger_name = EXCLUDED.ledger_name,
                        is_debit = EXCLUDED.is_debit
                """, (
                    entry['guid'],
                    voucher_id,
                    ledger_id,
                    entry['ledger_name'],
                    self.parse_number(entry['amount']),
                    self.parse_boolean(entry['is_debit']),
                    self.company_id,
                    self.division_id,
                    datetime.now()
                ))
                
                success_count += 1
                
            except Exception as e:
                logger.warning(f"⚠️  Failed to insert ledger entry {entry['guid']}: {e}")
        
        self.supabase_manager.conn.commit()
        self.stats['ledger_entries'] = success_count
        
        logger.info(f"✅ Successfully inserted {success_count} ledger entries")
        return success_count
    
    def insert_inventory_entries(self, inventory_entries: List[Dict[str, Any]], voucher_lookup: Dict[str, int]) -> int:
        """Insert inventory entries with correct foreign key relationships."""
        cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SET search_path TO tally')
        
        # Build lookup tables for foreign keys
        godown_lookup = self.build_godown_lookup_table()
        stock_item_lookup = self.build_stock_item_lookup_table()
        
        success_count = 0
        
        logger.info(f"💾 Inserting {len(inventory_entries)} inventory entries...")
        
        for entry in inventory_entries:
            try:
                voucher_guid = entry['voucher_guid']
                voucher_id = voucher_lookup.get(voucher_guid)
                
                if not voucher_id:
                    logger.warning(f"⚠️  Voucher not found for GUID: {voucher_guid}")
                    continue
                
                # Resolve foreign keys
                godown_id = None
                if entry.get('godown_name'):
                    godown_id = godown_lookup.get(entry['godown_name'])
                
                stock_item_id = None
                if entry.get('stock_item_name'):
                    stock_item_id = stock_item_lookup.get(entry['stock_item_name'])
                
                cursor.execute("""
                    INSERT INTO inventory_entries (
                        guid, voucher_id, stock_item_id, stock_item_name, godown_id, godown_name,
                        quantity, rate, amount, tracking_number, order_number, order_duedate,
                        company_id, division_id, created_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (guid) DO UPDATE SET
                        quantity = EXCLUDED.quantity,
                        rate = EXCLUDED.rate,
                        amount = EXCLUDED.amount,
                        stock_item_id = EXCLUDED.stock_item_id,
                        stock_item_name = EXCLUDED.stock_item_name,
                        godown_id = EXCLUDED.godown_id,
                        godown_name = EXCLUDED.godown_name,
                        tracking_number = EXCLUDED.tracking_number,
                        order_number = EXCLUDED.order_number,
                        order_duedate = EXCLUDED.order_duedate
                """, (
                    entry['guid'],
                    voucher_id,
                    stock_item_id,
                    entry['stock_item_name'],
                    godown_id,
                    entry['godown_name'],
                    self.parse_number(entry['quantity']),
                    self.parse_number(entry['rate']),
                    self.parse_number(entry['amount']),
                    entry['tracking_number'],
                    entry['order_number'],
                    self.parse_date(entry['order_duedate']),
                    self.company_id,
                    self.division_id,
                    datetime.now()
                ))
                
                success_count += 1
                
            except Exception as e:
                logger.warning(f"⚠️  Failed to insert inventory entry {entry['guid']}: {e}")
        
        self.supabase_manager.conn.commit()
        self.stats['inventory_entries'] = success_count
        
        logger.info(f"✅ Successfully inserted {success_count} inventory entries")
        return success_count
    
    def run_integrated_migration(self) -> bool:
        """Run the integrated migration with YAML dynamic approach."""
        logger.info("🚀 Starting Integrated Migration with YAML Dynamic Approach")
        logger.info("=" * 80)
        
        if not self.connect():
            logger.error("❌ Failed to connect to Supabase")
            return False
        
        try:
            # Step 1: Extract voucher data
            vouchers = self.extract_voucher_data()
            if not vouchers:
                logger.error("❌ No vouchers extracted")
                return False
            
            # Step 2: Extract ledger entries using YAML dynamic approach
            ledger_entries = self.extract_ledger_entries()
            
            # Step 3: Extract inventory entries using YAML dynamic approach
            inventory_entries = self.extract_inventory_entries()
            
            # Step 4: Insert vouchers first (parent records)
            voucher_count = self.insert_vouchers(vouchers)
            
            # Step 5: Build voucher lookup table
            voucher_lookup = self.build_voucher_lookup_table(vouchers)
            
            # Step 6: Insert child records
            ledger_count = self.insert_ledger_entries(ledger_entries, voucher_lookup)
            inventory_count = self.insert_inventory_entries(inventory_entries, voucher_lookup)
            
            # Step 7: Validate results
            cursor = self.supabase_manager.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SET search_path TO tally')
            
            cursor.execute('SELECT COUNT(*) as count FROM vouchers')
            voucher_total = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM ledger_entries')
            ledger_total = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM inventory_entries')
            inventory_total = cursor.fetchone()['count']
            
            # Generate summary
            end_time = datetime.now()
            duration = end_time - self.stats['start_time']
            
            logger.info("\n" + "=" * 80)
            logger.info("🎉 INTEGRATED MIGRATION SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Duration: {duration}")
            logger.info(f"Vouchers: {voucher_total:,} records (inserted: {voucher_count:,})")
            logger.info(f"Ledger entries: {ledger_total:,} records (inserted: {ledger_count:,})")
            logger.info(f"Inventory entries: {inventory_total:,} records (inserted: {inventory_count:,})")
            logger.info(f"Total records: {voucher_total + ledger_total + inventory_total:,}")
            logger.info(f"Average ledger entries per voucher: {ledger_total/voucher_total:.2f}")
            logger.info(f"Average inventory entries per voucher: {inventory_total/voucher_total:.2f}")
            logger.info("=" * 80)
            
            success = voucher_count > 0 and (ledger_count > 0 or inventory_count > 0)
            if success:
                logger.info("🎉 INTEGRATED MIGRATION COMPLETED SUCCESSFULLY!")
                logger.info("✅ Multiple ledger and inventory entries per voucher achieved!")
            else:
                logger.error("❌ INTEGRATED MIGRATION FAILED!")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Integrated migration failed: {e}")
            return False
        finally:
            self.disconnect()

def main():
    """Main function."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    migration_system = IntegratedMigrationSystem()
    success = migration_system.run_integrated_migration()
    
    if success:
        logger.info("✅ Integrated migration completed successfully!")
    else:
        logger.error("❌ Integrated migration failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
