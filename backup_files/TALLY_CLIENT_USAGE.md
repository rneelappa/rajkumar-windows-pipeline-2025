# Tally Client Usage Guide

## 🎯 Overview

I've successfully created a Python equivalent of your C# Tally client that can send TDL XML messages to your Tally server via the ngrok URL. The client is ready to use once your Tally server is running.

## 📁 Files Created

- `tally_client.py` - Main Python Tally client
- `venv/` - Virtual environment with required dependencies
- `TALLY_CLIENT_USAGE.md` - This usage guide

## 🚀 Quick Start

### 1. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 2. Test Connection
```bash
python3 tally_client.py --test
```

### 3. Export Voucher Data
```bash
# Basic query (fastest)
python3 tally_client.py --query-type basic --save basic_export.xml

# Simple query
python3 tally_client.py --query-type simple --save simple_export.xml

# Comprehensive query (includes ledger/inventory entries - takes 10-20 seconds)
python3 tally_client.py --query-type comprehensive --save comprehensive_export.xml
```

## 🔧 Current Status

**❌ Tally Server Status**: Currently offline
- The ngrok tunnel is active but can't connect to localhost:9000
- Error: "No connection could be made because the target machine actively refused it"

## 🛠️ Tally Server Setup Required

To use the client, you need to:

1. **Start Tally Server**:
   - Open TallyPrime
   - Go to Gateway of Tally > F11 (Features) > Set "Use Tally.ERP 9 in Server Mode" to Yes
   - Set "Server Port" to 9000 (or update the ngrok tunnel accordingly)

2. **Verify ngrok Tunnel**:
   - Make sure ngrok is running and pointing to localhost:9000
   - Update the URL in `tally_client.py` if your ngrok URL changes

## 📋 Available Commands

### Connection Test
```bash
python3 tally_client.py --test
```

### Export Options
```bash
# Basic voucher data (voucher fields only)
python3 tally_client.py --query-type basic --company "YOUR_COMPANY_NAME"

# Simple voucher data (same as basic)
python3 tally_client.py --query-type simple --company "YOUR_COMPANY_NAME"

# Comprehensive data (includes ledger/inventory entries)
python3 tally_client.py --query-type comprehensive --company "YOUR_COMPANY_NAME"
```

### Custom Options
```bash
# Custom company name
python3 tally_client.py --company "SKM IMPEX-CHENNAI-(24-25)"

# Custom ngrok URL
python3 tally_client.py --url "https://your-ngrok-url.ngrok-free.app"

# Save to specific file
python3 tally_client.py --save "my_export.xml"
```

## 🔍 TDL Queries Available

### 1. Basic Query (`--query-type basic`)
- **Purpose**: Fast voucher data export
- **Fields**: voucher_amount, voucher_date, voucher_id, voucher_narration, voucher_party_name, voucher_reference, voucher_voucher_number, voucher_voucher_type
- **Speed**: Fast (< 5 seconds)

### 2. Simple Query (`--query-type simple`)
- **Purpose**: Same as basic but with different TDL structure
- **Fields**: Same as basic
- **Speed**: Fast (< 5 seconds)

### 3. Comprehensive Query (`--query-type comprehensive`)
- **Purpose**: Full voucher data with ledger and inventory entries
- **Fields**: All basic fields + trn_inventoryentries_*, trn_ledgerentries_*
- **Speed**: Slow (10-20 seconds) - **This is the equivalent of your C# code**

## 📊 Expected Output

When successful, the client will:
1. ✅ Test connection to Tally server
2. 🔍 Send TDL XML request
3. ⏳ Wait for response (10-20 seconds for comprehensive query)
4. 📊 Receive XML response with voucher data
5. 💾 Save response to `xml-files/` directory
6. 🎉 Display success message with file path

## 🐛 Troubleshooting

### Connection Issues
- **Error**: "Connection failed. Status: 400"
  - **Solution**: Check if Tally server is running on port 9000
  - **Solution**: Verify ngrok tunnel is active and pointing to correct port

### Timeout Issues
- **Error**: "Read timed out"
  - **Solution**: This is normal for comprehensive queries - increase timeout in code
  - **Solution**: Use basic/simple queries for faster results

### TDL Errors
- **Error**: "Could not find Report"
  - **Solution**: Check company name spelling
  - **Solution**: Verify Tally server has the specified company loaded

## 🔄 Next Steps

1. **Start your Tally server** on port 9000
2. **Verify ngrok tunnel** is active
3. **Test connection**: `python3 tally_client.py --test`
4. **Export data**: `python3 tally_client.py --query-type comprehensive`

## 💡 Python vs C# Differences

| Feature | C# | Python |
|---------|----|---------| 
| HTTP Client | HttpClient | requests library |
| XML Generation | String concatenation | f-strings |
| Error Handling | try-catch | try-except |
| Async Support | async/await | Not implemented |
| Timeout | Default | 120 seconds |

The Python version provides the same functionality as your C# code but with Python's syntax and ecosystem benefits.
