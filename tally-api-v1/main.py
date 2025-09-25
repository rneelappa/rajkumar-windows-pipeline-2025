#!/usr/bin/env python3
"""
Tally API v1 - Main Execution Script
====================================

This is the main entry point for the Tally to Supabase API integration.
It extracts data from Tally and sends it to the Supabase API with proper debit/credit accounting.

Usage:
    python main.py [--max-vouchers N]

Examples:
    python main.py                    # Process all vouchers
    python main.py --max-vouchers 10  # Process only 10 vouchers for testing
"""

import argparse
import logging
import sys
from production_api_with_real_data import ProductionAPIWithRealData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('tally_api.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Tally to Supabase API Integration')
    parser.add_argument('--max-vouchers', type=int, help='Maximum number of vouchers to process (for testing)')
    parser.add_argument('--dry-run', action='store_true', help='Extract data but do not send to API')
    
    args = parser.parse_args()
    
    try:
        logger.info("🚀 Starting Tally API v1 Integration")
        logger.info("=" * 80)
        
        # Create the production API instance
        api_solution = ProductionAPIWithRealData()
        
        if args.dry_run:
            logger.info("🔍 Running in DRY-RUN mode - no data will be sent to API")
            # Extract data only
            tally_data = api_solution.extract_real_tally_data()
            logger.info(f"📊 Extracted: {len(tally_data.get('vouchers', []))} vouchers, "
                       f"{len(tally_data.get('ledger_entries', []))} ledger entries, "
                       f"{len(tally_data.get('inventory_entries', []))} inventory entries")
        else:
            # Run full production API test
            success = api_solution.run_production_api_test(max_vouchers=args.max_vouchers)
            
            if success:
                logger.info("✅ Tally API Integration completed successfully!")
                return 0
            else:
                logger.error("❌ Tally API Integration failed!")
                return 1
                
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
