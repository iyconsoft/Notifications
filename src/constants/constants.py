CUSTOMERS_TO_SYNC = [
    {"id": "C1001", "name": "John Doe", "email": "john.doe@example.com", "phone": "555-1234"},
    {"id": "C1002", "name": "Jane Smith", "email": "jane.smith@example.com", "company": "Smith Co."}
]

# Employees
EMPLOYEES_TO_SYNC = [
    {"id": "E101", "first_name": "Sarah", "last_name": "Jenkins", "job_title": "Developer"},
    {"id": "E102", "first_name": "Mike", "last_name": "Brown", "job_title": "Sales Rep"}
]

# Invoices
# **ASSUMPTION**: The Customer 'FullName' (e.g., "John Doe") already exists or is
#                 being added in this batch (which it is).
# **ASSUMPTION**: The Item 'FullName' (e.g., "Services") ALREADY EXISTS in your
#                 QuickBooks Item List. This is critical.

INVOICES_TO_SYNC = [
    {
        "id": "INV-001",
        "customer_name": "John Doe", # Must match a customer's 'Name'
        "txn_date": "2024-10-25",
        "lines": [
            {"item_name": "Services", "desc": "Web Development", "quantity": 10, "rate": 150.00},
            {"item_name": "Services", "desc": "Consulting", "quantity": 2, "rate": 200.00}
        ]
    }
]

# "General Ledger" is a "Journal Entry" in QuickBooks
# **ASSUMPTION**: The Accounts 'FullName' (e.g., "Checking", "Office Expenses")
#                 ALREADY EXIST in your QuickBooks Chart of Accounts.
# The total of debits MUST equal the total of credits.

GL_ENTRIES_TO_SYNC = [
    {
        "id": "GL-001",
        "txn_date": "2024-10-25",
        "memo": "Monthly office supplies",
        "debit_lines": [
            {"account_name": "Office Expenses", "amount": 250.00, "memo": "Pens and paper"}
        ],
        "credit_lines": [
            {"account_name": "Checking", "amount": 250.00, "memo": "Paid from main account"}
        ]
    }
]

