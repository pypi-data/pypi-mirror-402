"""
Pydantic Models for Easybill API data.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class EasybillCustomer(BaseModel):
    """Customer from Easybill."""

    id: int
    number: str | None = None
    company_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    emails: list[str] = Field(default_factory=list)
    street: str | None = None
    zip_code: str | None = None
    city: str | None = None
    country: str | None = None
    vat_identifier: str | None = None
    payment_options: int | None = None

    @property
    def display_name(self) -> str:
        """Display name for the customer."""
        if self.company_name:
            return self.company_name
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.number or f"Customer {self.id}"

    @property
    def primary_email(self) -> str | None:
        """Primary email address."""
        return self.emails[0] if self.emails else None


class EasybillDocumentItem(BaseModel):
    """Single line item in a document."""

    id: int | None = None
    number: str | None = None
    description: str | None = None
    quantity: Decimal = Decimal("1")
    unit: str | None = None
    single_price_net: Decimal = Decimal("0")  # in cents
    total_price_net: Decimal = Decimal("0")  # in cents
    vat_percent: Decimal = Decimal("19")
    position_kind: str | None = None  # POSITION, TEXT, etc.


class EasybillDocument(BaseModel):
    """Document (invoice, credit note, etc.) from Easybill."""

    id: int
    number: str | None = None
    document_date: date | None = None
    due_date: date | None = None
    type: str  # INVOICE, CREDIT, OFFER, ORDER, etc.
    status: str | None = None  # DONE, CANCEL, etc.
    customer_id: int | None = None
    project_id: int | None = None

    # Amounts in cents
    amount_net: Decimal = Decimal("0")
    amount_gross: Decimal = Decimal("0")
    amount: Decimal = Decimal("0")  # Total amount
    currency: str = "EUR"

    # Payment status
    is_draft: bool = False
    paid_at: date | None = None

    # Additional info
    title: str | None = None
    text: str | None = None
    text_prefix: str | None = None

    items: list[EasybillDocumentItem] = Field(default_factory=list)

    @property
    def amount_net_eur(self) -> Decimal:
        """Net amount in EUR (converted from cents)."""
        return self.amount_net / 100

    @property
    def amount_gross_eur(self) -> Decimal:
        """Gross amount in EUR (converted from cents)."""
        gross = self.amount_gross if self.amount_gross else self.amount
        return gross / 100

    @property
    def is_paid(self) -> bool:
        """Is the document paid?"""
        return self.paid_at is not None

    @property
    def first_item_description(self) -> str | None:
        """Description of the first line item (as title fallback)."""
        if self.items:
            desc = self.items[0].description
            if desc:
                first_line = desc.split("\n")[0].strip()
                return first_line[:100] if len(first_line) > 100 else first_line
        return None


class EasybillProject(BaseModel):
    """Project from Easybill (for invoice project assignment)."""

    id: int
    name: str
    status: str | None = None  # OPEN, DONE, CANCEL
    customer_id: int | None = None
    budget_amount: Decimal | None = None
    budget_time: int | None = None  # in minutes
    consumed_amount: Decimal | None = None
    consumed_time: int | None = None
