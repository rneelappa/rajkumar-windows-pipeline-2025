# Tally to Supabase Migration System

A production-ready migration system that connects Tally ERP directly to Supabase PostgreSQL database.

## Overview

This system implements a 4-phase migration process:
1. **Tally → Validate**: Extract and validate data from Tally ERP
2. **Supabase → Validate**: Migrate validated data to Supabase PostgreSQL
3. **Validation**: Comprehensive data validation and relationship checks
4. **Production Ready**: Idempotent, batch processing, error handling

## Features

- ✅ **Direct Migration**: Tally → Supabase (no intermediate SQLite)
- ✅ **Batch Processing**: Prevents timeouts with large datasets
- ✅ **Upsert Logic**: Safe to run multiple times
- ✅ **Relationship Validation**: Ensures data integrity
- ✅ **Comprehensive Master Data**: Groups, Ledgers, Stock Items, etc.
- ✅ **Transaction Data**: Vouchers, Ledger Entries, Inventory Entries
- ✅ **Error Handling**: Robust error handling and logging
- ✅ **Production Ready**: Configurable, scalable, maintainable

## Project Structure

```
xml-quick-parser/
├── config.yaml                    # Configuration file
├── config_manager.py              # Configuration management
├── tally_client.py                # Tally ERP client
├── supabase_manager.py            # Supabase PostgreSQL client
├── tally_migration_system.py      # Main migration system
├── postgres_schema.sql            # PostgreSQL schema
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── tally-export-config.yaml       # Tally export configuration
├── tallyyaml.txt                 # Tally schema definitions
├── tally.mts.txt                  # Tally MTS definitions
├── Coderef.txt                    # Reference implementation
├── tallyrelationships.csv         # Table relationships
├── selfhierarchy.csv              # Self-referencing relationships
├── tabletotablelinks.csv          # Cross-table relationships
└── backup_files/                  # Backup of development files
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/rneelappa/rajkumar-windows-pipeline-2025.git
   cd rajkumar-windows-pipeline-2025
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the system**:
   - Update `config.yaml` with your Tally and Supabase credentials
   - Ensure Tally is running and accessible via ngrok

## Configuration

Edit `config.yaml` with your specific settings:

```yaml
company_id: "bc90d453-0c64-4f6f-8bbe-dca32aba40d1"
division_id: "b38bfb72-3dd7-4aa5-b970-71b919d5ded4"
tally_company_name: "SKM IMPEX-CHENNAI-(24-25)"
tally_url: "https://your-ngrok-url.ngrok-free.app"
supabase_schema: "tally"
supabase:
  host: "aws-0-ap-southeast-1.pooler.supabase.com"
  port: 5432
  database: "postgres"
  user: "postgres.your-user"
  password: "your-password"
  pool_mode: "session"
```

## Usage

### Complete Migration
```bash
python tally_migration_system.py
```

### Individual Phases
```bash
# Extract data from Tally
python tally_migration_system.py --phase 1

# Validate extracted data
python tally_migration_system.py --phase 2

# Migrate to Supabase
python tally_migration_system.py --phase 3

# Validate Supabase data
python tally_migration_system.py --phase 4
```

## Database Schema

The system creates the following tables in Supabase:

### Master Data Tables
- `groups` - Account groups
- `ledgers` - Chart of accounts
- `stock_items` - Inventory items
- `voucher_types` - Voucher type definitions
- `godowns` - Warehouse locations
- `stock_categories` - Stock categorization
- `stock_groups` - Stock grouping
- `units_of_measure` - Measurement units
- `cost_categories` - Cost categorization
- `cost_centres` - Cost centers

### Transaction Data Tables
- `vouchers` - Financial vouchers
- `ledger_entries` - Voucher ledger entries
- `inventory_entries` - Voucher inventory entries

All tables include:
- `company_id` and `division_id` for multi-tenancy
- `guid` for Tally integration
- Proper foreign key relationships
- Upsert capabilities

## Migration Process

### Phase 1: Extract from Tally
- Connects to Tally ERP via ngrok
- Extracts master data (Groups, Ledgers, Stock Items, etc.)
- Extracts transaction data (Vouchers, Entries)
- Validates data structure and completeness

### Phase 2: Validate Data
- Checks data integrity
- Validates required fields (GUID, Name)
- Ensures proper data types
- Reports data quality metrics

### Phase 3: Migrate to Supabase
- Connects to Supabase PostgreSQL
- Migrates master data in batches
- Migrates transaction data in batches
- Implements upsert logic for idempotency

### Phase 4: Validate Supabase
- Verifies record counts
- Checks foreign key relationships
- Identifies orphaned records
- Reports migration success metrics

## Error Handling

The system includes comprehensive error handling:
- Network timeouts and connection issues
- Data validation errors
- Database constraint violations
- Tally server crashes and recovery
- Batch processing failures

## Logging

All operations are logged to:
- Console output (real-time monitoring)
- `migration.log` file (persistent logging)

Log levels include:
- INFO: Normal operations
- WARNING: Non-critical issues
- ERROR: Critical failures

## Production Considerations

### Performance
- Batch processing prevents timeouts
- Configurable batch sizes
- Connection pooling
- Efficient upsert operations

### Reliability
- Idempotent operations
- Comprehensive error handling
- Data validation at each phase
- Rollback capabilities

### Security
- Environment-based configuration
- No hardcoded credentials
- Secure database connections
- Input validation and sanitization

## Troubleshooting

### Common Issues

1. **Tally Connection Failed**
   - Verify ngrok is running
   - Check Tally server status
   - Validate company name in config

2. **Supabase Connection Failed**
   - Verify database credentials
   - Check network connectivity
   - Ensure schema exists

3. **Data Validation Errors**
   - Check Tally data integrity
   - Verify XML parsing
   - Review field mappings

4. **Migration Timeouts**
   - Reduce batch sizes
   - Check network stability
   - Monitor resource usage

### Debug Mode
Enable debug logging by modifying the logging level in `tally_migration_system.py`:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section
- Review the logs for error details

## Changelog

### Version 1.0.0
- Initial production release
- 4-phase migration system
- Comprehensive master and transaction data support
- Batch processing and error handling
- Supabase integration