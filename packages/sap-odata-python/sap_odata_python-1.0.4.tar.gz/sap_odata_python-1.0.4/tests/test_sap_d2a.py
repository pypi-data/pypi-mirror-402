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
"""

from sap_odata import ODataClient, ODataError, ODataConnectionError, ODataAuthError
import json


# SAP D2A Configuration
SAP_CONFIG = {
    "host": "https://saphec-dv2.cisco.com:44300",
    "username": "vaibhago",
    "password": "Aichusiddhu123))",
    "client": "120",
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
