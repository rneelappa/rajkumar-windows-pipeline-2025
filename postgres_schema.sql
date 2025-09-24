-- =====================================================
-- TALLY POSTGRESQL SCHEMA
-- Comprehensive PostgreSQL database for Tally data
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- MASTER DATA TABLES
-- =====================================================

-- Groups Master Table
CREATE TABLE IF NOT EXISTS groups (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    parent_id INTEGER,
    primary_group VARCHAR,
    is_revenue BOOLEAN,
    is_deemedpositive BOOLEAN,
    is_reserved BOOLEAN,
    affects_gross_profit BOOLEAN,
    sort_position INTEGER,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES groups(id)
);

-- Voucher Types Master Table
CREATE TABLE IF NOT EXISTS voucher_types (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    parent_id INTEGER,
    numbering_method VARCHAR,
    is_deemedpositive BOOLEAN,
    affects_stock BOOLEAN,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES voucher_types(id)
);

-- Ledgers Master Table
CREATE TABLE IF NOT EXISTS ledgers (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    parent_id INTEGER,
    alias VARCHAR,
    description VARCHAR,
    notes VARCHAR,
    is_revenue BOOLEAN,
    is_deemedpositive BOOLEAN,
    opening_balance NUMERIC(15,2),
    closing_balance NUMERIC(15,2),
    mailing_name VARCHAR,
    mailing_address VARCHAR,
    mailing_state VARCHAR,
    mailing_country VARCHAR,
    mailing_pincode VARCHAR,
    email VARCHAR,
    it_pan VARCHAR,
    gstn VARCHAR,
    gst_registration_type VARCHAR,
    gst_supply_type VARCHAR,
    gst_duty_head VARCHAR,
    tax_rate NUMERIC(5,2),
    bank_account_holder VARCHAR,
    bank_account_number VARCHAR,
    bank_ifsc VARCHAR,
    bank_swift VARCHAR,
    bank_name VARCHAR,
    bank_branch VARCHAR,
    bill_credit_period INTEGER,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES groups(id)
);

-- Units of Measure Master Table
CREATE TABLE IF NOT EXISTS units_of_measure (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    parent VARCHAR,
    base_unit VARCHAR,
    conversion_factor NUMERIC(10,4),
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stock Categories Master Table
CREATE TABLE IF NOT EXISTS stock_categories (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    parent_id INTEGER,
    alias VARCHAR,
    description VARCHAR,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES stock_categories(id)
);

-- Stock Groups Master Table
CREATE TABLE IF NOT EXISTS stock_groups (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    parent_id INTEGER,
    alias VARCHAR,
    description VARCHAR,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES stock_groups(id)
);

-- Stock Items Master Table
CREATE TABLE IF NOT EXISTS stock_items (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    parent_id INTEGER,
    category_id INTEGER,
    alias VARCHAR,
    description VARCHAR,
    notes VARCHAR,
    part_number VARCHAR,
    uom_id INTEGER,
    alternate_uom_id INTEGER,
    conversion NUMERIC(10,4),
    opening_balance NUMERIC(15,4),
    opening_rate NUMERIC(15,2),
    opening_value NUMERIC(15,2),
    closing_balance NUMERIC(15,4),
    closing_rate NUMERIC(15,2),
    closing_value NUMERIC(15,2),
    costing_method VARCHAR,
    gst_type_of_supply VARCHAR,
    gst_hsn_code VARCHAR,
    gst_hsn_description VARCHAR,
    gst_rate NUMERIC(5,2),
    gst_taxability VARCHAR,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES stock_groups(id),
    FOREIGN KEY (category_id) REFERENCES stock_categories(id),
    FOREIGN KEY (uom_id) REFERENCES units_of_measure(id),
    FOREIGN KEY (alternate_uom_id) REFERENCES units_of_measure(id)
);

-- Godowns Master Table
CREATE TABLE IF NOT EXISTS godowns (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    parent_id INTEGER,
    address VARCHAR,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES godowns(id)
);

-- Cost Categories Master Table
CREATE TABLE IF NOT EXISTS cost_categories (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    parent_id INTEGER,
    alias VARCHAR,
    description VARCHAR,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES cost_categories(id)
);

-- Cost Centres Master Table
CREATE TABLE IF NOT EXISTS cost_centres (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    parent_id INTEGER,
    category_id INTEGER,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES cost_centres(id),
    FOREIGN KEY (category_id) REFERENCES cost_categories(id)
);

-- Employees Master Table
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    parent_id INTEGER,
    alias VARCHAR,
    description VARCHAR,
    notes VARCHAR,
    category VARCHAR,
    employee_id VARCHAR,
    joining_date DATE,
    leaving_date DATE,
    designation VARCHAR,
    department VARCHAR,
    email VARCHAR,
    phone VARCHAR,
    address VARCHAR,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES cost_centres(id)
);

-- Payheads Master Table
CREATE TABLE IF NOT EXISTS payheads (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    parent_id INTEGER,
    alias VARCHAR,
    description VARCHAR,
    notes VARCHAR,
    payhead_type VARCHAR,
    calculation_type VARCHAR,
    calculation_period VARCHAR,
    calculation_basis VARCHAR,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES groups(id)
);

-- Attendance Types Master Table
CREATE TABLE IF NOT EXISTS attendance_types (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    parent_id INTEGER,
    alias VARCHAR,
    description VARCHAR,
    attendance_type VARCHAR,
    time_value NUMERIC(15,2),
    type_value NUMERIC(15,2),
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES attendance_types(id)
);

-- =====================================================
-- TRANSACTION TABLES
-- =====================================================

-- Vouchers Transaction Table
CREATE TABLE IF NOT EXISTS vouchers (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    date DATE,
    voucher_type VARCHAR,
    voucher_number VARCHAR,
    reference_number VARCHAR,
    reference_date DATE,
    narration VARCHAR,
    party_name VARCHAR,
    place_of_supply VARCHAR,
    is_invoice BOOLEAN,
    is_accounting_voucher BOOLEAN,
    is_inventory_voucher BOOLEAN,
    is_order_voucher BOOLEAN,
    voucher_type_id INTEGER,
    party_ledger_id INTEGER,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (voucher_type_id) REFERENCES voucher_types(id),
    FOREIGN KEY (party_ledger_id) REFERENCES ledgers(id)
);

-- Ledger Entries Transaction Table
CREATE TABLE IF NOT EXISTS ledger_entries (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    ledger_id INTEGER,
    ledger_name VARCHAR,
    amount NUMERIC(15,2),
    amount_forex NUMERIC(15,2),
    currency VARCHAR,
    is_debit BOOLEAN,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (ledger_id) REFERENCES ledgers(id)
);

-- Inventory Entries Transaction Table
CREATE TABLE IF NOT EXISTS inventory_entries (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    stock_item_id INTEGER,
    stock_item_name VARCHAR,
    godown_id INTEGER,
    godown_name VARCHAR,
    quantity NUMERIC(15,4),
    rate NUMERIC(15,2),
    amount NUMERIC(15,2),
    amount_forex NUMERIC(15,2),
    currency VARCHAR,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (stock_item_id) REFERENCES stock_items(id),
    FOREIGN KEY (godown_id) REFERENCES godowns(id)
);

-- Employee Entries Transaction Table
CREATE TABLE IF NOT EXISTS employee_entries (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    employee_id INTEGER,
    employee_name VARCHAR,
    category VARCHAR,
    amount NUMERIC(15,2),
    sort_order NUMERIC(10,2),
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

-- Payhead Allocations Transaction Table
CREATE TABLE IF NOT EXISTS payhead_allocations (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    employee_id INTEGER,
    payhead_id INTEGER,
    category VARCHAR,
    employee_name VARCHAR,
    employee_sort_order NUMERIC(10,2),
    payhead_name VARCHAR,
    payhead_sort_order NUMERIC(10,2),
    amount NUMERIC(15,2),
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (payhead_id) REFERENCES payheads(id)
);

-- Attendance Entries Transaction Table
CREATE TABLE IF NOT EXISTS attendance_entries (
    id SERIAL PRIMARY KEY,
    guid VARCHAR UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    employee_id INTEGER,
    attendance_type_id INTEGER,
    employee_name VARCHAR,
    attendance_type VARCHAR,
    time_value NUMERIC(15,2),
    type_value NUMERIC(15,2),
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (attendance_type_id) REFERENCES attendance_types(id)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Create indexes on frequently queried columns
CREATE INDEX IF NOT EXISTS idx_vouchers_date ON vouchers(date);
CREATE INDEX IF NOT EXISTS idx_vouchers_company_division ON vouchers(company_id, division_id);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_voucher_id ON ledger_entries(voucher_id);
CREATE INDEX IF NOT EXISTS idx_inventory_entries_voucher_id ON inventory_entries(voucher_id);
CREATE INDEX IF NOT EXISTS idx_employee_entries_voucher_id ON employee_entries(voucher_id);
CREATE INDEX IF NOT EXISTS idx_payhead_allocations_voucher_id ON payhead_allocations(voucher_id);
CREATE INDEX IF NOT EXISTS idx_attendance_entries_voucher_id ON attendance_entries(voucher_id);

-- Create indexes on GUID columns
CREATE INDEX IF NOT EXISTS idx_groups_guid ON groups(guid);
CREATE INDEX IF NOT EXISTS idx_voucher_types_guid ON voucher_types(guid);
CREATE INDEX IF NOT EXISTS idx_ledgers_guid ON ledgers(guid);
CREATE INDEX IF NOT EXISTS idx_stock_items_guid ON stock_items(guid);
CREATE INDEX IF NOT EXISTS idx_employees_guid ON employees(guid);
CREATE INDEX IF NOT EXISTS idx_payheads_guid ON payheads(guid);
CREATE INDEX IF NOT EXISTS idx_attendance_types_guid ON attendance_types(guid);
