from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
import xml.etree.ElementTree as ET
import uuid, html, datetime
from src.core.config import logging, settings

QBWC_USERNAME = settings.qbwc_username
QBWC_PASSWORD = settings.qbwc_password
ACTIVE_TICKETS = {}


# --- SOAP Parser (same as before) ---
def parse_soap_request(xml_string):
    try:
        namespaces = {
            'soap': settings.qbwc_soap_url,
            'qb': settings.qbwc_url
        }
        
        root = ET.fromstring(xml_string)
        body = root.find('soap:Body', namespaces)
        if body is None:
            raise ValueError("No <soap:Body> found")
            
        method_node = body[0]
        if method_node is None:
            raise ValueError("<soap:Body> is empty")

        method_name = method_node.tag.split('}')[-1]
        
        params = {}
        for child in method_node:
            param_name = child.tag.split('}')[-1]
            params[param_name] = child.text
            
        return method_name, params
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        return None, None

def wrap_soap_response(method_name, body_content):
    return f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
        <soap:Body>
            <{method_name}Response xmlns="http://developer.intuit.com/">
                {body_content}
            </{method_name}Response>
        </soap:Body>
    </soap:Envelope>
    """


# --- Your handler functions converted to async ---
async def handle_serverVersion():
    logging.info("QBWC: Called serverVersion")
    result_xml = "<serverVersionResult><string>1.0</string></serverVersionResult>"
    return wrap_soap_response("serverVersion", result_xml)

async def handle_clientVersion(params):
    logging.info(f"QBWC: Called clientVersion: {params.get('strVersion')}")
    result_xml = "<clientVersionResult><string></string></clientVersionResult>"
    return wrap_soap_response("clientVersion", result_xml)

async def handle_authenticate(sync_queue, params):
    username = params.get('strUserName')
    password = params.get('strPassword')
    
    logging.info(f"QBWC: Called authenticate with user: {username}")
    
    if username == QBWC_USERNAME and password == QBWC_PASSWORD:
        ticket = str(uuid.uuid4())

        ACTIVE_TICKETS[ticket] = {
            "sync_queue": sync_queue,
            "total_jobs": len(sync_queue),
            "jobs_done": 0
        }
        
        result_xml = f"""
        <authenticateResult>
            <string>{ticket}</string>
            <string></string>
        </authenticateResult>
        """
        logging.info(f"QBWC: Authentication Succeeded. {len(sync_queue)} jobs queued.")
    else:
        result_xml = f"""
        <authenticateResult>
            <string></string>
            <string>nvu</string>
        </authenticateResult>
        """
        logging.info("QBWC: Authentication FAILED.")
        
    return wrap_soap_response("authenticate", result_xml)

async def handle_sendRequestXML(params):
    ticket = params.get('ticket')
    session = ACTIVE_TICKETS.get(ticket)
    
    logging.info(f"QBWC: Called sendRequestXML")

    if not session:
        result_xml = "<sendRequestXMLResult><string>INVALID_TICKET</string></sendRequestXMLResult>"
        logging.info("QBWC: Invalid ticket.")
    elif session["sync_queue"]:
        job = session["sync_queue"].pop(0)
        job_type = job["type"]
        job_data = job["data"]
        request_id = f"{job_type}_{job['id']}"
        
        qbxml_request = ""
        
        if job_type == "customer":
            qbxml_request = create_customer_add_qbxml(job_data, request_id)
            logging.info(f"QBWC: Sending job: Add Customer {job_data['name']}")
        
        elif job_type == "employee":
            qbxml_request = create_employee_add_qbxml(job_data, request_id)
            logging.info(f"QBWC: Sending job: Add Employee {job_data['first_name']} {job_data['last_name']}")
        
        elif job_type == "invoice":
            qbxml_request = create_invoice_add_qbxml(job_data, request_id)
            logging.info(f"QBWC: Sending job: Add Invoice {job_data['id']} for {job_data['customer_name']}")

        elif job_type == "gl_entry":
            qbxml_request = create_journal_entry_add_qbxml(job_data, request_id)
            logging.info(f"QBWC: Sending job: Add Journal Entry {job_data['id']}")
        else:
            logging.info(f"QBWC: Unknown job type in queue: {job_type}")
        
        result_xml = f"<sendRequestXMLResult><string>{html.escape(qbxml_request)}</string></sendRequestXMLResult>"
    else:
        result_xml = "<sendRequestXMLResult><string></string></sendRequestXMLResult>"
        logging.info("QBWC: No more jobs to send.")
        
    return wrap_soap_response("sendRequestXML", result_xml)

async def handle_receiveResponseXML(params):
    ticket = params.get('ticket')
    response_xml = params.get('response')
    session = ACTIVE_TICKETS.get(ticket)
    
    logging.info(f"QBWC: Called receiveResponseXML")
    
    if not session:
        result_xml = "<receiveResponseXMLResult><int>-1</int></receiveResponseXMLResult>"
        logging.info("QBWC: Invalid ticket.")
    else:
        logging.info("----------------- RESPONSE FROM QUICKBOOKS -----------------")
        logging.info(response_xml)
        logging.info("------------------------------------------------------------")
        
        session["jobs_done"] += 1
        progress = 0
        if session["total_jobs"] > 0:
            progress = int((session["jobs_done"] / session["total_jobs"]) * 100)
        
        result_xml = f"<receiveResponseXMLResult><int>{progress}</int></receiveResponseXMLResult>"
        logging.info(f"QBWC: Job received. Progress: {progress}%")

    return wrap_soap_response("receiveResponseXML", result_xml)

async def handle_closeConnection(params):
    ticket = params.get('ticket')
    if ticket in ACTIVE_TICKETS:
        del ACTIVE_TICKETS[ticket]
    
    logging.info("QBWC: Called closeConnection. Session closed.")
    result_xml = "<closeConnectionResult><string>OK</string></closeConnectionResult>"
    return wrap_soap_response("closeConnection", result_xml)

async def handle_connectionError(params):
    ticket = params.get('ticket')
    message = params.get('message')
    logging.info(f"QBWC: Connection Error! Ticket: {ticket}, Message: {message}")
    result_xml = "<connectionErrorResult><string>OK</string></connectionErrorResult>"
    return wrap_soap_response("connectionError", result_xml)





# --- QBXML Generation Functions ---

def create_customer_add_qbxml(customer, request_id):
    """Converts a customer dictionary into a CustomerAddRq QBXML string."""
    name = html.escape(customer.get('name', ''))
    company = html.escape(customer.get('company', ''))
    email = html.escape(customer.get('email', ''))
    phone = html.escape(customer.get('phone', ''))

    qbxml = f"""
    <?xml version="1.0" encoding="utf-8"?>
    <?qbxml version="13.0"?>
    <QBXML>
        <QBXMLMsgsRq onError="stopOnError">
            <CustomerAddRq requestID="{request_id}">
                <CustomerAdd>
                    <Name>{name}</Name>
                    <CompanyName>{company}</CompanyName>
                    <Email>{email}</Email>
                    <Phone>{phone}</Phone>
                </CustomerAdd>
            </CustomerAddRq>
        </QBXMLMsgsRq>
    </QBXML>
    """
    return qbxml

def create_employee_add_qbxml(employee, request_id):
    """Converts an employee dictionary into an EmployeeAddRq QBXML string."""
    first_name = html.escape(employee.get('first_name', ''))
    last_name = html.escape(employee.get('last_name', ''))
    job_title = html.escape(employee.get('job_title', ''))

    qbxml = f"""
    <?xml version="1.0" encoding="utf-8"?>
    <?qbxml version="13.0"?>
    <QBXML>
        <QBXMLMsgsRq onError="stopOnError">
            <EmployeeAddRq requestID="{request_id}">
                <EmployeeAdd>
                    <FirstName>{first_name}</FirstName>
                    <LastName>{last_name}</LastName>
                    <JobTitle>{job_title}</JobTitle>
                </EmployeeAdd>
            </EmployeeAddRq>
        </QBXMLMsgsRq>
    </QBXML>
    """
    return qbxml

def create_invoice_add_qbxml(invoice, request_id):
    """Converts an invoice dictionary into an InvoiceAddRq QBXML string."""
    customer_name = html.escape(invoice.get('customer_name', ''))
    txn_date = html.escape(invoice.get('txn_date', datetime.date.today().isoformat()))
    
    # Build the line items
    line_items_xml = ""
    for line in invoice.get('lines', []):
        item_name = html.escape(line.get('item_name', ''))
        desc = html.escape(line.get('desc', ''))
        quantity = line.get('quantity', 0)
        rate = line.get('rate', 0.0)
        
        line_items_xml += f"""
        <InvoiceLineAdd>
            <ItemRef><FullName>{item_name}</FullName></ItemRef>
            <Desc>{desc}</Desc>
            <Quantity>{quantity}</Quantity>
            <Rate>{rate}</Rate>
        </InvoiceLineAdd>
        """

    qbxml = f"""
    <?xml version="1.0" encoding="utf-8"?>
    <?qbxml version="13.0"?>
    <QBXML>
        <QBXMLMsgsRq onError="stopOnError">
            <InvoiceAddRq requestID="{request_id}">
                <InvoiceAdd>
                    <CustomerRef><FullName>{customer_name}</FullName></CustomerRef>
                    <TxnDate>{txn_date}</TxnDate>
                    {line_items_xml}
                </InvoiceAdd>
            </InvoiceAddRq>
        </QBXMLMsgsRq>
    </QBXML>
    """
    return qbxml

def create_journal_entry_add_qbxml(entry, request_id):
    """Converts a GL entry dictionary into a JournalEntryAddRq QBXML string."""
    txn_date = html.escape(entry.get('txn_date', datetime.date.today().isoformat()))
    memo = html.escape(entry.get('memo', ''))
    
    lines_xml = ""
    # Add Debit Lines
    for line in entry.get('debit_lines', []):
        account_name = html.escape(line.get('account_name', ''))
        amount = line.get('amount', 0.0)
        line_memo = html.escape(line.get('memo', ''))
        lines_xml += f"""
        <JournalDebitLine>
            <AccountRef><FullName>{account_name}</FullName></AccountRef>
            <Amount>{amount}</Amount>
            <Memo>{line_memo}</Memo>
        </JournalDebitLine>
        """

    # Add Credit Lines
    for line in entry.get('credit_lines', []):
        account_name = html.escape(line.get('account_name', ''))
        amount = line.get('amount', 0.0)
        line_memo = html.escape(line.get('memo', ''))
        lines_xml += f"""
        <JournalCreditLine>
            <AccountRef><FullName>{account_name}</FullName></AccountRef>
            <Amount>{amount}</Amount>
            <Memo>{line_memo}</Memo>
        </JournalCreditLine>
        """

    qbxml = f"""
    <?xml version="1.0" encoding="utf-8"?>
    <?qbxml version="13.0"?>
    <QBXML>
        <QBXMLMsgsRq onError="stopOnError">
            <JournalEntryAddRq requestID="{request_id}">
                <JournalEntryAdd>
                    <TxnDate>{txn_date}</TxnDate>
                    <Memo>{memo}</Memo>
                    {lines_xml}
                </JournalEntryAdd>
            </JournalEntryAddRq>
        </QBXMLMsgsRq>
    </QBXML>
    """
    return qbxml
