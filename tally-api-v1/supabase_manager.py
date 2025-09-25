#!/usr/bin/env python3
"""
Supabase Database Manager
=========================

Handles connection to Supabase PostgreSQL database and schema management.
"""

import psycopg2
import psycopg2.extras
from psycopg2 import sql
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from collections import defaultdict

class SupabaseManager:
    """Manages Supabase PostgreSQL database operations"""
    
    def __init__(self):
        self.conn = None
        self.schema_name = "tally"
        self.company_id = "bc90d453-0c64-4f6f-8bbe-dca32aba40d1"
        self.division_id = "b38e3757-f338-4cc3-b754-2ade914290e1"
    
    def connect(self) -> bool:
        """Connect to Supabase database"""
        try:
            self.conn = psycopg2.connect(
                host='aws-0-ap-southeast-1.pooler.supabase.com',
                port=5432,
                database='postgres',
                user='postgres.ppfwlhfehwelinfprviw',
                password='RAJK22**kjar'
            )
            self.conn.autocommit = False
            logging.info("✅ Connected to Supabase database")
            return True
        except Exception as e:
            logging.error(f"❌ Failed to connect to Supabase: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def create_schema(self) -> bool:
        """Create the tally schema if it doesn't exist"""
        if not self.connect():
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # Create schema
            cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                sql.Identifier(self.schema_name)
            ))
            
            # Set search path to include our schema
            cursor.execute(sql.SQL("SET search_path TO {}, public").format(
                sql.Identifier(self.schema_name)
            ))
            
            self.conn.commit()
            logging.info(f"✅ Schema '{self.schema_name}' created/verified")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to create schema: {e}")
            self.conn.rollback()
            return False
        finally:
            self.disconnect()
    
    def create_tables(self) -> bool:
        """Create all tables in the schema"""
        if not self.connect():
            return False
        
        try:
            cursor = self.conn.cursor()
            
            # Set search path
            cursor.execute(sql.SQL("SET search_path TO {}, public").format(
                sql.Identifier(self.schema_name)
            ))
            
            # Enable UUID extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
            
            # Read and execute PostgreSQL schema
            with open('postgres_schema.sql', 'r') as f:
                postgres_sql = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in postgres_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        logging.warning(f"⚠️  Statement failed (may already exist): {e}")
                        continue
            
            self.conn.commit()
            logging.info("✅ All tables created successfully")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to create tables: {e}")
            self.conn.rollback()
            return False
        finally:
            self.disconnect()
    
    def _convert_sqlite_to_postgres(self, sqlite_sql: str) -> str:
        """Convert SQLite schema to PostgreSQL"""
        # Replace SQLite specific syntax with PostgreSQL
        postgres_sql = sqlite_sql
        
        # Replace AUTOINCREMENT with SERIAL
        postgres_sql = postgres_sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
        
        # Replace TEXT with VARCHAR
        postgres_sql = postgres_sql.replace('TEXT', 'VARCHAR')
        
        # Replace DECIMAL with NUMERIC
        postgres_sql = postgres_sql.replace('DECIMAL', 'NUMERIC')
        
        # Replace BOOLEAN with BOOLEAN (PostgreSQL supports this)
        # postgres_sql = postgres_sql.replace('BOOLEAN', 'BOOLEAN')
        
        # Replace TIMESTAMP with TIMESTAMP
        # postgres_sql = postgres_sql.replace('TIMESTAMP', 'TIMESTAMP')
        
        # Replace UUID with UUID (PostgreSQL supports this)
        # postgres_sql = postgres_sql.replace('UUID', 'UUID')
        
        # Remove SQLite specific pragma statements
        postgres_sql = postgres_sql.replace('PRAGMA foreign_keys = ON;', '')
        
        # Replace INSERT OR REPLACE with ON CONFLICT
        postgres_sql = postgres_sql.replace('INSERT OR REPLACE INTO', 'INSERT INTO')
        
        return postgres_sql
    
    def parse_xml_data(self, xml_file_path: str) -> Dict[str, Any]:
        """Parse XML data and organize into structured format"""
        logging.info(f"📖 Parsing XML file: {xml_file_path}")
        
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            vouchers = {}
            ledger_entries = {}
            inventory_entries = {}
            employee_entries = {}
            payhead_allocations = {}
            attendance_entries = {}
            
            current_record = {}
            
            for element in root.iter():
                if element.tag == 'VOUCHER_AMOUNT':
                    # Start of new voucher record
                    if current_record:
                        # Save previous record
                        voucher_id = current_record.get('VOUCHER_ID')
                        if voucher_id:
                            vouchers[voucher_id] = current_record.copy()
                            
                            # Extract ledger entry
                            if 'TRN_LEDGERENTRIES_ID' in current_record:
                                ledger_entries[current_record['TRN_LEDGERENTRIES_ID']] = current_record.copy()
                            
                            # Extract inventory entry
                            if 'TRN_INVENTORYENTRIES_ID' in current_record:
                                inventory_entries[current_record['TRN_INVENTORYENTRIES_ID']] = current_record.copy()
                            
                            # Extract employee entry
                            if 'TRN_EMPLOYEE_GUID' in current_record:
                                employee_entries[current_record['TRN_EMPLOYEE_GUID']] = current_record.copy()
                            
                            # Extract payhead allocation
                            if 'TRN_PAYHEAD_GUID' in current_record:
                                payhead_allocations[current_record['TRN_PAYHEAD_GUID']] = current_record.copy()
                            
                            # Extract attendance entry
                            if 'TRN_ATTENDANCE_GUID' in current_record:
                                attendance_entries[current_record['TRN_ATTENDANCE_GUID']] = current_record.copy()
                    
                    # Start new record
                    current_record = {'VOUCHER_AMOUNT': element.text}
                else:
                    # Add field to current record
                    current_record[element.tag] = element.text
            
            # Handle last record
            if current_record:
                voucher_id = current_record.get('VOUCHER_ID')
                if voucher_id:
                    vouchers[voucher_id] = current_record.copy()
                    
                    # Extract all entry types
                    if 'TRN_LEDGERENTRIES_ID' in current_record:
                        ledger_entries[current_record['TRN_LEDGERENTRIES_ID']] = current_record.copy()
                    if 'TRN_INVENTORYENTRIES_ID' in current_record:
                        inventory_entries[current_record['TRN_INVENTORYENTRIES_ID']] = current_record.copy()
                    if 'TRN_EMPLOYEE_GUID' in current_record:
                        employee_entries[current_record['TRN_EMPLOYEE_GUID']] = current_record.copy()
                    if 'TRN_PAYHEAD_GUID' in current_record:
                        payhead_allocations[current_record['TRN_PAYHEAD_GUID']] = current_record.copy()
                    if 'TRN_ATTENDANCE_GUID' in current_record:
                        attendance_entries[current_record['TRN_ATTENDANCE_GUID']] = current_record.copy()
            
            logging.info(f"📊 Parsed data:")
            logging.info(f"   Vouchers: {len(vouchers)}")
            logging.info(f"   Ledger entries: {len(ledger_entries)}")
            logging.info(f"   Inventory entries: {len(inventory_entries)}")
            logging.info(f"   Employee entries: {len(employee_entries)}")
            logging.info(f"   Payhead allocations: {len(payhead_allocations)}")
            logging.info(f"   Attendance entries: {len(attendance_entries)}")
            
            return {
                'vouchers': vouchers,
                'ledger_entries': ledger_entries,
                'inventory_entries': inventory_entries,
                'employee_entries': employee_entries,
                'payhead_allocations': payhead_allocations,
                'attendance_entries': attendance_entries
            }
            
        except Exception as e:
            logging.error(f"❌ Failed to parse XML: {e}")
            return {}
    
    def safe_decimal(self, value):
        """Safely convert value to float for PostgreSQL"""
        if value is None or value == '' or value == 'None':
            return None
        try:
            # Remove commas from numbers
            if isinstance(value, str):
                value = value.replace(',', '')
            return float(str(value))
        except (ValueError, TypeError):
            return None
    
    def safe_date(self, value):
        """Safely convert value to date"""
        if value is None or value == '' or value == 'None':
            return None
        try:
            # Handle Tally date format (1-Apr-25)
            if isinstance(value, str) and '-' in value:
                parts = value.split('-')
                if len(parts) == 3:
                    day, month, year = parts
                    # Convert 2-digit year to 4-digit
                    if len(year) == 2:
                        year = '20' + year
                    
                    # Convert month name to number
                    month_map = {
                        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                    }
                    month_num = month_map.get(month, month)
                    
                    return f"{year}-{month_num}-{day.zfill(2)}"
            return value
        except:
            return None
    
    def safe_boolean(self, value):
        """Safely convert value to boolean"""
        if value is None or value == '' or value == 'None':
            return None
        return str(value).lower() in ('true', '1', 'yes', 'on')
    
    def upsert_vouchers(self, vouchers: Dict[str, Dict[str, Any]]) -> int:
        """Upsert vouchers with company_id and division_id"""
        if not self.connect():
            return 0
        
        try:
            cursor = self.conn.cursor()
            
            # Set search path
            cursor.execute(sql.SQL("SET search_path TO {}, public").format(
                sql.Identifier(self.schema_name)
            ))
            
            count = 0
            for voucher_guid, voucher_data in vouchers.items():
                try:
                    # Lookup voucher_type_id by name
                    voucher_type_id = None
                    voucher_type = voucher_data.get('VOUCHER_VOUCHER_TYPE')
                    if voucher_type:
                        cursor.execute("SELECT id FROM voucher_types WHERE name = %s", (voucher_type,))
                        result = cursor.fetchone()
                        if result:
                            voucher_type_id = result['id']
                    
                    # Lookup party_ledger_id by name
                    party_ledger_id = None
                    party_name = voucher_data.get('VOUCHER_PARTY_NAME')
                    if party_name:
                        cursor.execute("SELECT id FROM ledgers WHERE name = %s", (party_name,))
                        result = cursor.fetchone()
                        if result:
                            party_ledger_id = result['id']
                    
                    # Upsert voucher
                    cursor.execute("""
                        INSERT INTO vouchers (
                            guid, date, voucher_type, voucher_number, reference_number, 
                            reference_date, narration, party_name, place_of_supply,
                            is_invoice, is_accounting_voucher, is_inventory_voucher, is_order_voucher,
                            voucher_type_id, party_ledger_id, company_id, division_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (guid) DO UPDATE SET
                            date = EXCLUDED.date,
                            voucher_type = EXCLUDED.voucher_type,
                            voucher_number = EXCLUDED.voucher_number,
                            reference_number = EXCLUDED.reference_number,
                            narration = EXCLUDED.narration,
                            party_name = EXCLUDED.party_name,
                            voucher_type_id = EXCLUDED.voucher_type_id,
                            party_ledger_id = EXCLUDED.party_ledger_id,
                            company_id = EXCLUDED.company_id,
                            division_id = EXCLUDED.division_id
                    """, (
                        voucher_data.get('VOUCHER_ID'),
                        self.safe_date(voucher_data.get('VOUCHER_DATE')),
                        voucher_data.get('VOUCHER_VOUCHER_TYPE'),
                        voucher_data.get('VOUCHER_VOUCHER_NUMBER'),
                        voucher_data.get('VOUCHER_REFERENCE'),
                        None,  # reference_date not available
                        voucher_data.get('VOUCHER_NARRATION'),
                        voucher_data.get('VOUCHER_PARTY_NAME'),
                        None,  # place_of_supply not available
                        None,  # is_invoice not available
                        None,  # is_accounting_voucher not available
                        None,  # is_inventory_voucher not available
                        None,  # is_order_voucher not available
                        voucher_type_id,
                        party_ledger_id,
                        self.company_id,
                        self.division_id
                    ))
                    count += 1
                except Exception as e:
                    logging.warning(f"⚠️  Error upserting voucher {voucher_guid}: {e}")
            
            self.conn.commit()
            logging.info(f"✅ Upserted {count} vouchers")
            return count
            
        except Exception as e:
            logging.error(f"❌ Failed to upsert vouchers: {e}")
            self.conn.rollback()
            return 0
        finally:
            self.disconnect()
    
    def get_database_statistics(self) -> Dict[str, int]:
        """Get database statistics"""
        if not self.connect():
            return {}
        
        try:
            cursor = self.conn.cursor()
            
            # Set search path
            cursor.execute(sql.SQL("SET search_path TO {}, public").format(
                sql.Identifier(self.schema_name)
            ))
            
            stats = {}
            
            # List of tables to check
            tables = [
                'vouchers', 'ledger_entries', 'inventory_entries', 'groups',
                'voucher_types', 'ledgers', 'units_of_measure', 'stock_categories',
                'stock_groups', 'stock_items', 'godowns', 'cost_categories',
                'cost_centres', 'employees', 'payheads', 'attendance_types',
                'employee_entries', 'payhead_allocations', 'attendance_entries'
            ]
            
            for table in tables:
                try:
                    cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                        sql.Identifier(table)
                    ))
                    result = cursor.fetchone()
                    stats[table] = result['count'] if result else 0
                except Exception as e:
                    logging.warning(f"⚠️  Table {table} not found: {e}")
                    stats[table] = 0
            
            return stats
            
        except Exception as e:
            logging.error(f"❌ Failed to get statistics: {e}")
            return {}
        finally:
            self.disconnect()
