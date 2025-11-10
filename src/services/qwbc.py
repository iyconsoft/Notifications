from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
import xml.etree.ElementTree as ET
import uuid, html, datetime, csv, os, time
from src.core.config import logger as logging, settings

QBWC_USERNAME = settings.qbwc_username
QBWC_PASSWORD = settings.qbwc_password
ACTIVE_TICKETS = {}
LOG_FILE = 'sync_log.csv'
LOG_FIELDS = ['Module', 'date', 'status', 'payload', 'error', 'duration']
MAX_RETRIES = 2


# --- Logging Function ---
def write_to_log(log_data):
    """Appends a new record to the CSV log file."""
    try:
        # Check if file exists to write headers
        file_exists = os.path.exists(LOG_FILE)
        
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(log_data)
            
    except Exception as e:
        logging.info(f"CRITICAL: Failed to write to log file {LOG_FILE}: {e}")

# --- QBXML Response Parser ---
def parse_qb_response(response_xml):
    """
    Parses the response XML from QuickBooks to find the status code and message.
    Returns: {"status": "Success" | "Failed", "message": "..."}
    """
    if not response_xml:
        return {"status": "Failed", "message": "Empty response from QuickBooks."}
        
    try:
        root = ET.fromstring(response_xml)
        
        # Find the ...Rs (response) tag. It's usually the first child of QBXMLMsgsRs.
        msgs_rs_node = root.find(".//QBXMLMsgsRs")
        if msgs_rs_node is None:
             # Find a single response, e.g. CustomerAddRs
            response_node = root.find(".//*[contains(name(), 'Rs')]")
            if response_node is None:
                # Fallback for simple responses
                response_node = root
        else:
             response_node = msgs_rs_node[0]

        if response_node is not None:
            status_code = response_node.attrib.get('statusCode', '-1')
            status_message = response_node.attrib.get('statusMessage', 'Unknown error')
            
            if status_code == "0":
                return {"status": "Success", "message": "OK"}
            else:
                return {"status": "Failed", "message": f"Code {status_code}: {status_message}"}
        else:
            return {"status": "Failed", "message": "Could not parse response XML structure."}

    except ET.ParseError as e:
        return {"status": "Failed", "message": f"XML Parse Error: {e}"}
    except Exception as e:
         return {"status": "Failed", "message": f"General parsing error: {e}"}

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
            params[child.tag.split('}')[-1]] = child.text
            
        return method_name, params
    except ET.ParseError as e:
        logging.info(f"XML Parse Error: {e}")
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
            "jobs_done": 0,
            "current_job": None
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
        logging.error("QBWC: Authentication FAILED.")
        
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
        request_id = f"{job_type}_{job['id']}_retry{job['retries']}"
        
        qbxml_request = ""
        
        if job_type == "customers":
            qbxml_request = create_customer_add_qbxml(job_data, request_id)
            logging.info(f"QBWC: Sending job: Add Customer {job_data['name']}")
        
        elif job_type == "employees":
            qbxml_request = create_employee_add_qbxml(job_data, request_id)
            logging.info(f"QBWC: Sending job: Add Employee {job_data['first_name']}")
        
        elif job_type == "invoices":
            qbxml_request = create_invoice_add_qbxml(job_data, request_id)
            logging.info(f"QBWC: Sending job: Add Invoice {job_data['id']} for {job_data['customer_name']}")

        elif job_type == "gl_entries":
            qbxml_request = create_journal_entry_add_qbxml(job_data, request_id)
            logging.info(f"QBWC: Sending job: Add Journal Entry {job_data['id']}")
        else:
            logging.info(f"QBWC: Unknown job type in queue: {job_type}")

        # Store the job we are about to send
        session["current_job"] = {
            "job": job,
            "start_time": time.time(),
            "request_xml": qbxml_request
        }
        
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
        return wrap_soap_response("receiveResponseXML", result_xml)

    # Get the job that this response is for
    pending_job = session.get("current_job")
    if not pending_job:
            logging.info("QBWC: Received a response but had no job in progress. Ignoring.")
            result_xml = "<receiveResponseXMLResult><int>0</int></receiveResponseXMLResult>"
            return wrap_soap_response("receiveResponseXML", result_xml)

    job = pending_job["job"]
    duration = end_time - pending_job["start_time"]
    
    # Parse the response to see if it was a success or failure
    qb_status = parse_qb_response(response_xml)
    status = qb_status["status"]
    error_message = qb_status["message"]
    log_status = status # Default log status
    
    if status == "Failed":
        logging.info(f"QBWC: Job {job['type']} {job['id']} FAILED. Reason: {error_message}")
        if job["retries"] < MAX_RETRIES:
            job["retries"] += 1
            session["sync_queue"].insert(0, job) # Add back to front of queue
            log_status = f"Failed (Retrying {job['retries']}/{MAX_RETRIES})"
            logging.info(f"QBWC: ...retrying job. Attempt {job['retries']}.")
        else:
            log_status = "Failed (Aborted)"
            session["jobs_done"] += 1 # Job is now "done" (by failing)
            logging.info(f"QBWC: ...max retries reached. Aborting job.")
    else:
        logging.info("----------------- RESPONSE FROM QUICKBOOKS -----------------")
        logging.info(response_xml)
        logging.info("------------------------------------------------------------")
        
        session["jobs_done"] += 1
        logging.info(f"QBWC: Job {job['type']} {job['id']} Succeeded.")
        # Write the detailed log
        log_data = {
            "Module": job["type"],
            "date": datetime.datetime.now().isoformat(),
            "status": log_status,
            "payload": pending_job["request_xml"],
            "error": error_message if status == "Failed" else "",
            "duration": f"{duration:.2f}s"
        }
        write_to_log(log_data)
        
        # Clear the in-flight job
        session["current_job"] = None
        
        # Calculate progress
        progress = 0
        if session["total_jobs"] > 0:
             progress = int((session["jobs_done"] / session["total_jobs"]) * 100)
        
        result_xml = f"<receiveResponseXMLResult><int>{progress}</int></receiveResponseXMLResult>"
        logging.info(f"QBWC: Progress: {progress}%")

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
    hresult = params.get('hresult')
    error_message = f"HRESULT: {hresult}, Message: {message}"
    logging.info(f"QBWC: Connection Error! {error_message}")

    # Log this connection error
    log_data = {
        "Module": "Connection",
        "date": datetime.datetime.now().isoformat(),
        "status": "Failed",
        "payload": "",
        "error": error_message,
        "duration": "0.00s"
    }
    write_to_log(log_data)

    # Reschedule the in-flight job if there was one
    if ticket in ACTIVE_TICKETS:
        session = ACTIVE_TICKETS[ticket]
        if session.get("current_job"):
            job = session["current_job"]["job"]
            session["sync_queue"].insert(0, job) # Add back to front
            session["current_job"] = None
            logging.info(f"QBWC: Rescheduling in-flight job {job['type']} {job['id']} due to connection error.")
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
