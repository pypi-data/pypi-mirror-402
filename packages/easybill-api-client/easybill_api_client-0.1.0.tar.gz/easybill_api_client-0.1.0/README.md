# Easybill API Client

Python client for the [Easybill REST API](https://www.easybill.de/api/).

## Installation

```bash
pip install easybill-api-client
```

## Usage

```python
from easybill_client import EasybillClient

with EasybillClient(api_key="your-api-key") as client:
    # Get all customers
    customers = client.get_customers()

    # Get invoices for a year
    invoices = client.get_invoices(year=2025)

    # Get all documents
    documents = client.get_documents()

    # Get projects
    projects = client.get_projects()
```

## API

### EasybillClient

- `get_customers(limit=1000)` - Get all customers
- `get_customer(customer_id)` - Get single customer
- `get_documents(document_type, start_date, end_date, customer_id, status, limit)` - Get documents
- `get_invoices(year, start_date, end_date, customer_id)` - Get invoices
- `get_document(document_id, with_items=True)` - Get single document
- `get_document_pdf(document_id)` - Download document PDF
- `get_projects(customer_id, limit)` - Get projects

### Document Types

```python
from easybill_client import DOC_TYPE_INVOICE, DOC_TYPE_CREDIT, DOC_TYPE_OFFER, DOC_TYPE_ORDER, DOC_TYPE_RECURRING
```

### Exceptions

- `EasybillError` - Base exception
- `EasybillAuthenticationError` - Authentication failed
- `EasybillRateLimitError` - Rate limit exceeded
- `EasybillNotFoundError` - Resource not found

### Models

- `EasybillCustomer` - Customer data
- `EasybillDocument` - Invoice/document data
- `EasybillDocumentItem` - Line item in document
- `EasybillProject` - Project data

## License

MIT
