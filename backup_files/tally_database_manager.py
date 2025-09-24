#!/usr/bin/env python3
"""
Tally Database Manager
=====================

This script creates and populates a SQLite database from Tally XML data.
It handles the comprehensive XML output from our Tally export and creates
proper relational database structure with foreign key relationships.

Usage:
    python3 tally_database_manager.py --create-db
    python3 tally_database_manager.py --populate-db --xml-file xml-files/comprehensive_extended_test.xml
    python3 tally_database_manager.py --show-stats
"""

import sqlite3
import xml.etree.ElementTree as ET
import argparse
import os
from typing import Dict, List, Any
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from config_manager import config

class TallyDatabaseManager:
    def __init__(self, db_path='tally_data.db'):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute("PRAGMA journal_mode = WAL")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def create_database(self):
        """Create database schema from SQL file"""
        if not self.connect():
            return False
        
        try:
            # Read and execute SQL schema
            with open('database_schema.sql', 'r') as f:
                schema_sql = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    self.conn.execute(statement)
            
            self.conn.commit()
            print("✅ Database schema created successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Database creation failed: {e}")
            self.conn.rollback()
            return False
        finally:
            self.disconnect()

    def insert_master_data(self, master_data: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Insert master data with proper parent-child relationships"""
        if not self.connect():
            return False

        try:
            cursor = self.conn.cursor()

            # Insert groups (with parent-child relationships)
            if 'groups' in master_data:
                self._insert_groups(cursor, master_data['groups'])

            # Insert voucher types (with parent-child relationships)
            if 'voucher_types' in master_data:
                self._insert_voucher_types(cursor, master_data['voucher_types'])

            # Insert units of measure
            if 'units_of_measure' in master_data:
                self._insert_units_of_measure(cursor, master_data['units_of_measure'])

            # Insert stock categories (with parent-child relationships)
            if 'stock_categories' in master_data:
                self._insert_stock_categories(cursor, master_data['stock_categories'])

            # Insert stock groups (with parent-child relationships)
            if 'stock_groups' in master_data:
                self._insert_stock_groups(cursor, master_data['stock_groups'])

            # Insert cost categories (with parent-child relationships)
            if 'cost_categories' in master_data:
                self._insert_cost_categories(cursor, master_data['cost_categories'])

            # Insert cost centres (with parent-child relationships)
            if 'cost_centres' in master_data:
                self._insert_cost_centres(cursor, master_data['cost_centres'])

            # Insert attendance types (with parent-child relationships)
            if 'attendance_types' in master_data:
                self._insert_attendance_types(cursor, master_data['attendance_types'])

            # Insert ledgers (with parent-child relationships)
            if 'ledgers' in master_data:
                self._insert_ledgers(cursor, master_data['ledgers'])

            # Insert godowns (with parent-child relationships)
            if 'godowns' in master_data:
                self._insert_godowns(cursor, master_data['godowns'])

            # Insert stock items (with relationships to groups, categories, UOM)
            if 'stock_items' in master_data:
                self._insert_stock_items(cursor, master_data['stock_items'])

            # Insert employees (with cost centre relationships)
            if 'employees' in master_data:
                self._insert_employees(cursor, master_data['employees'])

            # Insert payheads (with group relationships)
            if 'payheads' in master_data:
                self._insert_payheads(cursor, master_data['payheads'])

            self.conn.commit()
            print("✅ Master data inserted successfully!")
            return True

        except Exception as e:
            print(f"❌ Master data insertion failed: {e}")
            self.conn.rollback()
            return False
        finally:
            self.disconnect()

    def _insert_groups(self, cursor, groups: List[Dict[str, Any]]):
        """Insert groups with parent-child relationships"""
        print("📥 Inserting groups...")
        count = 0

        for group_data in groups:
            try:
                # Lookup parent_id by name if parent exists
                parent_id = None
                parent_name = group_data.get('parent')
                if parent_name:
                    cursor.execute("SELECT id FROM groups WHERE name = ?", (parent_name,))
                    result = cursor.fetchone()
                    if result:
                        parent_id = result[0]

                cursor.execute("""
                    INSERT OR REPLACE INTO groups (
                        guid, name, parent_id, primary_group, is_revenue, is_deemedpositive,
                        is_reserved, affects_gross_profit, sort_position
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    group_data.get('guid'),
                    group_data.get('name'),
                    parent_id,  # Store parent_id instead of parent name
                    group_data.get('primary_group'),
                    self.safe_boolean(group_data.get('is_revenue')),
                    self.safe_boolean(group_data.get('is_deemedpositive')),
                    self.safe_boolean(group_data.get('is_reserved')),
                    self.safe_boolean(group_data.get('affects_gross_profit')),
                    self.safe_decimal(group_data.get('sort_position'))
                ))
                count += 1
            except Exception as e:
                print(f"⚠️  Error inserting group {group_data.get('guid')}: {e}")

        print(f"   Groups inserted: {count}")

    def _insert_voucher_types(self, cursor, voucher_types: List[Dict[str, Any]]):
        """Insert voucher types with parent-child relationships"""
        print("📥 Inserting voucher types...")
        count = 0

        for vt_data in voucher_types:
            try:
                # Lookup parent_id by name if parent exists
                parent_id = None
                parent_name = vt_data.get('parent')
                if parent_name:
                    cursor.execute("SELECT id FROM voucher_types WHERE name = ?", (parent_name,))
                    result = cursor.fetchone()
                    if result:
                        parent_id = result[0]

                cursor.execute("""
                    INSERT OR REPLACE INTO voucher_types (
                        guid, name, parent_id, numbering_method, is_deemedpositive, affects_stock
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    vt_data.get('guid'),
                    vt_data.get('name'),
                    parent_id,  # Store parent_id instead of parent name
                    vt_data.get('numbering_method'),
                    self.safe_boolean(vt_data.get('is_deemedpositive')),
                    self.safe_boolean(vt_data.get('affects_stock'))
                ))
                count += 1
            except Exception as e:
                print(f"⚠️  Error inserting voucher type {vt_data.get('guid')}: {e}")

        print(f"   Voucher types inserted: {count}")

    def _insert_units_of_measure(self, cursor, uoms: List[Dict[str, Any]]):
        """Insert units of measure"""
        print("📥 Inserting units of measure...")
        count = 0

        for uom_data in uoms:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO units_of_measure (
                        guid, name, parent, base_unit, conversion_factor
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    uom_data.get('guid'),
                    uom_data.get('name'),
                    uom_data.get('parent'),
                    uom_data.get('base_unit'),
                    self.safe_decimal(uom_data.get('conversion_factor'))
                ))
                count += 1
            except Exception as e:
                print(f"⚠️  Error inserting UOM {uom_data.get('guid')}: {e}")

        print(f"   Units of measure inserted: {count}")

    def _insert_stock_categories(self, cursor, categories: List[Dict[str, Any]]):
        """Insert stock categories with parent-child relationships"""
        print("📥 Inserting stock categories...")
        count = 0

        for cat_data in categories:
            try:
                # Lookup parent_id by name if parent exists
                parent_id = None
                parent_name = cat_data.get('parent')
                if parent_name:
                    cursor.execute("SELECT id FROM stock_categories WHERE name = ?", (parent_name,))
                    result = cursor.fetchone()
                    if result:
                        parent_id = result[0]

                cursor.execute("""
                    INSERT OR REPLACE INTO stock_categories (
                        guid, name, parent_id, alias, description
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    cat_data.get('guid'),
                    cat_data.get('name'),
                    parent_id,  # Store parent_id instead of parent name
                    cat_data.get('alias'),
                    cat_data.get('description')
                ))
                count += 1
            except Exception as e:
                print(f"⚠️  Error inserting stock category {cat_data.get('guid')}: {e}")

        print(f"   Stock categories inserted: {count}")

    def _insert_stock_groups(self, cursor, groups: List[Dict[str, Any]]):
        """Insert stock groups with parent-child relationships"""
        print("📥 Inserting stock groups...")
        count = 0

        for group_data in groups:
            try:
                # Lookup parent_id by name if parent exists
                parent_id = None
                parent_name = group_data.get('parent')
                if parent_name:
                    cursor.execute("SELECT id FROM stock_groups WHERE name = ?", (parent_name,))
                    result = cursor.fetchone()
                    if result:
                        parent_id = result[0]

                cursor.execute("""
                    INSERT OR REPLACE INTO stock_groups (
                        guid, name, parent_id, alias, description
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    group_data.get('guid'),
                    group_data.get('name'),
                    parent_id,  # Store parent_id instead of parent name
                    group_data.get('alias'),
                    group_data.get('description')
                ))
                count += 1
            except Exception as e:
                print(f"⚠️  Error inserting stock group {group_data.get('guid')}: {e}")

        print(f"   Stock groups inserted: {count}")

    def _insert_cost_categories(self, cursor, categories: List[Dict[str, Any]]):
        """Insert cost categories with parent-child relationships"""
        print("📥 Inserting cost categories...")
        count = 0

        for cat_data in categories:
            try:
                # Lookup parent_id by name if parent exists
                parent_id = None
                parent_name = cat_data.get('parent')
                if parent_name:
                    cursor.execute("SELECT id FROM cost_categories WHERE name = ?", (parent_name,))
                    result = cursor.fetchone()
                    if result:
                        parent_id = result[0]

                cursor.execute("""
                    INSERT OR REPLACE INTO cost_categories (
                        guid, name, parent_id, alias, description
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    cat_data.get('guid'),
                    cat_data.get('name'),
                    parent_id,  # Store parent_id instead of parent name
                    cat_data.get('alias'),
                    cat_data.get('description')
                ))
                count += 1
            except Exception as e:
                print(f"⚠️  Error inserting cost category {cat_data.get('guid')}: {e}")

        print(f"   Cost categories inserted: {count}")

    def _insert_cost_centres(self, cursor, centres: List[Dict[str, Any]]):
        """Insert cost centres with parent-child relationships"""
        print("📥 Inserting cost centres...")
        count = 0

        for centre_data in centres:
            try:
                # Lookup parent_id by name if parent exists
                parent_id = None
                parent_name = centre_data.get('parent')
                if parent_name:
                    cursor.execute("SELECT id FROM cost_centres WHERE name = ?", (parent_name,))
                    result = cursor.fetchone()
                    if result:
                        parent_id = result[0]

                cursor.execute("""
                    INSERT OR REPLACE INTO cost_centres (
                        guid, name, parent_id, category_id
                    ) VALUES (?, ?, ?, ?)
                """, (
                    centre_data.get('guid'),
                    centre_data.get('name'),
                    parent_id,  # Store parent_id instead of parent name
                    centre_data.get('category')  # This will need to be looked up too
                ))
                count += 1
            except Exception as e:
                print(f"⚠️  Error inserting cost centre {centre_data.get('guid')}: {e}")

        print(f"   Cost centres inserted: {count}")

    def _insert_attendance_types(self, cursor, types: List[Dict[str, Any]]):
        """Insert attendance types with parent-child relationships"""
        print("📥 Inserting attendance types...")
        count = 0

        for type_data in types:
            try:
                # Lookup parent_id by name if parent exists
                parent_id = None
                parent_name = type_data.get('parent')
                if parent_name:
                    cursor.execute("SELECT id FROM attendance_types WHERE name = ?", (parent_name,))
                    result = cursor.fetchone()
                    if result:
                        parent_id = result[0]

                cursor.execute("""
                    INSERT OR REPLACE INTO attendance_types (
                        guid, name, parent_id, alias, description, attendance_type, time_value, type_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    type_data.get('guid'),
                    type_data.get('name'),
                    parent_id,  # Store parent_id instead of parent name
                    type_data.get('alias'),
                    type_data.get('description'),
                    type_data.get('attendance_type'),
                    self.safe_decimal(type_data.get('time_value')),
                    self.safe_decimal(type_data.get('type_value'))
                ))
                count += 1
            except Exception as e:
                print(f"⚠️  Error inserting attendance type {type_data.get('guid')}: {e}")

        print(f"   Attendance types inserted: {count}")

    def _insert_ledgers(self, cursor, ledgers: List[Dict[str, Any]]):
        """Insert ledgers with group relationships"""
        print("📥 Inserting ledgers...")
        count = 0

        for ledger_data in ledgers:
            try:
                # Lookup parent_id by name
                parent_id = None
                parent_name = ledger_data.get('parent')
                if parent_name:
                    cursor.execute("SELECT id FROM groups WHERE name = ?", (parent_name,))
                    result = cursor.fetchone()
                    if result:
                        parent_id = result[0]

                cursor.execute("""
                    INSERT OR REPLACE INTO ledgers (
                        guid, name, parent_id, alias, description, notes, is_revenue, is_deemedpositive,
                        opening_balance, closing_balance, mailing_name, mailing_address, mailing_state,
                        mailing_country, mailing_pincode, email, it_pan, gstn, gst_registration_type,
                        gst_supply_type, gst_duty_head, tax_rate, bank_account_holder, bank_account_number,
                        bank_ifsc, bank_swift, bank_name, bank_branch, bill_credit_period
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ledger_data.get('guid'),
                    ledger_data.get('name'),
                    parent_id,  # Store parent_id instead of parent name
                    ledger_data.get('alias'),
                    ledger_data.get('description'),
                    ledger_data.get('notes'),
                    self.safe_boolean(ledger_data.get('is_revenue')),
                    self.safe_boolean(ledger_data.get('is_deemedpositive')),
                    self.safe_decimal(ledger_data.get('opening_balance')),
                    self.safe_decimal(ledger_data.get('closing_balance')),
                    ledger_data.get('mailing_name'),
                    ledger_data.get('mailing_address'),
                    ledger_data.get('mailing_state'),
                    ledger_data.get('mailing_country'),
                    ledger_data.get('mailing_pincode'),
                    ledger_data.get('email'),
                    ledger_data.get('it_pan'),
                    ledger_data.get('gstn'),
                    ledger_data.get('gst_registration_type'),
                    ledger_data.get('gst_supply_type'),
                    ledger_data.get('gst_duty_head'),
                    self.safe_decimal(ledger_data.get('tax_rate')),
                    ledger_data.get('bank_account_holder'),
                    ledger_data.get('bank_account_number'),
                    ledger_data.get('bank_ifsc'),
                    ledger_data.get('bank_swift'),
                    ledger_data.get('bank_name'),
                    ledger_data.get('bank_branch'),
                    self.safe_decimal(ledger_data.get('bill_credit_period'))
                ))
                count += 1
            except Exception as e:
                print(f"⚠️  Error inserting ledger {ledger_data.get('guid')}: {e}")

        print(f"   Ledgers inserted: {count}")

    def _insert_godowns(self, cursor, godowns: List[Dict[str, Any]]):
        """Insert godowns with parent-child relationships"""
        print("📥 Inserting godowns...")
        count = 0

        for godown_data in godowns:
            try:
                # Lookup parent_id by name if parent exists
                parent_id = None
                parent_name = godown_data.get('parent')
                if parent_name:
                    cursor.execute("SELECT id FROM godowns WHERE name = ?", (parent_name,))
                    result = cursor.fetchone()
                    if result:
                        parent_id = result[0]

                cursor.execute("""
                    INSERT OR REPLACE INTO godowns (
                        guid, name, parent_id, address
                    ) VALUES (?, ?, ?, ?)
                """, (
                    godown_data.get('guid'),
                    godown_data.get('name'),
                    parent_id,  # Store parent_id instead of parent name
                    godown_data.get('address')
                ))
                count += 1
            except Exception as e:
                print(f"⚠️  Error inserting godown {godown_data.get('guid')}: {e}")

        print(f"   Godowns inserted: {count}")

    def _insert_stock_items(self, cursor, items: List[Dict[str, Any]]):
        """Insert stock items with relationships to groups, categories, UOM"""
        print("📥 Inserting stock items...")
        count = 0

        for item_data in items:
            try:
                # Lookup parent_id by name
                parent_id = None
                parent_name = item_data.get('parent')
                if parent_name:
                    cursor.execute("SELECT id FROM stock_groups WHERE name = ?", (parent_name,))
                    result = cursor.fetchone()
                    if result:
                        parent_id = result[0]

                # Lookup category_id by name
                category_id = None
                category_name = item_data.get('category')
                if category_name:
                    cursor.execute("SELECT id FROM stock_categories WHERE name = ?", (category_name,))
                    result = cursor.fetchone()
                    if result:
                        category_id = result[0]

                # Lookup uom_id by name
                uom_id = None
                uom_name = item_data.get('uom')
                if uom_name:
                    cursor.execute("SELECT id FROM units_of_measure WHERE name = ?", (uom_name,))
                    result = cursor.fetchone()
                    if result:
                        uom_id = result[0]

                # Lookup alternate_uom_id by name
                alt_uom_id = None
                alt_uom_name = item_data.get('alternate_uom')
                if alt_uom_name:
                    cursor.execute("SELECT id FROM units_of_measure WHERE name = ?", (alt_uom_name,))
                    result = cursor.fetchone()
                    if result:
                        alt_uom_id = result[0]

                cursor.execute("""
                    INSERT OR REPLACE INTO stock_items (
                        guid, name, parent_id, category_id, alias, description, notes, part_number,
                        uom_id, alternate_uom_id, conversion, opening_balance, opening_rate, opening_value,
                        closing_balance, closing_rate, closing_value, costing_method, gst_type_of_supply,
                        gst_hsn_code, gst_hsn_description, gst_rate, gst_taxability
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item_data.get('guid'),
                    item_data.get('name'),
                    parent_id,  # Store parent_id instead of parent name
                    category_id,  # Store category_id instead of category name
                    item_data.get('alias'),
                    item_data.get('description'),
                    item_data.get('notes'),
                    item_data.get('part_number'),
                    uom_id,  # Store uom_id instead of uom name
                    alt_uom_id,  # Store alternate_uom_id instead of alternate_uom name
                    self.safe_decimal(item_data.get('conversion')),
                    self.safe_decimal(item_data.get('opening_balance')),
                    self.safe_decimal(item_data.get('opening_rate')),
                    self.safe_decimal(item_data.get('opening_value')),
                    self.safe_decimal(item_data.get('closing_balance')),
                    self.safe_decimal(item_data.get('closing_rate')),
                    self.safe_decimal(item_data.get('closing_value')),
                    item_data.get('costing_method'),
                    item_data.get('gst_type_of_supply'),
                    item_data.get('gst_hsn_code'),
                    item_data.get('gst_hsn_description'),
                    self.safe_decimal(item_data.get('gst_rate')),
                    item_data.get('gst_taxability')
                ))
                count += 1
            except Exception as e:
                print(f"⚠️  Error inserting stock item {item_data.get('guid')}: {e}")

        print(f"   Stock items inserted: {count}")

    def _insert_employees(self, cursor, employees: List[Dict[str, Any]]):
        """Insert employees with cost centre relationships"""
        print("📥 Inserting employees...")
        count = 0

        for emp_data in employees:
            try:
                # Lookup parent_id by name
                parent_id = None
                parent_name = emp_data.get('parent')
                if parent_name:
                    cursor.execute("SELECT id FROM cost_centres WHERE name = ?", (parent_name,))
                    result = cursor.fetchone()
                    if result:
                        parent_id = result[0]

                cursor.execute("""
                    INSERT OR REPLACE INTO employees (
                        guid, name, parent_id, alias, description, notes, category, employee_id,
                        joining_date, leaving_date, designation, department, email, phone, address
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    emp_data.get('guid'),
                    emp_data.get('name'),
                    parent_id,  # Store parent_id instead of parent name
                    emp_data.get('alias'),
                    emp_data.get('description'),
                    emp_data.get('notes'),
                    emp_data.get('category'),
                    emp_data.get('employee_id'),
                    self.safe_date(emp_data.get('joining_date')),
                    self.safe_date(emp_data.get('leaving_date')),
                    emp_data.get('designation'),
                    emp_data.get('department'),
                    emp_data.get('email'),
                    emp_data.get('phone'),
                    emp_data.get('address')
                ))
                count += 1
            except Exception as e:
                print(f"⚠️  Error inserting employee {emp_data.get('guid')}: {e}")

        print(f"   Employees inserted: {count}")

    def _insert_payheads(self, cursor, payheads: List[Dict[str, Any]]):
        """Insert payheads with group relationships"""
        print("📥 Inserting payheads...")
        count = 0

        for ph_data in payheads:
            try:
                # Lookup parent_id by name
                parent_id = None
                parent_name = ph_data.get('parent')
                if parent_name:
                    cursor.execute("SELECT id FROM groups WHERE name = ?", (parent_name,))
                    result = cursor.fetchone()
                    if result:
                        parent_id = result[0]

                cursor.execute("""
                    INSERT OR REPLACE INTO payheads (
                        guid, name, parent_id, alias, description, notes, payhead_type,
                        calculation_type, calculation_period, calculation_basis
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ph_data.get('guid'),
                    ph_data.get('name'),
                    parent_id,  # Store parent_id instead of parent name
                    ph_data.get('alias'),
                    ph_data.get('description'),
                    ph_data.get('notes'),
                    ph_data.get('payhead_type'),
                    ph_data.get('calculation_type'),
                    ph_data.get('calculation_period'),
                    ph_data.get('calculation_basis')
                ))
                count += 1
            except Exception as e:
                print(f"⚠️  Error inserting payhead {ph_data.get('guid')}: {e}")

        print(f"   Payheads inserted: {count}")
    
    def parse_xml_data(self, xml_file_path):
        """Parse XML data and organize into structured format"""
        print(f"📖 Parsing XML file: {xml_file_path}")
        
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Organize data by type
            vouchers = defaultdict(dict)
            ledger_entries = defaultdict(dict)
            inventory_entries = defaultdict(dict)
            employee_entries = defaultdict(dict)
            payhead_allocations = defaultdict(dict)
            attendance_entries = defaultdict(dict)
            
            current_voucher = None
            current_ledger = None
            current_inventory = None
            current_employee = None
            current_payhead = None
            current_attendance = None
            
            for elem in root:
                tag = elem.tag
                value = elem.text if elem.text else None
                
                if tag.startswith('VOUCHER_'):
                    if tag == 'VOUCHER_ID':
                        current_voucher = value
                    if current_voucher:
                        vouchers[current_voucher][tag] = value
                        
                elif tag.startswith('TRN_LEDGERENTRIES_'):
                    if tag == 'TRN_LEDGERENTRIES_ID':
                        current_ledger = value
                    if current_ledger:
                        ledger_entries[current_ledger][tag] = value
                        
                elif tag.startswith('TRN_INVENTORYENTRIES_'):
                    if tag == 'TRN_INVENTORYENTRIES_ID':
                        current_inventory = value
                    if current_inventory:
                        inventory_entries[current_inventory][tag] = value
                        
                elif tag.startswith('TRN_EMPLOYEE_'):
                    if tag == 'TRN_EMPLOYEE_GUID':
                        current_employee = value
                    if current_employee:
                        employee_entries[current_employee][tag] = value
                        
                elif tag.startswith('TRN_PAYHEAD_'):
                    if tag == 'TRN_PAYHEAD_GUID':
                        current_payhead = value
                    if current_payhead:
                        payhead_allocations[current_payhead][tag] = value
                        
                elif tag.startswith('TRN_ATTENDANCE_'):
                    if tag == 'TRN_ATTENDANCE_GUID':
                        current_attendance = value
                    if current_attendance:
                        attendance_entries[current_attendance][tag] = value
            
            print(f"📊 Parsed data:")
            print(f"   Vouchers: {len(vouchers)}")
            print(f"   Ledger entries: {len(ledger_entries)}")
            print(f"   Inventory entries: {len(inventory_entries)}")
            print(f"   Employee entries: {len(employee_entries)}")
            print(f"   Payhead allocations: {len(payhead_allocations)}")
            print(f"   Attendance entries: {len(attendance_entries)}")
            
            return vouchers, ledger_entries, inventory_entries, employee_entries, payhead_allocations, attendance_entries
            
        except Exception as e:
            print(f"❌ XML parsing failed: {e}")
            return None, None, None, None, None, None
    
    def safe_decimal(self, value):
        """Safely convert value to float for SQLite"""
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
        if isinstance(value, str):
            return value.lower() in ['yes', 'true', '1', 'y']
        return bool(value)
    
    def populate_database(self, xml_file_path):
        """Populate database with XML data"""
        if not self.connect():
            return False
        
        try:
            # Parse XML data
            vouchers, ledger_entries, inventory_entries, employee_entries, payhead_allocations, attendance_entries = self.parse_xml_data(xml_file_path)
            if not vouchers:
                print("❌ No data to populate")
                return False
            
            print("🔄 Starting database population...")
            
            # Insert vouchers
            voucher_count = 0
            for voucher_guid, voucher_data in vouchers.items():
                try:
                    cursor = self.conn.cursor()
                    
                    # Lookup voucher_type_id by name
                    voucher_type_id = None
                    voucher_type_name = voucher_data.get('VOUCHER_VOUCHER_TYPE')
                    if voucher_type_name:
                        cursor.execute("SELECT id FROM voucher_types WHERE name = ?", (voucher_type_name,))
                        result = cursor.fetchone()
                        if result:
                            voucher_type_id = result[0]
                    
                    # Lookup party_ledger_id by name
                    party_ledger_id = None
                    party_name = voucher_data.get('VOUCHER_PARTY_NAME')
                    if party_name:
                        cursor.execute("SELECT id FROM ledgers WHERE name = ?", (party_name,))
                        result = cursor.fetchone()
                        if result:
                            party_ledger_id = result[0]
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO vouchers (
                            guid, date, voucher_type, voucher_number, reference_number, 
                            reference_date, narration, party_name, place_of_supply,
                            is_invoice, is_accounting_voucher, is_inventory_voucher, is_order_voucher,
                            voucher_type_id, party_ledger_id, company_id, division_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        config.get_company_id(),
                        config.get_division_id()
                    ))
                    voucher_count += 1
                except Exception as e:
                    print(f"⚠️  Error inserting voucher {voucher_guid}: {e}")
            
            # Insert ledger entries
            ledger_count = 0
            for ledger_guid, ledger_data in ledger_entries.items():
                try:
                    # Get voucher_id - ledger GUID should match voucher GUID
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT id FROM vouchers WHERE guid = ?", (ledger_guid,))
                    voucher_result = cursor.fetchone()
                    if not voucher_result:
                        # Try to find voucher by matching the GUID pattern
                        cursor.execute("SELECT id FROM vouchers WHERE guid LIKE ?", (f"{ledger_guid[:8]}%",))
                        voucher_result = cursor.fetchone()
                        if not voucher_result:
                            continue
                    voucher_id = voucher_result[0]
                    
                    # Lookup ledger_id by name
                    ledger_id = None
                    ledger_name = ledger_data.get('TRN_LEDGERENTRIES_LEDGER_NAME')
                    if ledger_name:
                        cursor.execute("SELECT id FROM ledgers WHERE name = ?", (ledger_name,))
                        result = cursor.fetchone()
                        if result:
                            ledger_id = result[0]
                    
                    # Insert ledger entry
                    cursor.execute("""
                        INSERT OR REPLACE INTO ledger_entries (
                            guid, voucher_id, ledger_id, ledger_name, amount, amount_forex, 
                            currency, is_debit
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ledger_data.get('TRN_LEDGERENTRIES_ID'),
                        voucher_id,
                        ledger_id,
                        ledger_data.get('TRN_LEDGERENTRIES_LEDGER_NAME'),
                        self.safe_decimal(ledger_data.get('TRN_LEDGERENTRIES_AMOUNT')),
                        None,  # amount_forex not available
                        None,  # currency not available
                        self.safe_boolean(ledger_data.get('TRN_LEDGERENTRIES_IS_DEBIT'))
                    ))
                    ledger_count += 1
                except Exception as e:
                    print(f"⚠️  Error inserting ledger entry {ledger_guid}: {e}")
            
            # Insert inventory entries
            inventory_count = 0
            for inventory_guid, inventory_data in inventory_entries.items():
                try:
                    # Get voucher_id - inventory GUID should match voucher GUID
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT id FROM vouchers WHERE guid = ?", (inventory_guid,))
                    voucher_result = cursor.fetchone()
                    if not voucher_result:
                        # Try to find voucher by matching the GUID pattern
                        cursor.execute("SELECT id FROM vouchers WHERE guid LIKE ?", (f"{inventory_guid[:8]}%",))
                        voucher_result = cursor.fetchone()
                        if not voucher_result:
                            continue
                    voucher_id = voucher_result[0]
                    
                    # Lookup stock_item_id by name
                    stock_item_id = None
                    stock_item_name = inventory_data.get('TRN_INVENTORYENTRIES_STOCKITEM_NAME')
                    if stock_item_name:
                        cursor.execute("SELECT id FROM stock_items WHERE name = ?", (stock_item_name,))
                        result = cursor.fetchone()
                        if result:
                            stock_item_id = result[0]
                    
                    # Lookup godown_id by name (if godown_name is available)
                    godown_id = None
                    godown_name = inventory_data.get('TRN_INVENTORYENTRIES_GODOWN_NAME')
                    if godown_name:
                        cursor.execute("SELECT id FROM godowns WHERE name = ?", (godown_name,))
                        result = cursor.fetchone()
                        if result:
                            godown_id = result[0]
                    
                    # Insert inventory entry
                    cursor.execute("""
                        INSERT OR REPLACE INTO inventory_entries (
                            guid, voucher_id, stock_item_id, stock_item_name, quantity, rate, amount,
                            additional_amount, discount_amount, godown_id, godown_name, tracking_number,
                            order_number, order_duedate
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        inventory_data.get('TRN_INVENTORYENTRIES_ID'),
                        voucher_id,
                        stock_item_id,
                        inventory_data.get('TRN_INVENTORYENTRIES_STOCKITEM_NAME'),
                        self.safe_decimal(inventory_data.get('TRN_INVENTORYENTRIES_QUANTITY')),
                        self.safe_decimal(inventory_data.get('TRN_INVENTORYENTRIES_RATE')),
                        self.safe_decimal(inventory_data.get('TRN_INVENTORYENTRIES_AMOUNT')),
                        None,  # additional_amount not available
                        None,  # discount_amount not available
                        godown_id,
                        godown_name,
                        None,  # tracking_number not available
                        None,  # order_number not available
                        None   # order_duedate not available
                    ))
                    inventory_count += 1
                except Exception as e:
                    print(f"⚠️  Error inserting inventory entry {inventory_guid}: {e}")

            # Insert employee entries
            employee_count = 0
            for employee_guid, employee_data in employee_entries.items():
                try:
                    # Get voucher_id - employee GUID should match voucher GUID
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT id FROM vouchers WHERE guid = ?", (employee_guid,))
                    voucher_result = cursor.fetchone()
                    if not voucher_result:
                        # Try to find voucher by matching the GUID pattern
                        cursor.execute("SELECT id FROM vouchers WHERE guid LIKE ?", (f"{employee_guid[:8]}%",))
                        voucher_result = cursor.fetchone()
                        if not voucher_result:
                            continue
                    voucher_id = voucher_result[0]

                    # Lookup employee_id by name
                    employee_id = None
                    employee_name = employee_data.get('TRN_EMPLOYEE_NAME')
                    if employee_name:
                        cursor.execute("SELECT id FROM employees WHERE name = ?", (employee_name,))
                        result = cursor.fetchone()
                        if result:
                            employee_id = result[0]

                    # Insert employee entry
                    cursor.execute("""
                        INSERT OR REPLACE INTO employee_entries (
                            guid, voucher_id, employee_id, category, employee_name, amount, employee_sort_order
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        employee_data.get('TRN_EMPLOYEE_GUID'),
                        voucher_id,
                        employee_id,
                        employee_data.get('TRN_EMPLOYEE_CATEGORY'),
                        employee_data.get('TRN_EMPLOYEE_NAME'),
                        self.safe_decimal(employee_data.get('TRN_EMPLOYEE_AMOUNT')),
                        self.safe_decimal(employee_data.get('TRN_EMPLOYEE_SORT_ORDER'))
                    ))
                    employee_count += 1
                except Exception as e:
                    print(f"⚠️  Error inserting employee entry {employee_guid}: {e}")

            # Insert payhead allocations
            payhead_count = 0
            for payhead_guid, payhead_data in payhead_allocations.items():
                try:
                    # Get voucher_id - payhead GUID should match voucher GUID
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT id FROM vouchers WHERE guid = ?", (payhead_guid,))
                    voucher_result = cursor.fetchone()
                    if not voucher_result:
                        # Try to find voucher by matching the GUID pattern
                        cursor.execute("SELECT id FROM vouchers WHERE guid LIKE ?", (f"{payhead_guid[:8]}%",))
                        voucher_result = cursor.fetchone()
                        if not voucher_result:
                            continue
                    voucher_id = voucher_result[0]

                    # Lookup employee_id by name
                    employee_id = None
                    employee_name = payhead_data.get('TRN_PAYHEAD_EMPLOYEE_NAME')
                    if employee_name:
                        cursor.execute("SELECT id FROM employees WHERE name = ?", (employee_name,))
                        result = cursor.fetchone()
                        if result:
                            employee_id = result[0]

                    # Lookup payhead_id by name
                    payhead_id = None
                    payhead_name = payhead_data.get('TRN_PAYHEAD_NAME')
                    if payhead_name:
                        cursor.execute("SELECT id FROM payheads WHERE name = ?", (payhead_name,))
                        result = cursor.fetchone()
                        if result:
                            payhead_id = result[0]

                    # Insert payhead allocation
                    cursor.execute("""
                        INSERT OR REPLACE INTO payhead_allocations (
                            guid, voucher_id, employee_id, payhead_id, category, employee_name, employee_sort_order,
                            payhead_name, payhead_sort_order, amount
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        payhead_data.get('TRN_PAYHEAD_GUID'),
                        voucher_id,
                        employee_id,
                        payhead_id,
                        payhead_data.get('TRN_PAYHEAD_CATEGORY'),
                        payhead_data.get('TRN_PAYHEAD_EMPLOYEE_NAME'),
                        self.safe_decimal(payhead_data.get('TRN_PAYHEAD_EMPLOYEE_SORT_ORDER')),
                        payhead_data.get('TRN_PAYHEAD_NAME'),
                        self.safe_decimal(payhead_data.get('TRN_PAYHEAD_SORT_ORDER')),
                        self.safe_decimal(payhead_data.get('TRN_PAYHEAD_AMOUNT'))
                    ))
                    payhead_count += 1
                except Exception as e:
                    print(f"⚠️  Error inserting payhead allocation {payhead_guid}: {e}")

            # Insert attendance entries
            attendance_count = 0
            for attendance_guid, attendance_data in attendance_entries.items():
                try:
                    # Get voucher_id - attendance GUID should match voucher GUID
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT id FROM vouchers WHERE guid = ?", (attendance_guid,))
                    voucher_result = cursor.fetchone()
                    if not voucher_result:
                        # Try to find voucher by matching the GUID pattern
                        cursor.execute("SELECT id FROM vouchers WHERE guid LIKE ?", (f"{attendance_guid[:8]}%",))
                        voucher_result = cursor.fetchone()
                        if not voucher_result:
                            continue
                    voucher_id = voucher_result[0]

                    # Lookup employee_id by name
                    employee_id = None
                    employee_name = attendance_data.get('TRN_ATTENDANCE_EMPLOYEE_NAME')
                    if employee_name:
                        cursor.execute("SELECT id FROM employees WHERE name = ?", (employee_name,))
                        result = cursor.fetchone()
                        if result:
                            employee_id = result[0]

                    # Lookup attendance_type_id by name
                    attendance_type_id = None
                    attendance_type = attendance_data.get('TRN_ATTENDANCE_TYPE')
                    if attendance_type:
                        cursor.execute("SELECT id FROM attendance_types WHERE name = ?", (attendance_type,))
                        result = cursor.fetchone()
                        if result:
                            attendance_type_id = result[0]

                    # Insert attendance entry
                    cursor.execute("""
                        INSERT OR REPLACE INTO attendance_entries (
                            guid, voucher_id, employee_id, attendance_type_id, employee_name, attendance_type, time_value, type_value
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        attendance_data.get('TRN_ATTENDANCE_GUID'),
                        voucher_id,
                        employee_id,
                        attendance_type_id,
                        attendance_data.get('TRN_ATTENDANCE_EMPLOYEE_NAME'),
                        attendance_data.get('TRN_ATTENDANCE_TYPE'),
                        self.safe_decimal(attendance_data.get('TRN_ATTENDANCE_TIME_VALUE')),
                        self.safe_decimal(attendance_data.get('TRN_ATTENDANCE_TYPE_VALUE'))
                    ))
                    attendance_count += 1
                except Exception as e:
                    print(f"⚠️  Error inserting attendance entry {attendance_guid}: {e}")

            self.conn.commit()
            print(f"✅ Database population completed!")
            print(f"   Vouchers inserted: {voucher_count}")
            print(f"   Ledger entries inserted: {ledger_count}")
            print(f"   Inventory entries inserted: {inventory_count}")
            print(f"   Employee entries inserted: {employee_count}")
            print(f"   Payhead allocations inserted: {payhead_count}")
            print(f"   Attendance entries inserted: {attendance_count}")

            return True
            
        except Exception as e:
            print(f"❌ Database population failed: {e}")
            self.conn.rollback()
            return False
        finally:
            self.disconnect()
    
    def show_statistics(self):
        """Show database statistics"""
        if not self.connect():
            return False
        
        try:
            cursor = self.conn.cursor()
            
            print("📊 DATABASE STATISTICS")
            print("=" * 50)
            
            # Count records in each table
            tables = [
                'vouchers', 'ledger_entries', 'inventory_entries',
                'groups', 'voucher_types', 'ledgers', 'units_of_measure', 
                'stock_categories', 'stock_groups', 'stock_items', 'godowns', 
                'cost_categories', 'cost_centres', 'employees', 'payheads', 'attendance_types',
                'employee_entries', 'payhead_allocations', 'attendance_entries',
                'cost_centre_allocations_trn', 'cost_category_centre_allocations',
                'cost_inventory_category_centre_allocations', 'inventory_accounting_entries',
                'closing_stock_ledger', 'cost_centre_allocations', 'bill_allocations',
                'bank_allocations', 'batch_allocations'
            ]
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"{table:20s}: {count:8d} records")
                except:
                    print(f"{table:20s}: Table not found")
            
            print()
            
            # Show sample data
            print("📋 SAMPLE VOUCHER DATA:")
            cursor.execute("""
                SELECT guid, date, voucher_type, voucher_number, narration, party_name
                FROM vouchers 
                LIMIT 5
            """)
            for row in cursor.fetchall():
                print(f"  {row[0][:8]}... | {row[1]} | {row[2]} | {row[3]} | {row[4][:30]}...")
            
            print()
            print("📋 SAMPLE LEDGER ENTRY DATA:")
            cursor.execute("""
                SELECT le.guid, v.voucher_number, le.ledger_name, le.amount
                FROM ledger_entries le
                JOIN vouchers v ON le.voucher_id = v.id
                LIMIT 5
            """)
            for row in cursor.fetchall():
                print(f"  {row[0][:8]}... | {row[1]} | {row[2][:30]}... | {row[3]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Statistics query failed: {e}")
            return False
        finally:
            self.disconnect()

def main():
    parser = argparse.ArgumentParser(description='Tally Database Manager')
    parser.add_argument('--create-db', action='store_true', help='Create database schema')
    parser.add_argument('--populate-db', action='store_true', help='Populate database with XML data')
    parser.add_argument('--xml-file', type=str, help='XML file path for population')
    parser.add_argument('--show-stats', action='store_true', help='Show database statistics')
    parser.add_argument('--db-path', type=str, default='tally_data.db', help='Database file path')
    
    args = parser.parse_args()
    
    if not any([args.create_db, args.populate_db, args.show_stats]):
        parser.print_help()
        return
    
    db_manager = TallyDatabaseManager(args.db_path)
    
    if args.create_db:
        print("🏗️  Creating database schema...")
        if db_manager.create_database():
            print("✅ Database creation completed successfully!")
        else:
            print("❌ Database creation failed!")
            sys.exit(1)
    
    if args.populate_db:
        if not args.xml_file:
            print("❌ XML file path required for population")
            sys.exit(1)
        if not os.path.exists(args.xml_file):
            print(f"❌ XML file not found: {args.xml_file}")
            sys.exit(1)
        
        print("📥 Populating database with XML data...")
        if db_manager.populate_database(args.xml_file):
            print("✅ Database population completed successfully!")
        else:
            print("❌ Database population failed!")
            sys.exit(1)
    
    if args.show_stats:
        db_manager.show_statistics()

if __name__ == "__main__":
    main()
