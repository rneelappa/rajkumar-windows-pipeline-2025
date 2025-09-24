-- =====================================================
-- TALLY DATABASE SCHEMA
-- Comprehensive SQLite database for Tally data
-- =====================================================

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- =====================================================
-- MASTER DATA TABLES
-- =====================================================

-- Groups Master Table
CREATE TABLE groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    parent_id INTEGER,
    primary_group TEXT,
    is_revenue BOOLEAN,
    is_deemedpositive BOOLEAN,
    is_reserved BOOLEAN,
    affects_gross_profit BOOLEAN,
    sort_position INTEGER,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES groups(id)
);

-- Voucher Types Master Table
CREATE TABLE voucher_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    parent_id INTEGER,
    numbering_method TEXT,
    is_deemedpositive BOOLEAN,
    affects_stock BOOLEAN,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES voucher_types(id)
);

-- Ledgers Master Table
CREATE TABLE ledgers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    parent_id INTEGER,
    alias TEXT,
    description TEXT,
    notes TEXT,
    is_revenue BOOLEAN,
    is_deemedpositive BOOLEAN,
    opening_balance DECIMAL(15,2),
    closing_balance DECIMAL(15,2),
    mailing_name TEXT,
    mailing_address TEXT,
    mailing_state TEXT,
    mailing_country TEXT,
    mailing_pincode TEXT,
    email TEXT,
    it_pan TEXT,
    gstn TEXT,
    gst_registration_type TEXT,
    gst_supply_type TEXT,
    gst_duty_head TEXT,
    tax_rate DECIMAL(5,2),
    bank_account_holder TEXT,
    bank_account_number TEXT,
    bank_ifsc TEXT,
    bank_swift TEXT,
    bank_name TEXT,
    bank_branch TEXT,
    bill_credit_period INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES groups(id)
);

-- Units of Measure Master Table
CREATE TABLE units_of_measure (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    parent TEXT,
    base_unit TEXT,
    conversion_factor DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stock Categories Master Table
CREATE TABLE stock_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    parent TEXT,
    alias TEXT,
    description TEXT,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stock Groups Master Table
CREATE TABLE stock_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    parent_id INTEGER,
    alias TEXT,
    description TEXT,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES stock_groups(id)
);

-- Stock Items Master Table
CREATE TABLE stock_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    parent_id INTEGER,
    category_id INTEGER,
    alias TEXT,
    description TEXT,
    notes TEXT,
    part_number TEXT,
    uom_id INTEGER,
    alternate_uom_id INTEGER,
    conversion DECIMAL(10,4),
    opening_balance DECIMAL(15,4),
    opening_rate DECIMAL(15,2),
    opening_value DECIMAL(15,2),
    closing_balance DECIMAL(15,4),
    closing_rate DECIMAL(15,2),
    closing_value DECIMAL(15,2),
    costing_method TEXT,
    gst_type_of_supply TEXT,
    gst_hsn_code TEXT,
    gst_hsn_description TEXT,
    gst_rate DECIMAL(5,2),
    gst_taxability TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES stock_groups(id),
    FOREIGN KEY (category_id) REFERENCES stock_categories(id),
    FOREIGN KEY (uom_id) REFERENCES units_of_measure(id),
    FOREIGN KEY (alternate_uom_id) REFERENCES units_of_measure(id)
);

-- Godowns Master Table
CREATE TABLE godowns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    parent TEXT,
    address TEXT,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cost Categories Master Table
CREATE TABLE cost_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    parent TEXT,
    alias TEXT,
    description TEXT,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cost Centres Master Table
CREATE TABLE cost_centres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    parent TEXT,
    category TEXT,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Employees Master Table
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    parent TEXT,
    alias TEXT,
    description TEXT,
    notes TEXT,
    category TEXT,
    employee_id TEXT,
    joining_date DATE,
    leaving_date DATE,
    designation TEXT,
    department TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payheads Master Table
CREATE TABLE payheads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    parent TEXT,
    alias TEXT,
    description TEXT,
    notes TEXT,
    payhead_type TEXT,
    calculation_type TEXT,
    calculation_period TEXT,
    calculation_basis TEXT,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Attendance Types Master Table
CREATE TABLE attendance_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    parent TEXT,
    alias TEXT,
    description TEXT,
    notes TEXT,
    attendance_type TEXT,
    time_value DECIMAL(10,2),
    type_value DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TRANSACTION TABLES
-- =====================================================

-- Vouchers Transaction Table
CREATE TABLE vouchers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    date DATE NOT NULL,
    voucher_type TEXT NOT NULL,
    voucher_number TEXT,
    reference_number TEXT,
    reference_date DATE,
    narration TEXT,
    party_name TEXT,
    place_of_supply TEXT,
    is_invoice BOOLEAN DEFAULT 0,
    is_accounting_voucher BOOLEAN DEFAULT 0,
    is_inventory_voucher BOOLEAN DEFAULT 0,
    is_order_voucher BOOLEAN DEFAULT 0,
    company_id UUID NOT NULL,
    division_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key to voucher_types
    voucher_type_id INTEGER,
    -- Foreign key to ledgers (party)
    party_ledger_id INTEGER,
    FOREIGN KEY (voucher_type_id) REFERENCES voucher_types(id),
    FOREIGN KEY (party_ledger_id) REFERENCES ledgers(id)
);

-- Ledger Entries Transaction Table
CREATE TABLE ledger_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    ledger_id INTEGER,
    ledger_name TEXT,
    amount DECIMAL(15,2),
    amount_forex DECIMAL(15,2),
    currency TEXT,
    is_debit BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (ledger_id) REFERENCES ledgers(id)
);

-- Inventory Entries Transaction Table
CREATE TABLE inventory_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    stock_item_id INTEGER,
    stock_item_name TEXT,
    quantity DECIMAL(15,4),
    rate DECIMAL(15,2),
    amount DECIMAL(15,2),
    additional_amount DECIMAL(15,2),
    discount_amount DECIMAL(15,2),
    godown_id INTEGER,
    godown_name TEXT,
    tracking_number TEXT,
    order_number TEXT,
    order_duedate DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (stock_item_id) REFERENCES stock_items(id),
    FOREIGN KEY (godown_id) REFERENCES godowns(id)
);

-- =====================================================
-- ADDITIONAL TRANSACTION TABLES
-- =====================================================

-- Cost Centre Allocations Transaction Table
CREATE TABLE cost_centre_allocations_trn (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    ledger_entry_id INTEGER,
    cost_centre_id INTEGER,
    amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (ledger_entry_id) REFERENCES ledger_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (cost_centre_id) REFERENCES cost_centres(id)
);

-- Cost Category Centre Allocations Transaction Table
CREATE TABLE cost_category_centre_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    ledger_entry_id INTEGER,
    cost_category_id INTEGER,
    cost_centre_id INTEGER,
    amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (ledger_entry_id) REFERENCES ledger_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (cost_category_id) REFERENCES cost_categories(id),
    FOREIGN KEY (cost_centre_id) REFERENCES cost_centres(id)
);

-- Cost Inventory Category Centre Allocations Transaction Table
CREATE TABLE cost_inventory_category_centre_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    inventory_entry_id INTEGER,
    cost_category_id INTEGER,
    cost_centre_id INTEGER,
    amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (inventory_entry_id) REFERENCES inventory_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (cost_category_id) REFERENCES cost_categories(id),
    FOREIGN KEY (cost_centre_id) REFERENCES cost_centres(id)
);

-- Inventory Accounting Entries Transaction Table
CREATE TABLE inventory_accounting_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    inventory_entry_id INTEGER,
    ledger_entry_id INTEGER,
    amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (inventory_entry_id) REFERENCES inventory_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (ledger_entry_id) REFERENCES ledger_entries(id) ON DELETE CASCADE
);

-- Closing Stock Ledger Transaction Table
CREATE TABLE closing_stock_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    stock_item_id INTEGER,
    quantity DECIMAL(15,4),
    rate DECIMAL(15,2),
    amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (stock_item_id) REFERENCES stock_items(id)
);

-- =====================================================
-- RELATIONSHIP TABLES
-- =====================================================

-- Cost Centre Allocations
CREATE TABLE cost_centre_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ledger_entry_id INTEGER NOT NULL,
    cost_centre_id INTEGER NOT NULL,
    amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (ledger_entry_id) REFERENCES ledger_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (cost_centre_id) REFERENCES cost_centres(id),
    
    -- Unique constraint
    UNIQUE(ledger_entry_id, cost_centre_id)
);

-- Bill Allocations
CREATE TABLE bill_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ledger_entry_id INTEGER NOT NULL,
    bill_name TEXT NOT NULL,
    bill_type TEXT,
    amount DECIMAL(15,2),
    bill_credit_period INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (ledger_entry_id) REFERENCES ledger_entries(id) ON DELETE CASCADE
);

-- Bank Allocations
CREATE TABLE bank_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ledger_entry_id INTEGER NOT NULL,
    transaction_type TEXT,
    instrument_date DATE,
    instrument_number TEXT,
    bank_name TEXT,
    amount DECIMAL(15,2),
    bankers_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (ledger_entry_id) REFERENCES ledger_entries(id) ON DELETE CASCADE
);

-- Batch Allocations
CREATE TABLE batch_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_entry_id INTEGER NOT NULL,
    batch_name TEXT NOT NULL,
    quantity DECIMAL(15,4),
    amount DECIMAL(15,2),
    godown_id INTEGER,
    destination_godown_id INTEGER,
    tracking_number TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (inventory_entry_id) REFERENCES inventory_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (godown_id) REFERENCES godowns(id),
    FOREIGN KEY (destination_godown_id) REFERENCES godowns(id)
);

-- Employee Entries Transaction Table
CREATE TABLE employee_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    employee_id INTEGER,
    category TEXT,
    employee_name TEXT,
    amount DECIMAL(15,2),
    employee_sort_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

-- Payhead Allocations Transaction Table
CREATE TABLE payhead_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    employee_id INTEGER,
    payhead_id INTEGER,
    category TEXT,
    employee_name TEXT,
    employee_sort_order INTEGER,
    payhead_name TEXT,
    payhead_sort_order INTEGER,
    amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (payhead_id) REFERENCES payheads(id)
);

-- Attendance Entries Transaction Table
CREATE TABLE attendance_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    employee_id INTEGER,
    attendance_type_id INTEGER,
    employee_name TEXT,
    attendance_type TEXT,
    time_value DECIMAL(10,2),
    type_value DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (attendance_type_id) REFERENCES attendance_types(id)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Vouchers indexes
CREATE INDEX idx_vouchers_guid ON vouchers(guid);
CREATE INDEX idx_vouchers_date ON vouchers(date);
CREATE INDEX idx_vouchers_type ON vouchers(voucher_type);
CREATE INDEX idx_vouchers_number ON vouchers(voucher_number);

-- Ledger entries indexes
CREATE INDEX idx_ledger_entries_voucher_id ON ledger_entries(voucher_id);
CREATE INDEX idx_ledger_entries_ledger_id ON ledger_entries(ledger_id);
CREATE INDEX idx_ledger_entries_guid ON ledger_entries(guid);

-- Inventory entries indexes
CREATE INDEX idx_inventory_entries_voucher_id ON inventory_entries(voucher_id);
CREATE INDEX idx_inventory_entries_stock_item_id ON inventory_entries(stock_item_id);
CREATE INDEX idx_inventory_entries_guid ON inventory_entries(guid);

-- Master data indexes
CREATE INDEX idx_groups_guid ON groups(guid);
CREATE INDEX idx_groups_name ON groups(name);
CREATE INDEX idx_voucher_types_guid ON voucher_types(guid);
CREATE INDEX idx_voucher_types_name ON voucher_types(name);
CREATE INDEX idx_ledgers_guid ON ledgers(guid);
CREATE INDEX idx_ledgers_name ON ledgers(name);
CREATE INDEX idx_units_of_measure_guid ON units_of_measure(guid);
CREATE INDEX idx_units_of_measure_name ON units_of_measure(name);
CREATE INDEX idx_stock_categories_guid ON stock_categories(guid);
CREATE INDEX idx_stock_categories_name ON stock_categories(name);
CREATE INDEX idx_stock_groups_guid ON stock_groups(guid);
CREATE INDEX idx_stock_groups_name ON stock_groups(name);
CREATE INDEX idx_stock_items_guid ON stock_items(guid);
CREATE INDEX idx_stock_items_name ON stock_items(name);
CREATE INDEX idx_godowns_guid ON godowns(guid);
CREATE INDEX idx_godowns_name ON godowns(name);
CREATE INDEX idx_cost_categories_guid ON cost_categories(guid);
CREATE INDEX idx_cost_categories_name ON cost_categories(name);
CREATE INDEX idx_cost_centres_guid ON cost_centres(guid);
CREATE INDEX idx_cost_centres_name ON cost_centres(name);
CREATE INDEX idx_employees_guid ON employees(guid);
CREATE INDEX idx_employees_name ON employees(name);
CREATE INDEX idx_payheads_guid ON payheads(guid);
CREATE INDEX idx_payheads_name ON payheads(name);
CREATE INDEX idx_attendance_types_guid ON attendance_types(guid);
CREATE INDEX idx_attendance_types_name ON attendance_types(name);

-- Employee transaction indexes
CREATE INDEX idx_employee_entries_voucher_id ON employee_entries(voucher_id);
CREATE INDEX idx_employee_entries_employee_id ON employee_entries(employee_id);
CREATE INDEX idx_employee_entries_guid ON employee_entries(guid);
CREATE INDEX idx_payhead_allocations_voucher_id ON payhead_allocations(voucher_id);
CREATE INDEX idx_payhead_allocations_employee_id ON payhead_allocations(employee_id);
CREATE INDEX idx_payhead_allocations_payhead_id ON payhead_allocations(payhead_id);
CREATE INDEX idx_payhead_allocations_guid ON payhead_allocations(guid);
CREATE INDEX idx_attendance_entries_voucher_id ON attendance_entries(voucher_id);
CREATE INDEX idx_attendance_entries_employee_id ON attendance_entries(employee_id);
CREATE INDEX idx_attendance_entries_guid ON attendance_entries(guid);

-- Additional transaction table indexes
CREATE INDEX idx_cost_centre_allocations_trn_voucher_id ON cost_centre_allocations_trn(voucher_id);
CREATE INDEX idx_cost_centre_allocations_trn_ledger_entry_id ON cost_centre_allocations_trn(ledger_entry_id);
CREATE INDEX idx_cost_centre_allocations_trn_cost_centre_id ON cost_centre_allocations_trn(cost_centre_id);
CREATE INDEX idx_cost_centre_allocations_trn_guid ON cost_centre_allocations_trn(guid);

CREATE INDEX idx_cost_category_centre_allocations_voucher_id ON cost_category_centre_allocations(voucher_id);
CREATE INDEX idx_cost_category_centre_allocations_ledger_entry_id ON cost_category_centre_allocations(ledger_entry_id);
CREATE INDEX idx_cost_category_centre_allocations_cost_category_id ON cost_category_centre_allocations(cost_category_id);
CREATE INDEX idx_cost_category_centre_allocations_cost_centre_id ON cost_category_centre_allocations(cost_centre_id);
CREATE INDEX idx_cost_category_centre_allocations_guid ON cost_category_centre_allocations(guid);

CREATE INDEX idx_cost_inventory_category_centre_allocations_voucher_id ON cost_inventory_category_centre_allocations(voucher_id);
CREATE INDEX idx_cost_inventory_category_centre_allocations_inventory_entry_id ON cost_inventory_category_centre_allocations(inventory_entry_id);
CREATE INDEX idx_cost_inventory_category_centre_allocations_cost_category_id ON cost_inventory_category_centre_allocations(cost_category_id);
CREATE INDEX idx_cost_inventory_category_centre_allocations_cost_centre_id ON cost_inventory_category_centre_allocations(cost_centre_id);
CREATE INDEX idx_cost_inventory_category_centre_allocations_guid ON cost_inventory_category_centre_allocations(guid);

CREATE INDEX idx_inventory_accounting_entries_voucher_id ON inventory_accounting_entries(voucher_id);
CREATE INDEX idx_inventory_accounting_entries_inventory_entry_id ON inventory_accounting_entries(inventory_entry_id);
CREATE INDEX idx_inventory_accounting_entries_ledger_entry_id ON inventory_accounting_entries(ledger_entry_id);
CREATE INDEX idx_inventory_accounting_entries_guid ON inventory_accounting_entries(guid);

CREATE INDEX idx_closing_stock_ledger_voucher_id ON closing_stock_ledger(voucher_id);
CREATE INDEX idx_closing_stock_ledger_stock_item_id ON closing_stock_ledger(stock_item_id);
CREATE INDEX idx_closing_stock_ledger_guid ON closing_stock_ledger(guid);

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Voucher Summary View
CREATE VIEW voucher_summary AS
SELECT 
    v.id,
    v.guid,
    v.date,
    v.voucher_type,
    v.voucher_number,
    v.narration,
    v.party_name,
    v.place_of_supply,
    COUNT(DISTINCT le.id) as ledger_entry_count,
    COUNT(DISTINCT ie.id) as inventory_entry_count,
    SUM(le.amount) as total_ledger_amount,
    SUM(ie.amount) as total_inventory_amount
FROM vouchers v
LEFT JOIN ledger_entries le ON v.id = le.voucher_id
LEFT JOIN inventory_entries ie ON v.id = ie.voucher_id
GROUP BY v.id, v.guid, v.date, v.voucher_type, v.voucher_number, v.narration, v.party_name, v.place_of_supply;

-- Ledger Entry Details View
CREATE VIEW ledger_entry_details AS
SELECT 
    le.id,
    le.guid,
    v.date as voucher_date,
    v.voucher_type,
    v.voucher_number,
    l.name as ledger_name,
    le.amount,
    le.currency,
    le.is_debit,
    v.party_name
FROM ledger_entries le
JOIN vouchers v ON le.voucher_id = v.id
JOIN ledgers l ON le.ledger_id = l.id;

-- Inventory Entry Details View
CREATE VIEW inventory_entry_details AS
SELECT 
    ie.id,
    ie.guid,
    v.date as voucher_date,
    v.voucher_type,
    v.voucher_number,
    si.name as stock_item_name,
    ie.quantity,
    ie.rate,
    ie.amount,
    g.name as godown_name,
    ie.tracking_number,
    ie.order_number
FROM inventory_entries ie
JOIN vouchers v ON ie.voucher_id = v.id
LEFT JOIN stock_items si ON ie.stock_item_id = si.id
LEFT JOIN godowns g ON ie.godown_id = g.id;

-- Employee Entry Details View
CREATE VIEW employee_entry_details AS
SELECT 
    ee.id,
    ee.guid,
    v.date as voucher_date,
    v.voucher_type,
    v.voucher_number,
    e.name as employee_name,
    ee.category,
    ee.amount,
    ee.employee_sort_order
FROM employee_entries ee
JOIN vouchers v ON ee.voucher_id = v.id
LEFT JOIN employees e ON ee.employee_id = e.id;

-- Payhead Allocation Details View
CREATE VIEW payhead_allocation_details AS
SELECT 
    pa.id,
    pa.guid,
    v.date as voucher_date,
    v.voucher_type,
    v.voucher_number,
    e.name as employee_name,
    p.name as payhead_name,
    pa.category,
    pa.amount,
    pa.employee_sort_order,
    pa.payhead_sort_order
FROM payhead_allocations pa
JOIN vouchers v ON pa.voucher_id = v.id
LEFT JOIN employees e ON pa.employee_id = e.id
LEFT JOIN payheads p ON pa.payhead_id = p.id;

-- Attendance Entry Details View
CREATE VIEW attendance_entry_details AS
SELECT 
    ae.id,
    ae.guid,
    v.date as voucher_date,
    v.voucher_type,
    v.voucher_number,
    e.name as employee_name,
    at.name as attendance_type_name,
    ae.attendance_type,
    ae.time_value,
    ae.type_value
FROM attendance_entries ae
JOIN vouchers v ON ae.voucher_id = v.id
LEFT JOIN employees e ON ae.employee_id = e.id
LEFT JOIN attendance_types at ON ae.attendance_type_id = at.id;

-- =====================================================
-- MISSING TRANSACTION TABLES FROM CSV RELATIONSHIPS
-- =====================================================

-- Accounting Entries Transaction Table (trn_accounting)
CREATE TABLE accounting_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    ledger_id INTEGER,
    ledger_name TEXT,
    amount DECIMAL(15,2),
    amount_forex DECIMAL(15,2),
    currency TEXT,
    is_debit BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (ledger_id) REFERENCES ledgers(id)
);

-- Inventory Transaction Table (trn_inventory) 
CREATE TABLE inventory_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    stock_item_id INTEGER,
    stock_item_name TEXT,
    godown_id INTEGER,
    godown_name TEXT,
    quantity DECIMAL(15,4),
    rate DECIMAL(15,2),
    amount DECIMAL(15,2),
    amount_forex DECIMAL(15,2),
    currency TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (stock_item_id) REFERENCES stock_items(id),
    FOREIGN KEY (godown_id) REFERENCES godowns(id)
);

-- Cost Centre Transaction Table (trn_cost_centre)
CREATE TABLE cost_centre_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    ledger_id INTEGER,
    ledger_name TEXT,
    cost_centre_id INTEGER,
    cost_centre_name TEXT,
    amount DECIMAL(15,2),
    amount_forex DECIMAL(15,2),
    currency TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (ledger_id) REFERENCES ledgers(id),
    FOREIGN KEY (cost_centre_id) REFERENCES cost_centres(id)
);

-- Cost Category Centre Transaction Table (trn_cost_category_centre)
CREATE TABLE cost_category_centre_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    ledger_id INTEGER,
    ledger_name TEXT,
    cost_category_id INTEGER,
    cost_category_name TEXT,
    cost_centre_id INTEGER,
    cost_centre_name TEXT,
    amount DECIMAL(15,2),
    amount_forex DECIMAL(15,2),
    currency TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (ledger_id) REFERENCES ledgers(id),
    FOREIGN KEY (cost_category_id) REFERENCES cost_categories(id),
    FOREIGN KEY (cost_centre_id) REFERENCES cost_centres(id)
);

-- Batch Transaction Table (trn_batch)
CREATE TABLE batch_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    voucher_id INTEGER NOT NULL,
    stock_item_id INTEGER,
    stock_item_name TEXT,
    godown_id INTEGER,
    godown_name TEXT,
    batch_name TEXT,
    quantity DECIMAL(15,4),
    rate DECIMAL(15,2),
    amount DECIMAL(15,2),
    amount_forex DECIMAL(15,2),
    currency TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE,
    FOREIGN KEY (stock_item_id) REFERENCES stock_items(id),
    FOREIGN KEY (godown_id) REFERENCES godowns(id)
);
