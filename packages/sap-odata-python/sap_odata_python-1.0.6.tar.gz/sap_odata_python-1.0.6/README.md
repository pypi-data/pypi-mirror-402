# SAP OData Python

Simple, AI/LLM-friendly Python client for SAP OData V2 and V4 services.

[![PyPI](https://img.shields.io/pypi/v/sap-odata-python)](https://pypi.org/project/sap-odata-python/)
[![Python](https://img.shields.io/pypi/pyversions/sap-odata-python)](https://pypi.org/project/sap-odata-python/)
[![License](https://img.shields.io/pypi/l/sap-odata-python)](https://github.com/vaibhavgoel-github-1986/sap-odata-python/blob/main/LICENSE)

## Why This Library?

- **SAP-First Design**: Built specifically for SAP OData services (V2 Gateway & V4 RAP)
- **AI/LLM Friendly**: Single generic function design - perfect for AI agents and automation
- **Simple API**: One client, one method signature for all operations
- **Automatic URL Building**: Handles complex SAP URL patterns automatically
- **Input Validation**: Clear error messages for missing parameters
- **Raw Responses**: Returns API responses as-is (no transformation)
- **Helper Methods**: `get_value()` and `get_next_link()` for convenient data extraction

## Installation

\`\`\`bash
pip install sap-odata-python
\`\`\`

## Quick Start - SAP Systems

\`\`\`python
from sap_odata import ODataClient

# Connect to SAP system (sap_mode=True is the default)
client = ODataClient(
    "https://sap-system.company.com:44300",
    username="your_user",
    password="your_password",
    client="100"
)

# SAP OData V4 (RAP Services)
response = client.get(
    service="zsd_my_service",
    entity="MyEntity",
    version="v4",
    namespace="zsb_my_service",  # Required for V4
    filter="Status eq 'ACTIVE'",
    top=10
)
# V4 Response: {"@odata.context": "...", "value": [...]}
items = client.get_value(response, "v4")

# SAP OData V2 (Gateway Services)
response = client.get(
    service="ZMY_SALESORDER_SRV",
    entity="SalesOrderSet",
    version="v2",
    filter="Status eq 'OPEN'",
    top=10
)
# V2 Response: {"d": {"results": [...]}} or {"d": [...]}
items = client.get_value(response, "v2")

for item in items:
    print(item)
\`\`\`

## Response Formats

This library returns **raw API responses** without transformation:

| Version | Collection Response | Single Entity Response |
|---------|---------------------|------------------------|
| **V4** | `{"@odata.context": "...", "value": [...]}` | `{"@odata.context": "...", "ID": 1, ...}` |
| **V2** | `{"d": {"results": [...]}}` or `{"d": [...]}` | `{"d": {"ID": 1, ...}}` |

### Helper Methods

Use helper methods to extract data consistently:

\`\`\`python
# get_value() - Extract entities as a list (works for both V2 and V4)
response = client.get("ZMY_SRV", "Products", version="v2", top=10)
items = client.get_value(response, "v2")  # Returns list of products

# get_next_link() - Get pagination URL
next_url = client.get_next_link(response, "v4")  # @odata.nextLink
next_url = client.get_next_link(response, "v2")  # d.__next
\`\`\`

## SAP URL Patterns (Handled Automatically)

The library automatically builds correct SAP URLs:

| Version | URL Pattern |
|---------|-------------|
| **V4** | `/sap/opu/odata4/sap/{namespace}/srvd_a2x/sap/{service}/0001/{entity}` |
| **V2** | `/sap/opu/odata/sap/{service}/{entity}` |

You just provide `service`, `entity`, and `namespace` (for V4) - the library builds the full URL.

## API Reference

### ODataClient Constructor

\`\`\`python
client = ODataClient(
    host,                    # SAP system URL (e.g., "https://sap.company.com:44300")
    username="",             # SAP username
    password="",             # SAP password
    client="",               # SAP client number (e.g., "100", "120")
    sap_mode=True,           # True for SAP systems (default), False for other OData services
    verify_ssl=True,         # SSL certificate verification
    timeout=60               # Request timeout in seconds
)
\`\`\`

### Methods

| Method | Description |
|--------|-------------|
| `get(service, entity, version, namespace, **params)` | Read data (GET) |
| `post(service, entity, data, version, namespace)` | Create record (POST) |
| `patch(service, entity, data, version, namespace)` | Update record (PATCH) |
| `delete(service, entity, version, namespace)` | Delete record (DELETE) |
| `metadata(service, version, namespace)` | Get service metadata (XML) |
| `get_value(response, version)` | Extract entities as list from response |
| `get_next_link(response, version)` | Extract pagination URL from response |

### Query Parameters (for GET)

| Parameter | Example | Description |
|-----------|---------|-------------|
| `top` | `top=10` | Limit number of results |
| `skip` | `skip=20` | Skip records (pagination) |
| `filter` | `filter="Price gt 100"` | OData filter expression |
| `select` | `select="ID,Name,Price"` | Select specific fields |
| `expand` | `expand="Customer,Items"` | Expand navigation properties |
| `orderby` | `orderby="Name asc"` | Sort results |

## SAP OData V4 (RAP Services)

\`\`\`python
client = ODataClient(
    "https://sap-system.company.com:44300",
    username="user",
    password="pass",
    client="100"
)

# Simple query
response = client.get(
    service="zmy_product_api",
    entity="Products",
    version="v4",
    namespace="zsb_product_api",
    filter="ProductID eq '12345'"
)
# Raw V4: {"@odata.context": "...", "value": [...]}
products = client.get_value(response, "v4")

# Single entity by key
response = client.get(
    service="zmy_product_api",
    entity="Products('12345')",
    version="v4",
    namespace="zsb_product_api"
)
# Raw V4 single: {"@odata.context": "...", "ProductID": "12345", ...}
product = client.get_value(response, "v4")[0]

# Complex nested \$expand
response = client.get(
    service="zmy_order_api",
    entity="Orders",
    version="v4",
    namespace="zsb_order_api",
    filter="OrderID eq '12345'",
    expand="Customer(\$expand=Contacts),LineItems(\$expand=Product)"
)
orders = client.get_value(response, "v4")
for order in orders:
    print(f"Order: {order['OrderID']}")
    for line in order.get("LineItems", []):
        print(f"  Line Item: {line['ProductName']}")
\`\`\`

## SAP OData V2 (Gateway Services)

\`\`\`python
# Simple query
response = client.get(
    service="ZMY_SALESORDER_SRV",
    entity="SalesOrderSet",
    version="v2",
    top=10,
    filter="Status eq 'OPEN'"
)
# Raw V2: {"d": {"results": [...]}} or {"d": [...]}
orders = client.get_value(response, "v2")

# Single entity by key
response = client.get(
    service="ZMY_CUSTOMER_SRV",
    entity="CustomerSet(CustomerID='CUST001')",
    version="v2"
)
# Raw V2 single: {"d": {"CustomerID": "CUST001", ...}}
customer = client.get_value(response, "v2")[0]

# Complex nested \$expand (V2 style with /)
response = client.get(
    service="ZMY_ORDER_SRV",
    entity="OrderSet(OrderID='12345')",
    version="v2",
    expand="OrderToCustomer/CustomerToContacts,OrderToItems/ItemToProduct"
)
orders = client.get_value(response, "v2")
for order in orders:
    print(f"Order: {order['OrderID']}")
    for item in order.get("OrderToItems", {}).get("results", []):
        print(f"  Item: {item['ProductName']}")
\`\`\`

## Pagination

\`\`\`python
# V4 Pagination
response = client.get("zmy_service", "Products", version="v4", namespace="zsb_service", top=100)
all_items = client.get_value(response, "v4")

while next_link := client.get_next_link(response, "v4"):
    # Next link is a full URL, extract path for next call
    # Or use requests directly with next_link
    break  # Simplified example

# V2 Pagination
response = client.get("ZMY_SRV", "Products", version="v2", top=100)
all_items = client.get_value(response, "v2")

next_link = client.get_next_link(response, "v2")  # d.__next
\`\`\`

## Write Operations

\`\`\`python
# POST - Create
response = client.post(
    service="ZMY_SALESORDER_SRV",
    entity="SalesOrderSet",
    data={"CustomerID": "CUST001", "Amount": 1000},
    version="v2"
)

# PATCH - Update
client.patch(
    service="ZMY_SALESORDER_SRV",
    entity="SalesOrderSet('12345')",
    data={"Status": "APPROVED"},
    version="v2"
)

# DELETE
client.delete(
    service="ZMY_SALESORDER_SRV",
    entity="SalesOrderSet('12345')",
    version="v2"
)
\`\`\`

## Non-SAP OData Services

\`\`\`python
# Public OData services (Northwind, TripPin, etc.)
client = ODataClient("https://services.odata.org", sap_mode=False)

# V4 example
response = client.get("TripPinRESTierService", "People", top=3)
people = client.get_value(response, "v4")

# V2 example
response = client.get("V2/Northwind/Northwind.svc", "Products", version="v2", top=5)
products = client.get_value(response, "v2")
\`\`\`

## Error Handling

\`\`\`python
from sap_odata import ODataClient, ODataError, ODataConnectionError

try:
    response = client.get("zmy_service", "Products", version="v4", namespace="zsb_service")
except ODataError as e:
    # Validation errors (missing service, entity, namespace, invalid version)
    print(f"Validation error: {e}")
except ODataConnectionError as e:
    # Connection/network errors
    print(f"Connection error: {e}")
\`\`\`

### Validation Rules

| Error | Condition |
|-------|-----------|
| "Service name is required" | Empty service name |
| "Entity name is required" | Empty entity name |
| "Invalid version" | Version not 'v2' or 'v4' |
| "Namespace is required for SAP V4" | SAP V4 without namespace |

## Input Validation

\`\`\`python
# These raise ODataError with clear messages:

# Empty service
client.get("", "Products")  # ODataError: Service name is required

# Empty entity
client.get("ZMY_SRV", "")  # ODataError: Entity name is required

# Invalid version
client.get("ZMY_SRV", "Products", version="v3")  # ODataError: Invalid version

# SAP V4 without namespace
client.get("zmy_service", "Products", version="v4")  # ODataError: Namespace is required
\`\`\`

## Context Manager

\`\`\`python
with ODataClient("https://sap-system.com", username="user", password="pass") as client:
    response = client.get("ZMY_SRV", "Products", version="v2", top=10)
    products = client.get_value(response, "v2")
# Session is automatically closed
\`\`\`

## License

MIT License - see [LICENSE](LICENSE) file.
