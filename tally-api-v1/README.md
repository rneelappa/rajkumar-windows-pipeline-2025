# Tally API v1 Integration

A production-ready solution for extracting data from TallyPrime and sending it to Supabase API with proper accounting logic.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Test with 10 vouchers
python main.py --max-vouchers 10

# Full production run
python main.py
```

## Features

- ✅ **Real-time Tally Integration** - Direct connection to TallyPrime via API
- ✅ **Proper Accounting Logic** - Handles debit/credit assignment correctly
- ✅ **Production Ready** - Comprehensive error handling and logging
- ✅ **Scalable** - Processes 1,748+ vouchers efficiently
- ✅ **Configurable** - YAML-based configuration for flexibility

## Architecture

```
TallyPrime → Tally API v1 → Supabase API → PostgreSQL
```

## Performance

- **Throughput**: ~28 vouchers/minute
- **Success Rate**: 100%
- **Full Dataset**: ~62 minutes for 1,748 vouchers

## Documentation

See `tally-api-execution25sep2025.txt` for complete documentation including:
- Detailed setup instructions
- File descriptions
- Troubleshooting guide
- Performance metrics
- Security considerations

## Support

Check the logs in `tally_api.log` for detailed execution information.
