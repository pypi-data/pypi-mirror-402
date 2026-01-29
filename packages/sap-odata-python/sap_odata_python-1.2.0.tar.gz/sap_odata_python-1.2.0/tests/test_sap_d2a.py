"""
Test script for sap-odata-python library against SAP D2A system.

Service: zsd_file_manager (V4)
Entity: FileManager

FileManagerType Properties:
- file_name: File Name with extension (key)
- file_path: File/Folder Path (key)
- operation_type: Operation Type (key)
- logical_filename: Logical File Name
- folder_name: Folder Name
- file_size: File Size
- file_owner: File Owner
- modified_date: Last Modified Date
- modified_time: Last Modified Time
- total_file_count: Total Files in Folder
- file_content: File content
- include_content: Include file content in response
- overwrite: Overwrite Existing
- status: Status
- message: Message

NOTE: This test requires SAP credentials set via environment variables:
- SAP_HOST: SAP system URL
- SAP_USERNAME: SAP username
- SAP_PASSWORD: SAP password
- SAP_CLIENT: SAP client number
"""

import os
from sap_odata import ODataClient, ODataError, ODataConnectionError, ODataAuthError
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SAP D2A Configuration from environment variables
SAP_CONFIG = {
    "host": os.environ.get("SAP_HOST",""),
    "username": os.environ.get("SAP_USERNAME",""),
    "password": os.environ.get("SAP_PASSWORD",""),
    "client": os.environ.get("SAP_CLIENT",""),
}

# Service Configuration
SERVICE = "zsd_file_manager"
NAMESPACE = "zsb_file_manager"
ENTITY = "FileManager"


def test_metadata():
    """Test: Get service metadata."""
    print("\n" + "=" * 60)
    print("TEST 1: Get Metadata")
    print("=" * 60)
    
    client = ODataClient(
        SAP_CONFIG["host"],
        username=SAP_CONFIG["username"],
        password=SAP_CONFIG["password"],
        client=SAP_CONFIG["client"],
        sap_mode=True,
    )
    
    metadata = client.metadata(SERVICE, version="v4", namespace=NAMESPACE)
    print(f"✅ Metadata retrieved: {len(metadata)} chars")
    print(f"   Contains 'FileManagerType': {'FileManagerType' in metadata}")
    return True


def test_list_files():
    """Test: List files in a directory."""
    print("\n" + "=" * 60)
    print("TEST 2: List Files in Directory")
    print("=" * 60)
    
    client = ODataClient(
        SAP_CONFIG["host"],
        username=SAP_CONFIG["username"],
        password=SAP_CONFIG["password"],
        client=SAP_CONFIG["client"],
        sap_mode=True,
    )
    
    result = client.get(
        service=SERVICE,
        entity=ENTITY,
        version="v4",
        namespace=NAMESPACE,
        filter="file_path eq '/interface/D2A/Common/Inbound/I001A/Load' and include_content eq false",
    )
    
    files = result.get("value", [])
    print(f"✅ Found {len(files)} file(s)")
    
    for f in files[:5]:  # Show first 5
        print(f"   - {f.get('file_name')} ({f.get('status')})")
    
    return True


def test_check_specific_file():
    """Test: Check if specific file exists."""
    print("\n" + "=" * 60)
    print("TEST 3: Check Specific File")
    print("=" * 60)
    
    client = ODataClient(
        SAP_CONFIG["host"],
        username=SAP_CONFIG["username"],
        password=SAP_CONFIG["password"],
        client=SAP_CONFIG["client"],
        sap_mode=True,
    )
    
    file_name = "INTSRQ2A01126_Base_ATO1.json"
    file_path = "/interface/D2A/Common/Inbound/I001A/Load"
    
    result = client.get(
        service=SERVICE,
        entity=ENTITY,
        version="v4",
        namespace=NAMESPACE,
        filter=f"file_name eq '{file_name}' and file_path eq '{file_path}' and include_content eq false",
    )
    
    files = result.get("value", [])
    if files:
        f = files[0]
        print(f"✅ File check completed")
        print(f"   File: {f.get('file_name')}")
        print(f"   Path: {f.get('file_path')}")
        print(f"   Status: {f.get('status')}")
        print(f"   Message: {f.get('message')}")
    else:
        print("❌ No response received")
    
    return True


def test_select_fields():
    """Test: Select specific fields only."""
    print("\n" + "=" * 60)
    print("TEST 4: Select Specific Fields")
    print("=" * 60)
    
    client = ODataClient(
        SAP_CONFIG["host"],
        username=SAP_CONFIG["username"],
        password=SAP_CONFIG["password"],
        client=SAP_CONFIG["client"],
        sap_mode=True,
    )
    
    result = client.get(
        service=SERVICE,
        entity=ENTITY,
        version="v4",
        namespace=NAMESPACE,
        filter="file_path eq '/interface/D2A/Common/Inbound/I001A/Load' and include_content eq false",
        select="file_name,file_path,status,message",
    )
    
    files = result.get("value", [])
    print(f"✅ Query with $select completed")
    print(f"   Found {len(files)} file(s)")
    
    if files:
        print(f"   Fields returned: {list(files[0].keys())}")
    
    return True


def test_pagination():
    """Test: Pagination with get_next_link() and get_value() helpers."""
    print("\n" + "=" * 60)
    print("TEST 5: Pagination & Helper Methods (SKU Filter API)")
    print("=" * 60)
    
    client = ODataClient(
        SAP_CONFIG["host"],
        username=SAP_CONFIG["username"],
        password=SAP_CONFIG["password"],
        client=SAP_CONFIG["client"],
        sap_mode=True,
    )
    
    # First page - small page size
    result = client.get(
        service="zsd_sku_filter",
        entity="Products",
        version="v4",
        namespace="zsb_sku_filter_api",
        top=5,
    )
    
    # Test raw response structure (V4)
    print(f"✅ Raw response keys: {list(result.keys())}")
    assert "@odata.context" in result, "V4 response should have @odata.context"
    
    # Test get_value() helper
    items = client.get_value(result, "v4")
    print(f"✅ get_value() returned: {len(items)} items")
    assert isinstance(items, list), "get_value should return a list"
    
    # Test get_next_link() helper
    next_link = client.get_next_link(result, "v4")
    print(f"✅ get_next_link() returned: {'URL' if next_link else 'None (no more pages)'}")
    
    # Show sample data
    if items:
        print(f"   Sample fields: {list(items[0].keys())[:5]}...")
        for item in items[:3]:
            print(f"   - {item.get('ProductName', 'N/A')}: {item.get('ChargeType', 'N/A')}")
    
    print(f"✅ Pagination test completed")
    return True


def test_count_only():
    """Test: Count only endpoint (/Entity/$count) - returns just the number."""
    print("\n" + "=" * 60)
    print("TEST 6: Count Only Endpoint (/Entity/$count)")
    print("=" * 60)
    
    client = ODataClient(
        SAP_CONFIG["host"],
        username=SAP_CONFIG["username"],
        password=SAP_CONFIG["password"],
        client=SAP_CONFIG["client"],
        sap_mode=True,
    )
    
    # Count all files in a directory
    total = client.count(
        service=SERVICE,
        entity=ENTITY,
        version="v4",
        namespace=NAMESPACE,
        filter="file_path eq '/interface/D2A/Common/Inbound/I001A/Load' and include_content eq false",
    )
    
    print(f"✅ count() returned: {total}")
    assert isinstance(total, int), "count() should return an integer"
    assert total >= 0, "count should be non-negative"
    print(f"   Total files in directory: {total}")
    
    # Count with different filter (SKU Filter API for variety)
    sku_count = client.count(
        service="zsd_sku_filter",
        entity="Products",
        version="v4",
        namespace="zsb_sku_filter_api",
    )
    
    print(f"✅ SKU Products count: {sku_count}")
    assert isinstance(sku_count, int), "count() should return an integer"
    
    print(f"✅ Count only test completed")
    return True


def test_inline_count():
    """Test: Inline count with data ($count=true) - returns count + data."""
    print("\n" + "=" * 60)
    print("TEST 7: Inline Count ($count=true)")
    print("=" * 60)
    
    client = ODataClient(
        SAP_CONFIG["host"],
        username=SAP_CONFIG["username"],
        password=SAP_CONFIG["password"],
        client=SAP_CONFIG["client"],
        sap_mode=True,
    )
    
    # Get data with inline count
    result = client.get(
        service="zsd_sku_filter",
        entity="Products",
        version="v4",
        namespace="zsb_sku_filter_api",
        top=5,
        count=True,  # Request inline count
    )
    
    print(f"✅ Raw response keys: {list(result.keys())}")
    
    # V4 response should have @odata.count
    assert "@odata.count" in result, "V4 response with $count=true should have @odata.count"
    
    # Use get_count() helper to extract count
    total_count = client.get_count(result, "v4")
    print(f"✅ get_count() returned: {total_count}")
    assert isinstance(total_count, int), "get_count() should return an integer"
    assert total_count >= 0, "count should be non-negative"
    
    # Use get_value() helper to extract data
    items = client.get_value(result, "v4")
    print(f"✅ get_value() returned: {len(items)} items")
    assert isinstance(items, list), "get_value() should return a list"
    
    # Verify we got limited results but total count is higher
    print(f"   Returned items: {len(items)}")
    print(f"   Total available: {total_count}")
    assert len(items) <= 5, "Should respect $top=5 limit"
    
    # Show comparison
    if total_count > len(items):
        print(f"   ℹ️  Showing {len(items)} of {total_count} total records")
    
    print(f"✅ Inline count test completed")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "#" * 60)
    print("SAP OData Python Library - D2A Integration Tests")
    print("#" * 60)
    print(f"\nHost: {SAP_CONFIG['host']}")
    print(f"Client: {SAP_CONFIG['client']}")
    print(f"Service: {SERVICE} (V4)")
    print(f"Namespace: {NAMESPACE}")
    
    tests = [
        ("Metadata", test_metadata),
        ("List Files", test_list_files),
        ("Check Specific File", test_check_specific_file),
        ("Select Fields", test_select_fields),
        ("Pagination", test_pagination),
        ("Count Only (/Entity/$count)", test_count_only),
        ("Inline Count ($count=true)", test_inline_count),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            success = test_fn()
            results.append((name, "✅ PASSED" if success else "❌ FAILED"))
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append((name, f"❌ ERROR: {str(e)[:50]}"))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, result in results:
        print(f"  {name}: {result}")
    
    passed = sum(1 for _, r in results if "PASSED" in r)
    print(f"\nTotal: {passed}/{len(tests)} tests passed")


if __name__ == "__main__":
    run_all_tests()
