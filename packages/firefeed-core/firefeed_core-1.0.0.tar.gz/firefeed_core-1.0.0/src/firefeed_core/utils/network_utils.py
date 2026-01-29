"""
Network Utilities

Common network utilities for FireFeed microservices.
"""

import asyncio
import logging
import socket
import ssl
import urllib.request
import urllib.error
from typing import Optional, Union, Dict, Any, List
import aiohttp
import httpx
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


async def make_request(
    url: str,
    method: str = 'GET',
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Union[Dict, str, bytes]] = None,
    timeout: int = 30,
    ssl_verify: bool = True,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Make HTTP request with retry logic.
    
    Args:
        url: Request URL
        method: HTTP method
        headers: Request headers
        data: Request data
        timeout: Request timeout in seconds
        ssl_verify: Verify SSL certificate
        max_retries: Maximum number of retries
        
    Returns:
        Response dictionary with status, headers, and content
    """
    headers = headers or {}
    headers.setdefault('User-Agent', 'FireFeed-Core/1.0')
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    ssl=None if ssl_verify else False
                ) as response:
                    content = await response.read()
                    
                    return {
                        'status': response.status,
                        'headers': dict(response.headers),
                        'content': content,
                        'url': str(response.url)
                    }
                    
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Request failed after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Request attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff


def download_file(
    url: str,
    destination: str,
    timeout: int = 30,
    chunk_size: int = 8192,
    ssl_verify: bool = True
) -> bool:
    """
    Download file from URL.
    
    Args:
        url: File URL
        destination: Local file path
        timeout: Download timeout in seconds
        chunk_size: Download chunk size
        ssl_verify: Verify SSL certificate
        
    Returns:
        True if download successful, False otherwise
    """
    try:
        # Configure SSL context
        context = None
        if not ssl_verify:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        # Create request
        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'FireFeed-Core/1.0')
        
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            with open(destination, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
        
        return True
        
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return False


def check_url_availability(
    url: str,
    timeout: int = 10,
    ssl_verify: bool = True
) -> bool:
    """
    Check if URL is available.
    
    Args:
        url: URL to check
        timeout: Check timeout in seconds
        ssl_verify: Verify SSL certificate
        
    Returns:
        True if URL is available, False otherwise
    """
    try:
        # Configure SSL context
        context = None
        if not ssl_verify:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        # Create request
        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'FireFeed-Core/1.0')
        
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            return response.status == 200
            
    except Exception as e:
        logger.debug(f"URL check failed: {e}")
        return False


def get_content_type(url: str, timeout: int = 10) -> Optional[str]:
    """
    Get content type of URL.
    
    Args:
        url: URL to check
        timeout: Check timeout in seconds
        
    Returns:
        Content type string, None if error
    """
    try:
        with httpx.Client() as client:
            response = client.head(url, timeout=timeout, headers={'User-Agent': 'FireFeed-Core/1.0'})
        return response.headers.get('content-type')
    except Exception as e:
        logger.error(f"Error getting content type: {e}")
        return None


def validate_ssl_certificate(
    hostname: str,
    port: int = 443,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    Validate SSL certificate.
    
    Args:
        hostname: Hostname to validate
        port: Port number
        timeout: Validation timeout in seconds
        
    Returns:
        Certificate information dictionary
    """
    try:
        context = ssl.create_default_context()
        
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                
                return {
                    'valid': True,
                    'subject': dict(x[0] for x in cert['subject']),
                    'issuer': dict(x[0] for x in cert['issuer']),
                    'not_before': cert['notBefore'],
                    'not_after': cert['notAfter'],
                    'serial_number': cert['serialNumber'],
                    'version': cert['version']
                }
                
    except Exception as e:
        logger.error(f"SSL certificate validation failed: {e}")
        return {
            'valid': False,
            'error': str(e)
        }


def get_ip_address(hostname: str) -> Optional[str]:
    """
    Get IP address for hostname.
    
    Args:
        hostname: Hostname to resolve
        
    Returns:
        IP address string, None if error
    """
    try:
        return socket.gethostbyname(hostname)
    except Exception as e:
        logger.error(f"Error resolving hostname: {e}")
        return None


def is_port_open(host: str, port: int, timeout: int = 5) -> bool:
    """
    Check if port is open on host.
    
    Args:
        host: Host to check
        port: Port to check
        timeout: Connection timeout in seconds
        
    Returns:
        True if port is open, False otherwise
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def get_network_interface_info() -> Dict[str, Any]:
    """
    Get network interface information.
    
    Returns:
        Network interface information
    """
    try:
        import psutil
        
        interfaces = {}
        for interface, addrs in psutil.net_if_addrs().items():
            interfaces[interface] = []
            for addr in addrs:
                interfaces[interface].append({
                    'family': addr.family.name,
                    'address': addr.address,
                    'netmask': addr.netmask,
                    'broadcast': addr.broadcast
                })
        
        return interfaces
        
    except Exception as e:
        logger.error(f"Error getting network interface info: {e}")
        return {}


def get_network_stats() -> Dict[str, Any]:
    """
    Get network statistics.
    
    Returns:
        Network statistics
    """
    try:
        import psutil
        
        stats = psutil.net_io_counters()
        return {
            'bytes_sent': stats.bytes_sent,
            'bytes_recv': stats.bytes_recv,
            'packets_sent': stats.packets_sent,
            'packets_recv': stats.packets_recv,
            'errin': stats.errin,
            'errout': stats.errout,
            'dropin': stats.dropin,
            'dropout': stats.dropout
        }
        
    except Exception as e:
        logger.error(f"Error getting network stats: {e}")
        return {}


def parse_url(url: str) -> Dict[str, Any]:
    """
    Parse URL into components.
    
    Args:
        url: URL to parse
        
    Returns:
        URL components dictionary
    """
    try:
        parsed = urlparse(url)
        return {
            'scheme': parsed.scheme,
            'netloc': parsed.netloc,
            'path': parsed.path,
            'params': parsed.params,
            'query': parsed.query,
            'fragment': parsed.fragment,
            'username': parsed.username,
            'password': parsed.password,
            'hostname': parsed.hostname,
            'port': parsed.port
        }
    except Exception as e:
        logger.error(f"Error parsing URL: {e}")
        return {}


def is_private_ip(ip: str) -> bool:
    """
    Check if IP address is private.
    
    Args:
        ip: IP address to check
        
    Returns:
        True if IP is private, False otherwise
    """
    try:
        import ipaddress
        
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private
    except Exception as e:
        logger.error(f"Error checking IP address: {e}")
        return False


def get_public_ip() -> Optional[str]:
    """
    Get public IP address.
    
    Returns:
        Public IP address string, None if error
    """
    try:
        with httpx.Client() as client:
            response = client.get('https://api.ipify.org', timeout=10)
            return response.text.strip()
    except Exception as e:
        logger.error(f"Error getting public IP: {e}")
        return None


def test_network_connectivity(hosts: List[str] = None) -> Dict[str, bool]:
    """
    Test network connectivity to multiple hosts.
    
    Args:
        hosts: List of hosts to test (defaults to common hosts)
        
    Returns:
        Dictionary of host connectivity status
    """
    if hosts is None:
        hosts = ['8.8.8.8', '1.1.1.1', 'google.com', 'cloudflare.com']
    
    results = {}
    
    for host in hosts:
        try:
            if ':' in host:
                # IPv6 or host:port
                host_part = host.split(':')[0]
                port = int(host.split(':')[1]) if ':' in host else 80
            else:
                host_part = host
                port = 80
            
            results[host] = is_port_open(host_part, port, timeout=5)
            
        except Exception as e:
            logger.error(f"Error testing connectivity to {host}: {e}")
            results[host] = False
    
    return results


def get_dns_resolution_time(hostname: str) -> Optional[float]:
    """
    Measure DNS resolution time.
    
    Args:
        hostname: Hostname to resolve
        
    Returns:
        Resolution time in seconds, None if error
    """
    import time
    
    try:
        start_time = time.time()
        socket.gethostbyname(hostname)
        end_time = time.time()
        
        return end_time - start_time
    except Exception as e:
        logger.error(f"Error measuring DNS resolution time: {e}")
        return None