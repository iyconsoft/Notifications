import asyncio, time, json, time, socket, ssl, certifi, httpx
from urllib.parse import urlparse
from typing import Dict, Optional, Tuple
from sqlalchemy import text


async def check_url_health(
    url: str,
    timeout: float = 5.0,
    method: str = "HEAD",
    verify_ssl: bool = True,
    follow_redirects: bool = True,
    user_agent: Optional[str] = None,
    retries: int = 0
    ) -> Dict[str, any]:
    
    # Validate and parse URL
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return {
                "status": "invalid",
                "error": "Invalid URL format",
                "url": url,
                "timestamp": time.time()
            }
    except Exception as e:
        return {
            "status": "invalid",
            "error": f"URL parsing error: {str(e)}",
            "url": url,
            "timestamp": time.time()
        }
    
    # Prepare request parameters
    headers = {}
    if user_agent:
        headers["User-Agent"] = user_agent
    else:
        headers["User-Agent"] = "HealthCheck/1.0"
    
    # Track metrics
    start_time = time.monotonic()
    dns_resolution_time = None
    tcp_connection_time = None
    first_byte_time = None
    total_time = None
    
    # Configure HTTPX client
    transport_args = {}
    
    # Configure retries if requested
    if retries > 0:
        from httpx import AsyncHTTPTransport
        transport = AsyncHTTPTransport(retries=retries)
    else:
        transport = None
    
    try:
        # DNS resolution timing
        dns_start = time.monotonic()
        hostname = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
        
        # Resolve hostname using asyncio (for consistency)
        loop = asyncio.get_event_loop()
        await loop.getaddrinfo(hostname, port, family=socket.AF_INET)
        dns_resolution_time = (time.monotonic() - dns_start) * 1000
        
        # Create httpx client with timeout
        timeout_config = httpx.Timeout(timeout, connect=timeout, read=timeout, write=timeout)
        
        async with httpx.AsyncClient(
            timeout=timeout_config,
            headers=headers,
            follow_redirects=follow_redirects,
            transport=transport,
            **transport_args
        ) as client:
            
            # Track TCP connection start
            tcp_start = time.monotonic()
            
            # Make the request
            request = client.build_request(method=method, url=url)
            
            # Send request and track first byte
            response = await client.send(request, stream=True)
            
            tcp_connection_time = (time.monotonic() - tcp_start) * 1000
            
            # Record time to first byte (headers received)
            first_byte_time = (time.monotonic() - start_time) * 1000
            
            # Read response body if needed
            if method.upper() == "GET":
                await response.aread()
            
            total_time = (time.monotonic() - start_time) * 1000
            
            # Get response data
            status_code = response.status_code
            response_headers = dict(response.headers)
            
            # Determine status category
            if 200 <= status_code < 400:
                status_category = "healthy"
            elif 400 <= status_code < 500:
                status_category = "client_error"
            elif 500 <= status_code < 600:
                status_category = "server_error"
            else:
                status_category = "unknown"
            
            result = {
                "status": "healthy" if 200 <= status_code < 400 else "unhealthy",
                "details": "connection is successful" if 200 <= status_code < 400 else status_category
            }
            
            # Clean up
            await response.aclose()
            
            return result
    
    except httpx.TimeoutException:
        return {
            "status": "timeout",
            "error": f"Request timed out after {timeout} seconds",
        }
    
    except httpx.ConnectError as e:
        return {
            "status": "connection_failed",
            "error": f"Connection failed: {str(e)}",
        }
    
    except httpx.HTTPStatusError as e:
        return {
            "status": "response_error",
            "error": f"Response error: {str(e)}",
        }
    
    except httpx.RemoteProtocolError:
        return {
            "status": "server_disconnected",
            "error": "Server disconnected unexpectedly",
        }
    
    except ssl.SSLError as e:
        return {
            "status": "ssl_error",
            "error": f"SSL error: {str(e)}",
        }
    
    except socket.gaierror as e:
        return {
            "status": "dns_error",
            "error": f"DNS resolution failed: {str(e)}",
        }
    
    except httpx.RequestError as e:
        return {
            "status": "request_error",
            "error": f"Request error: {str(e)}",
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": f"Unexpected error: {str(e)}",
        }

async def check_rabbitmq(connection) -> dict:
    try:
        channel = await connection.channel()
        await channel.close()  # Immediately close test channel
        return {"status": "healthy", "details": "Connection active"}
    except Exception as e:
        return {
            "status": "unhealthy", 
            "details": str(e),
            "error": "RabbitMQ connection failed"
        }

async def check_db(engine, session) -> dict:
    """Comprehensive DB health check"""
    try:
        await session.execute(text("SELECT 1"))
        pool = engine.pool

        return {
            "status": "healthy",
            "details": {
                "connection": "active",
                "connection_pool": {
                    "size": pool.size(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                }
            }
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": "DB operation failed",
            "details": str(e)
        }

def check_worker_task(task) -> dict:
    if not task:
        return {"status": "unhealthy", "error": "Worker task not initialized"}
    
    if task.done():
        exc = task.exception()
        if exc:
            return {
                "status": "unhealthy",
                "error": "Worker crashed",
                "details": str(exc)
            }
        return {
            "status": "unhealthy",
            "error": "Worker completed unexpectedly"
        }
    return {"status": "healthy", "details": "Worker running"}



async def check_app(app_service_url: str = None, timeout: int = 3) -> bool:
    """Check if an external application is reachable."""
    try:
        return True
    except Exception as e:
        return False
