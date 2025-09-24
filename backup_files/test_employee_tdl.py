#!/usr/bin/env python3
"""
Test Employee TDL Implementation
===============================

This script tests the comprehensive TDL with employee WALK functionality.
It sends the TDL to Tally server and saves the response for analysis.

Usage:
    python3 test_employee_tdl.py
"""

import sys
import os
import time
from tally_client import TallyClient

def test_employee_comprehensive_tdl():
    """Test the comprehensive TDL with employee WALK functionality"""

    # Create Tally client
    tally_client = TallyClient(base_url="https://d06cf3740c40.ngrok-free.app")

    print("🔄 Testing Comprehensive TDL with Employee Data")
    print("=" * 60)

    try:
        # Create comprehensive TDL with employee WALKs
        tdl_xml = tally_client.create_comprehensive_tdl()

        print(f"📤 Sending TDL request to Tally server...")
        print(f"📏 TDL size: {len(tdl_xml):,} characters")

        # Send TDL request
        start_time = time.time()
        response = tally_client.send_tdl_request(tdl_xml)
        end_time = time.time()

        response_time = end_time - start_time
        print(f"⏱️  Response time: {response_time:.2f} seconds")

        if response:
            print(f"📥 Response received: {len(response):,} characters")

            # Save response for analysis
            output_file = "xml-files/employee_comprehensive_response.xml"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(response)
            print(f"💾 Response saved to: {output_file}")

            # Basic analysis
            if "TRN_EMPLOYEE_" in response:
                print("✅ Employee data found in response!")
            else:
                print("⚠️  No employee data found in response")

            if "TRN_PAYHEAD_" in response:
                print("✅ Payhead data found in response!")
            else:
                print("⚠️  No payhead data found in response")

            if "TRN_ATTENDANCE_" in response:
                print("✅ Attendance data found in response!")
            else:
                print("⚠️  No attendance data found in response")

            # Check for data volume
            employee_count = response.count('TRN_EMPLOYEE_')
            payhead_count = response.count('TRN_PAYHEAD_')
            attendance_count = response.count('TRN_ATTENDANCE_')

            print("📊 Employee Data Summary:")
            print(f"   Employee entries: {employee_count}")
            print(f"   Payhead allocations: {payhead_count}")
            print(f"   Attendance entries: {attendance_count}")

        else:
            print("❌ No response received from Tally server")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

    return True

def main():
    """Main test function"""
    print("🧪 EMPLOYEE TDL TEST")
    print("=" * 40)

    success = test_employee_comprehensive_tdl()

    if success:
        print("🎉 Employee TDL test completed successfully!")
    else:
        print("❌ Employee TDL test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
