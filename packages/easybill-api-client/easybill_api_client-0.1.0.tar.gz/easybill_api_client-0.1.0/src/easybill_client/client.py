"""
Easybill REST API Client.

Wrapper around the easybill-rest library.

Example:
    from easybill_client import EasybillClient

    with EasybillClient(api_key="xxx") as client:
        customers = client.get_customers()
        invoices = client.get_invoices(year=2025)
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any

from easybill_rest import Client

from .models import (
    EasybillCustomer,
    EasybillDocument,
    EasybillDocumentItem,
    EasybillProject,
)

logger = logging.getLogger(__name__)

# Document types
DOC_TYPE_INVOICE = "INVOICE"
DOC_TYPE_CREDIT = "CREDIT"
DOC_TYPE_OFFER = "OFFER"
DOC_TYPE_ORDER = "ORDER"
DOC_TYPE_RECURRING = "RECURRING"


# === Exceptions ===


class EasybillError(Exception):
    """Base exception for Easybill errors."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class EasybillAuthenticationError(EasybillError):
    """Authentication error."""

    pass


class EasybillRateLimitError(EasybillError):
    """Rate limit exceeded."""

    pass


class EasybillNotFoundError(EasybillError):
    """Resource not found."""

    pass


# === Client ===


class EasybillClient:
    """
    Python client for the Easybill REST API.

    Args:
        api_key: Easybill API Key (from profile & settings)
        timeout: Request timeout in seconds (default: 30)

    Example:
        client = EasybillClient(api_key="your-api-key")

        # Get customers
        customers = client.get_customers()

        # Get invoices for a year
        invoices = client.get_invoices(year=2025)
    """

    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self._client = Client(api_key, timeout=timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    # === Customers ===

    def get_customers(self, limit: int = 1000) -> list[EasybillCustomer]:
        """
        Get all customers from Easybill.

        Args:
            limit: Maximum number per request (max 1000)

        Returns:
            List of EasybillCustomer objects
        """
        logger.info("Loading Easybill customers...")
        customers = []
        page = 1

        while True:
            try:
                response = self._client.customers().get_customers(params={"limit": limit, "page": page})
            except Exception as e:
                raise EasybillError(f"Error loading customers: {e}")

            items = response.get("items", [])
            if not items:
                break

            for data in items:
                customer = self._parse_customer(data)
                customers.append(customer)

            page += 1
            total_pages = response.get("pages", 1)
            if page > total_pages:
                break

        logger.info(f"Easybill: {len(customers)} customers loaded")
        return customers

    def get_customer(self, customer_id: int) -> EasybillCustomer:
        """
        Get a single customer.

        Args:
            customer_id: Easybill customer ID

        Returns:
            EasybillCustomer object
        """
        try:
            data = self._client.customers().get_customer(str(customer_id))
            return self._parse_customer(data)
        except Exception as e:
            if "404" in str(e):
                raise EasybillNotFoundError(f"Customer {customer_id} not found")
            raise EasybillError(f"Error loading customer: {e}")

    @staticmethod
    def _to_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
        """Safely convert a value to Decimal."""
        if value is None:
            return default
        try:
            return Decimal(str(value))
        except Exception:
            return default

    def _parse_customer(self, data: dict[str, Any]) -> EasybillCustomer:
        """Parse customer data from API response."""
        emails = []
        for i in range(1, 4):
            email = data.get(f"emails_{i}")
            if email:
                emails.append(email)

        return EasybillCustomer(
            id=data.get("id", 0),
            number=data.get("number"),
            company_name=data.get("company_name"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            emails=emails,
            street=data.get("street"),
            zip_code=data.get("zip_code"),
            city=data.get("city"),
            country=data.get("country"),
            vat_identifier=data.get("vat_identifier"),
            payment_options=data.get("payment_options"),
        )

    # === Documents ===

    def get_documents(
        self,
        document_type: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        customer_id: int | None = None,
        status: str | None = None,
        limit: int = 1000,
    ) -> list[EasybillDocument]:
        """
        Get documents from Easybill.

        Args:
            document_type: Document type (INVOICE, CREDIT, OFFER, ORDER, RECURRING)
            start_date: Start date for filter (document_date)
            end_date: End date for filter (document_date)
            customer_id: Only documents for this customer
            status: Document status (DONE, CANCEL, etc.)
            limit: Maximum number per request (max 1000)

        Returns:
            List of EasybillDocument objects
        """
        logger.info(f"Loading Easybill documents (type: {document_type or 'all'})...")
        documents = []
        page = 1

        params: dict[str, Any] = {"limit": limit}
        if document_type:
            params["type"] = document_type
        if start_date:
            params["document_date"] = f"{start_date.isoformat()},{end_date.isoformat() if end_date else ''}"
        if customer_id:
            params["customer_id"] = customer_id
        if status:
            params["status"] = status

        while True:
            params["page"] = page
            try:
                response = self._client.documents().get_documents(params=params)
            except Exception as e:
                raise EasybillError(f"Error loading documents: {e}")

            items = response.get("items", [])
            if not items:
                break

            for data in items:
                document = self._parse_document(data)
                documents.append(document)

            page += 1
            total_pages = response.get("pages", 1)
            if page > total_pages:
                break

        logger.info(f"Easybill: {len(documents)} documents loaded")
        return documents

    def get_invoices(
        self,
        year: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        customer_id: int | None = None,
    ) -> list[EasybillDocument]:
        """
        Get invoices from Easybill.

        Args:
            year: Year for filter (alternative to start_date/end_date)
            start_date: Start date for filter
            end_date: End date for filter
            customer_id: Only invoices for this customer

        Returns:
            List of EasybillDocument objects (only INVOICE type)
        """
        if year and not start_date:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)

        return self.get_documents(
            document_type=DOC_TYPE_INVOICE,
            start_date=start_date,
            end_date=end_date,
            customer_id=customer_id,
        )

    def get_document(self, document_id: int, with_items: bool = True) -> EasybillDocument:
        """
        Get a single document.

        Args:
            document_id: Easybill document ID
            with_items: Load line items

        Returns:
            EasybillDocument object
        """
        try:
            data = self._client.documents().get_document(str(document_id))
            return self._parse_document(data, with_items=with_items)
        except Exception as e:
            if "404" in str(e):
                raise EasybillNotFoundError(f"Document {document_id} not found")
            raise EasybillError(f"Error loading document: {e}")

    def get_document_pdf(self, document_id: int) -> bytes:
        """
        Download the PDF of a document.

        Args:
            document_id: Easybill document ID

        Returns:
            PDF as bytes
        """
        try:
            return self._client.documents().download_document_as_pdf(str(document_id))
        except Exception as e:
            if "404" in str(e):
                raise EasybillNotFoundError(f"Document {document_id} not found")
            raise EasybillError(f"Error loading PDF: {e}")

    def _parse_document(self, data: dict[str, Any], with_items: bool = True) -> EasybillDocument:
        """Parse document data from API response."""
        items = []
        if with_items and "items" in data:
            for item_data in data.get("items", []):
                items.append(
                    EasybillDocumentItem(
                        id=item_data.get("id"),
                        number=item_data.get("number"),
                        description=item_data.get("description"),
                        quantity=self._to_decimal(item_data.get("quantity"), Decimal("1")),
                        unit=item_data.get("unit"),
                        single_price_net=self._to_decimal(item_data.get("single_price_net"), Decimal("0")),
                        total_price_net=self._to_decimal(item_data.get("total_price_net"), Decimal("0")),
                        vat_percent=self._to_decimal(item_data.get("vat_percent"), Decimal("19")),
                        position_kind=item_data.get("position_kind"),
                    )
                )

        # Parse dates
        doc_date = data.get("document_date")
        if isinstance(doc_date, str):
            doc_date = date.fromisoformat(doc_date)

        due_date = data.get("due_date")
        if isinstance(due_date, str):
            due_date = date.fromisoformat(due_date)

        paid_at = data.get("paid_at")
        if isinstance(paid_at, str):
            paid_at = date.fromisoformat(paid_at.split("T")[0])

        return EasybillDocument(
            id=data.get("id", 0),
            number=data.get("number"),
            document_date=doc_date,
            due_date=due_date,
            type=data.get("type", "INVOICE"),
            status=data.get("status"),
            customer_id=data.get("customer_id"),
            project_id=data.get("project_id"),
            amount_net=self._to_decimal(data.get("amount_net")),
            amount_gross=self._to_decimal(data.get("amount_gross")),
            amount=self._to_decimal(data.get("amount")),
            currency=data.get("currency", "EUR"),
            is_draft=data.get("is_draft", False),
            paid_at=paid_at,
            title=data.get("title"),
            text=data.get("text"),
            text_prefix=data.get("text_prefix"),
            items=items,
        )

    # === Projects ===

    def get_projects(self, customer_id: int | None = None, limit: int = 1000) -> list[EasybillProject]:
        """
        Get projects from Easybill.

        Args:
            customer_id: Only projects for this customer
            limit: Maximum number per request

        Returns:
            List of EasybillProject objects
        """
        logger.info("Loading Easybill projects...")
        projects = []
        page = 1

        params: dict[str, Any] = {"limit": limit}
        if customer_id:
            params["customer_id"] = customer_id

        while True:
            params["page"] = page
            try:
                response = self._client.projects().get_projects(params=params)
            except Exception as e:
                raise EasybillError(f"Error loading projects: {e}")

            items = response.get("items", [])
            if not items:
                break

            for data in items:
                project = EasybillProject(
                    id=data.get("id", 0),
                    name=data.get("name", ""),
                    status=data.get("status"),
                    customer_id=data.get("customer_id"),
                    budget_amount=Decimal(str(data.get("budget_amount", 0))) if data.get("budget_amount") else None,
                    budget_time=data.get("budget_time"),
                    consumed_amount=Decimal(str(data.get("consumed_amount", 0))) if data.get("consumed_amount") else None,
                    consumed_time=data.get("consumed_time"),
                )
                projects.append(project)

            page += 1
            total_pages = response.get("pages", 1)
            if page > total_pages:
                break

        logger.info(f"Easybill: {len(projects)} projects loaded")
        return projects
