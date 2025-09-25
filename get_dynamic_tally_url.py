#!/usr/bin/env python3
"""
Get Dynamic Tally URL
====================
Simple function to get the current Tally URL from the database.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def get_tally_url() -> Optional[str]:
    """
    Get the current Tally URL from vyaapari_divisions table.
    Returns the URL or None if not found/accessible.
    """
    try:
        # Direct database connection
        conn = psycopg2.connect(
            host='aws-0-ap-southeast-1.pooler.supabase.com',
            port=5432,
            database='postgres',
            user='postgres.ppfwlhfehwelinfprviw',
            password='RAJK22**kjar'
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SET search_path TO public')
        
        # Query for Tally URL
        company_id = 'bc90d453-0c64-4f6f-8bbe-dca32aba40d1'
        division_id = 'b38bfb72-3dd7-4aa5-b970-71b919d5ded4'
        
        cursor.execute("""
            SELECT tally_url 
            FROM vyaapari_divisions 
            WHERE company_id = %s AND id = %s
        """, (company_id, division_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result['tally_url']:
            tally_url = result['tally_url'].strip()
            logger.info(f"✅ Retrieved Tally URL: {tally_url}")
            return tally_url
        else:
            logger.warning("⚠️  No Tally URL found in database")
            return None
            
    except Exception as e:
        logger.error(f"❌ Failed to retrieve Tally URL: {e}")
        return None

def test_tally_url(url: str) -> bool:
    """Test if the Tally URL is accessible."""
    try:
        import requests
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except:
        return False

def get_and_validate_tally_url() -> Optional[str]:
    """Get Tally URL and validate it's accessible."""
    url = get_tally_url()
    if url and test_tally_url(url):
        return url
    return None

if __name__ == "__main__":
    print("🔍 Testing Dynamic Tally URL...")
    url = get_and_validate_tally_url()
    if url:
        print(f"✅ Tally URL is ready: {url}")
    else:
        print("❌ No valid Tally URL available")
