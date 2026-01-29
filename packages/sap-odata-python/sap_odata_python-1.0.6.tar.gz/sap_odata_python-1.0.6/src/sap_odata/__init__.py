"""
SAP OData Python - A simple OData V2/V4 client library.

Example:
    >>> from sap_odata import ODataClient
    >>> client = ODataClient("https://services.odata.org", sap_mode=False)
    >>> response = client.get("V4/Northwind/Northwind.svc", "Products", top=5)
    >>> # V4 returns: {"@odata.context": "...", "value": [...]}
    >>> items = client.get_value(response, "v4")
    >>> for product in items:
    ...     print(product["ProductName"])
"""

__version__ = "1.0.6"
__author__ = "Vaibhav Goel"

from .client import ODataClient
from .exceptions import ODataError, ODataConnectionError, ODataAuthError

__all__ = ["ODataClient", "ODataError", "ODataConnectionError", "ODataAuthError"]
