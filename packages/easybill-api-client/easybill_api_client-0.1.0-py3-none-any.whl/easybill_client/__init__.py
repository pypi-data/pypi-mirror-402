"""
Easybill REST API Client.

Example:
    from easybill_client import EasybillClient

    with EasybillClient(api_key="xxx") as client:
        customers = client.get_customers()
        invoices = client.get_invoices(year=2025)
"""

from .client import (
    DOC_TYPE_CREDIT,
    DOC_TYPE_INVOICE,
    DOC_TYPE_OFFER,
    DOC_TYPE_ORDER,
    DOC_TYPE_RECURRING,
    EasybillAuthenticationError,
    EasybillClient,
    EasybillError,
    EasybillNotFoundError,
    EasybillRateLimitError,
)
from .models import (
    EasybillCustomer,
    EasybillDocument,
    EasybillDocumentItem,
    EasybillProject,
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "EasybillClient",
    # Exceptions
    "EasybillError",
    "EasybillAuthenticationError",
    "EasybillRateLimitError",
    "EasybillNotFoundError",
    # Models
    "EasybillCustomer",
    "EasybillDocument",
    "EasybillDocumentItem",
    "EasybillProject",
    # Constants
    "DOC_TYPE_INVOICE",
    "DOC_TYPE_CREDIT",
    "DOC_TYPE_OFFER",
    "DOC_TYPE_ORDER",
    "DOC_TYPE_RECURRING",
]
